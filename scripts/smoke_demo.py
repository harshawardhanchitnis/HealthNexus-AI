"""Actual HTTP acceptance for local/Docker demo; no provider inference calls."""
import argparse
import json
from pathlib import Path
from time import perf_counter, sleep, monotonic
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def run(base):
    result={'status':'PASS','base':'local Docker HTTP service','live_gemini_requests':0,'timings':{},'profiles':{}}
    def call(path,body=None,expected=200,method=None):
        start=perf_counter()
        req=Request(base+path,data=json.dumps(body).encode() if body else None,
            method=method or ('POST' if body else 'GET'),headers={'Content-Type':'application/json'})
        try:r=urlopen(req,timeout=180)
        except HTTPError as e:r=e
        with r:
            assert r.status==expected,(path,r.status)
            content=r.read();data=json.loads(content) if content else None
        return data,perf_counter()-start
    health,_=call('/health');assert health['status']=='ok'
    readiness,t=call('/readiness');result['readiness']=readiness;result['timings']['readiness_seconds']=t
    for profile,expected in [('redistribution-ready',(41763,17745,15679,10,26084)),('constrained',(30230,0,0,0,30230))]:
        scope=f'country_id=IN&state_id=MH&district_id=MH-PUNE&profile={profile}'
        _,t=call('/api/overview?'+scope);result['timings'][profile+'_overview_seconds']=t
        facilities,_=call('/api/facilities?'+scope)
        _,t=call('/api/forecasts/facilities/'+facilities['items'][0]['id']+'/medicines/IVF?'+scope)
        result['timings'][profile+'_forecast_seconds']=t
        scenario,t=call('/api/scenarios',{'country_id':'IN','profile':profile,'state_id':'MH','district_id':'MH-PUNE',
            'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,'seed':42},201)
        result['timings'][profile+'_scenario_seconds']=t;sid=scenario['scenario']['scenario_id']
        warnings,t=call('/api/warnings?'+scope+'&scenario_id='+sid);result['timings'][profile+'_warnings_seconds']=t
        plan,t=call('/api/optimization/redistribution',{'country_id':'IN','profile':profile,'state_id':'MH',
            'district_id':'MH-PUNE','scope':'district','scenario_id':sid},201)
        result['timings'][profile+'_optimization_seconds']=t
        actual=(plan['preview']['total_deficit'],plan['preview']['safe_capacity'],plan['impact']['transferred_units'],len(plan['transfers']),plan['impact']['after']['target_deficit'])
        assert actual==expected,(profile,actual)
        assert plan['impact']['new_donor_risks']==plan['impact']['donor_safety_violations']==0
        assert all(v['before']==v['after'] for v in plan['impact']['conservation'].values())
        offline,t=call('/api/ai/copilot',{'country_id':'IN','profile':profile,'state_id':'MH','district_id':'MH-PUNE',
            'mode':'offline','message':'Summarize resource risks in Pune.'})
        assert offline['mode']=='offline' and offline['metadata']['provider_requests']==0
        result['timings'][profile+'_offline_seconds']=t
        result['profiles'][profile]={'scenario_id':sid,'run_id':plan['run_id'],'scope':scope,'metrics':actual,
            'impact':plan['impact'],'warnings':warnings['summary'],'solver':plan['solver']['status']}
    saved,_=call('/api/federation/saved-demo');result['saved_federation_checksum']=saved['final_checksum']
    start=perf_counter();run,_=call('/api/federation/runs',{'rounds':5,'local_epochs':1,'seed':42,'policy':'sample-weighted'},202)
    deadline=monotonic()+120
    while monotonic()<deadline:
        row,_=call('/api/federation/runs/'+run['run_id'])
        if row['status'] in ('completed','failed'):break
        sleep(.2)
    assert row['status']=='completed' and row['raw_records_shared']==0
    # Numeric checkpoint identity is deterministic across OS/platforms to float32 precision;
    # metrics may differ by the published CPU reduction tolerance.
    import math
    assert math.isclose(row['global_test']['wape'],saved['global_test']['wape'],rel_tol=1e-6)
    result['timings']['federation_http_workflow_seconds']=perf_counter()-start
    result['federation']={'training_seconds':row['training_seconds'],'raw_records_shared':row['raw_records_shared'],
        'global_test':row['global_test'],'bytes_exchanged':row['bytes_exchanged'],'final_checksum':row['final_checksum'],
        'saved_checksum_equal':row['final_checksum']==saved['final_checksum']}
    call('/api/overview?profile=invalid',expected=422);call('/api/overview?country_id=XX',expected=422)
    call('/api/scenarios',{'scenario_type':'bad'},422)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',default='http://127.0.0.1:18000')
    parser.add_argument('--output',type=Path,default=Path('docs/evaluation/phase8-docker.json'));args=parser.parse_args()
    report=run(args.base);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
