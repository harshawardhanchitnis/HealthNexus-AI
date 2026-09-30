"""Verify canonical engines, saved evidence and publication safety. ZERO live Gemini calls."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))


def secret_scan(root=ROOT):
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
    paths = {root/p for p in tracked+untracked if p}
    paths.update((root/'frontend/dist').rglob('*'))
    patterns = [rb'AIza[0-9A-Za-z_-]{35}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    violations = []
    for path in paths:
        if not path.is_file():continue
        if path.name=='.env' or path.name.startswith('service-account') or path.name.startswith('credentials'):
            violations.append(str(path.relative_to(root)));continue
        if any(re.search(pattern,path.read_bytes()) for pattern in patterns):
            violations.append(str(path.relative_to(root)))
    if '.env' in tracked:violations.append('.env tracked')
    ignored = subprocess.run(['git','check-ignore','-q','.env'],cwd=root).returncode==0
    if violations or not ignored:raise ValueError('Secret scan failed; inspect flagged files privately. '+', '.join(violations))
    return {'status':'PASS','files_scanned':sum(p.is_file() for p in paths),'env_ignored':ignored,'env_tracked':False,
        'scope':'tracked/non-ignored files and production frontend bundles; credential patterns, not penetration testing'}


def verify(static=True):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.ai.config import AIConfig
    from app.forecasting.data import digest, facility_hash
    from app.forecasting.prediction import ForecastService
    from app.services.repository import LocalRepository
    from app.data_ingestion.catalog import datasets
    from app.federation.service import FederationService
    from app.federation.artifacts import load_model
    from app.federation.parameters import checksum
    from app.federation.client import FederatedClient
    from app.federation.training import TRAINING_LOCK
    from app.profiles.preparation import cache_path, restore
    from app.scenarios.engine import ScenarioEngine
    import numpy as np
    import torch
    report={'status':'PASS','live_gemini_requests':0,'checks':{},'timings':{},'profiles':{}}
    preserved={str(p.relative_to(ROOT)):digest(p) for folder in ('data/generated','artifacts/models')
               for p in (ROOT/folder).rglob('*') if p.is_file()}
    repo=LocalRepository();forecasts=ForecastService()
    sources=datasets();assert sources
    report['checks']['official_caches']={'datasets':len(sources),'records':sum(len(s.records) for s in sources)}
    for profile in ('constrained','redistribution-ready'):
        for country in ('IN','BR','RU','CN','ZA'):
            snapshot=repo.profile_snapshot(country,profile)
            bundle=forecasts.bundle(country,profile)
            assert snapshot.country==country and snapshot.operational_profile==profile
            assert all(bundle['manifest']['facility_hashes'][f.id]==facility_hash(f) for f in snapshot.facilities)
            if cache_path(snapshot).exists():
                # Optional preparation must reject a changed calculation-source
                # identity. A miss recomputes from unchanged trusted models;
                # this verifier never rebuilds or rewrites the frozen bundle.
                hit=restore(ScenarioEngine(forecasts),snapshot,bundle)
                report['checks'].setdefault('optional_planning_cache',{})[profile+':'+country] = 'hit' if hit else 'safe stale-cache miss; engine recomputes'
    report['checks']['profiles_and_models']='all 10 country/profile partitions validated'
    service=FederationService()
    try:
        saved=service.saved();parameters=load_model(ROOT/'data/demo/federation/global')
        assert checksum(parameters)==saved['final_checksum']
        with TRAINING_LOCK:
            old=torch.get_num_threads();torch.set_num_threads(2)
            try:
                for node in saved['nodes']:
                    client=FederatedClient(node['country_id'],ROOT,saved['config']['seed'])
                    assert client.describe()['table_sha256']==node['table_sha256']
                    client.set_parameters(parameters);metric=client.evaluate('test').model_dump()
                    assert all(np.isclose(v,node['federated_global'][k],rtol=1e-6,atol=1e-8) for k,v in metric.items() if v is not None)
            finally:torch.set_num_threads(old)
        report['checks']['federation']={'run_id':saved['run_id'],'final_checksum':saved['final_checksum'],
            'global_test':saved['global_test'],'raw_records_shared':saved['raw_records_shared'],'training_seconds':saved['training_seconds'],
            'bytes_exchanged':saved['bytes_exchanged'],'rounds':len(saved['rounds'])-1,'reload':'PASS'}
    finally:service.close()
    start=perf_counter();app=create_app(forecast_service=forecasts)
    app.state.copilot.config=AIConfig(api_key='',enabled=True)
    # Any accidental provider use fails immediately without a network request.
    app.state.copilot.transport_factory=lambda *_: (_ for _ in ()).throw(AssertionError('Live Gemini is prohibited'))
    with TestClient(app) as client:
        report['timings']['app_startup_after_imports_seconds']=perf_counter()-start
        def call(path,body=None,expected=200,method=None):
            start=perf_counter();r=client.request(method or ('POST' if body else 'GET'),path,json=body)
            elapsed=perf_counter()-start
            assert r.status_code==expected,(path,r.status_code,r.text[:200])
            return (r.json() if r.content else None),elapsed
        _,report['timings']['readiness_seconds']=call('/readiness')
        for profile,expected in [('redistribution-ready',(41763,17745,15679,10,26084)),('constrained',(30230,0,0,0,30230))]:
            scope=f'country_id=IN&state_id=MH&district_id=MH-PUNE&profile={profile}'
            overview,t=call('/api/overview?'+scope);report['timings'][profile+'_command_centre_api_seconds']=t
            fid=next(f.id for f in repo.profile_snapshot('IN',profile).facilities if f.district_id=='MH-PUNE')
            _,t=call(f'/api/forecasts/facilities/{fid}/medicines/IVF?country_id=IN&profile={profile}')
            report['timings'][profile+'_forecast_seconds']=t
            scenario,t=call('/api/scenarios',{'profile':profile,'country_id':'IN','state_id':'MH','district_id':'MH-PUNE',
                'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,'seed':42},201)
            report['timings'][profile+'_scenario_seconds']=t
            sid=scenario['scenario']['scenario_id']
            _,t=call('/api/warnings?'+scope+'&scenario_id='+sid);report['timings'][profile+'_warnings_seconds']=t
            plan,t=call('/api/optimization/redistribution',{'profile':profile,'country_id':'IN','state_id':'MH','district_id':'MH-PUNE',
                'scope':'district','scenario_id':sid},201)
            report['timings'][profile+'_optimization_seconds']=t
            actual=(plan['preview']['total_deficit'],plan['preview']['safe_capacity'],plan['impact']['transferred_units'],len(plan['transfers']),plan['impact']['after']['target_deficit'])
            assert actual==expected,(profile,actual)
            assert plan['impact']['new_donor_risks']==plan['impact']['donor_safety_violations']==0
            assert all(v['before']==v['after'] for v in plan['impact']['conservation'].values())
            report['profiles'][profile]={'target_before':actual[0],'safe_donor_capacity':actual[1],'transferred':actual[2],
                'lanes':actual[3],'unresolved':actual[4],'solver_status':plan['solver']['status'],'impact':plan['impact'],
                'solver_seconds':sum(s['seconds'] for s in plan['solver']['stages'])}
            _,t=call('/api/ai/copilot',{'profile':profile,'country_id':'IN','state_id':'MH','district_id':'MH-PUNE',
                'mode':'offline','message':'Summarize current resource risks in Pune.'})
            report['timings'][profile+'_offline_copilot_seconds']=t
            call('/api/scenarios/'+sid+'?country_id=BR&profile='+profile,expected=404)
            call('/api/scenarios/'+sid+'?'+scope,expected=204,method='DELETE')
            call('/api/scenarios/'+sid+'?'+scope,expected=404)
        for path in ('/api/overview?country_id=XX','/api/overview?profile=invalid'):
            call(path,expected=422)
        call('/api/scenarios',{'scenario_type':'INVALID'},422)
        call('/api/federation/runs',{'rounds':11},422)
        empty,_=call('/api/facilities?search=NO_SUCH_FACILITY');assert empty['total']==0
        failure,_=call('/api/ai/copilot',{'message':'Summarize Pune','mode':'gemini'},503)
        assert failure['detail']['code']=='missing_key'
        report['checks']['failure_modes']='invalid country/profile/body, empty filters, reset, missing key with no provider use'
    assert preserved=={p:digest(ROOT/p) for p in preserved}
    report['checks']['operational_assets_immutable']=len(preserved)
    report['checks']['security']=secret_scan()
    if static:
        folder=ROOT/'frontend/dist/healthnexus-frontend/browser'
        index=(folder/'index.html').read_text()
        assert '<base href="/">' in index or '<base href="/"' in index
        assert (folder/'runtime-config.js').exists()
        for src in re.findall(r'(?:src|href)="([^"?#]+\.(?:js|css))"',index):
            assert (folder/src).exists(),src
        report['checks']['static_frontend']='SPA base, runtime configuration and entry chunks PASS'
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'docs/evaluation/phase8-demo.json')
    parser.add_argument('--skip-frontend',action='store_true');args=parser.parse_args()
    try:report=verify(not args.skip_frontend)
    except Exception as error:
        print(f'FAIL: {type(error).__name__}: {error}');raise SystemExit(1)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print('PASS · canonical demo verified · ZERO live Gemini requests')
    print(json.dumps({'profiles':{k:{x:v[x] for x in ('target_before','safe_donor_capacity','transferred','lanes','unresolved')} for k,v in report['profiles'].items()},'timings':report['timings']},indent=2))

if __name__=='__main__':main()
