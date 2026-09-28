"""Reproducible local profile demos, country isolation, timings and model checks."""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.services.repository import LocalRepository
from app.scenarios.engine import ScenarioEngine
from app.scenarios.models import ScenarioRequest
from app.optimization.service import OptimizationService
from app.optimization.schemas import RedistributionRequest
from app.profiles.preparation import save
from app.forecasting.data import digest, facility_hash
from app.profiles.config import legacy_snapshot


def measure(service,snapshot,request):
    start=perf_counter();result=service.run(snapshot,request);wall=perf_counter()-start
    start=perf_counter();encoded=result.model_dump_json();serialization=perf_counter()-start
    return result,{'wall_seconds':wall,'response_serialization_seconds':serialization,'response_bytes':len(encoded.encode()),
        'stages':result.diagnostics,'solver_only_seconds':sum(s.seconds for s in result.solver.stages)}


def main():
    report={'profiles':{},'isolation':[],'performance':{}}
    repo=LocalRepository()
    original={c:digest(legacy_snapshot(c)) for c in ['IN','BR','RU','CN','ZA']}
    for profile in ['constrained','redistribution-ready']:
        snapshot=repo.profile_snapshot('IN',profile)
        engine=ScenarioEngine();planner=OptimizationService(engine)
        scenario=engine.run(snapshot,ScenarioRequest(profile=profile,state_id='MH',district_id='MH-PUNE',scenario_type='DENGUE_SURGE'))
        req=RedistributionRequest(profile=profile,state_id='MH',district_id='MH-PUNE',scope='district',scenario_id=scenario.scenario.scenario_id)
        immutable=snapshot.model_dump_json();saved=scenario.model_dump_json()
        preview=planner.preview(snapshot,req)
        result,timing=measure(planner,snapshot,req)
        assert snapshot.model_dump_json()==immutable and engine.store.get(req.scenario_id,'IN',profile).model_dump_json()==saved
        assert result.impact.new_donor_risks==result.impact.donor_safety_violations==0
        assert all(v['before']==v['after'] for v in result.impact.conservation.values())
        if profile=='constrained':
            assert (preview.total_deficit,preview.safe_capacity,result.impact.transferred_units,result.impact.after.target_deficit)==(30230,0,0,30230)
        else:
            assert preview.safe_capacity>0 and result.impact.transferred_units>0 and len(result.transfers)>0
            assert len({d.facility_id for d in preview.donors})>=2
            assert result.impact.after.expected_unmet<result.impact.before.expected_unmet
            assert any(t.receiver_risk_after['14']<t.receiver_risk_before['14'] or t.receiver_warning_after!=t.receiver_warning_before for t in result.transfers)
        Path(f'docs/evaluation/phase55-{profile}-pune.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
        report['profiles'][profile]={'timing':timing,'deficits':preview.deficit_by_resource,'capacity':preview.capacity_by_resource,
            'solver':result.solver.model_dump(mode='json'),'impact':result.impact.model_dump(),'greedy':result.greedy.model_dump(),
            'transfers':[t.model_dump(mode='json') for t in result.transfers],
            'warnings_before':result.before_warnings.summary.model_dump(),'warnings_after':result.after_warnings.summary.model_dump(),
            'roles':snapshot.inventory_roles,'baseline_snapshot_id':result.preview.snapshot_id}
        for scope in ['state','national']:
            q=req.model_copy(update={'scope':scope});planner.preview(snapshot,q)
            _,elapsed=measure(planner,snapshot,q)
            report['profiles'][profile][scope+'_warm']=elapsed
        print(profile,result.solver.status,preview.total_deficit,preview.safe_capacity,result.impact.transferred_units,flush=True)
        for country in ['IN','BR','RU','CN','ZA']:
            s=repo.profile_snapshot(country,profile)
            forecasts=engine.forecasts.predict(s,s.facilities[0].id,'medicine','IVF')
            assert forecasts.country_id==country and forecasts.provenance.operational_profile==profile
            q=RedistributionRequest(profile=profile,country_id=country,
                state_id=s.facilities[0].state_id,district_id=s.facilities[0].district_id,
                scope='district' if s.facilities[0].district_id else 'state')
            plan=planner.run(s,q)
            assert all(f.country_id==country for f in plan.before+plan.after)
            assert plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
            for wrong_country,wrong_profile in [(country,'redistribution-ready' if profile=='constrained' else 'constrained'),('BR' if country=='IN' else 'IN',profile)]:
                try:planner.get(plan.run_id,wrong_country,wrong_profile)
                except LookupError:pass
                else:raise AssertionError('Country/profile isolation failed')
            report['isolation'].append({'country':country,'profile':profile,'model':forecasts.provenance.model_version,'status':'passed'})
        del engine,planner
    s=repo.profile_snapshot('IN','constrained')
    engine=ScenarioEngine(use_prepared=False);planner=OptimizationService(engine)
    _,timing=measure(planner,s,RedistributionRequest())
    report['performance']['cold_national']=timing
    _,timing=measure(planner,s,RedistributionRequest())
    report['performance']['warm_national']=timing
    start=perf_counter();report['performance']['preparation']=save(engine,s)
    report['performance']['preparation']['seconds']=perf_counter()-start
    fresh=ScenarioEngine();planner=OptimizationService(fresh)
    _,timing=measure(planner,s,RedistributionRequest())
    report['performance']['prepared_cold_national']={**timing,'disk_hits':fresh.disk_hits}
    assert fresh.disk_hits==1
    assert original=={c:digest(legacy_snapshot(c)) for c in original}
    report['preserved_original_snapshot_hashes']=original
    report['checks']=['both real solver demos','immutable legacy snapshots and scenario','all five countries in both profiles',
        'same demand-model weights','positive donor reserve protection and conservation','cross-country and cross-profile rejection']
    Path('docs/evaluation/phase55-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report['performance'],indent=2),flush=True)

if __name__=='__main__':main()
