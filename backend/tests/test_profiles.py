import gzip
import json
import shutil
from collections import Counter
import numpy as np
import pytest
from fastapi.testclient import TestClient
from test_forecasting import trained
from app.forecasting.data import digest, facility_hash
from app.forecasting.prediction import ForecastService, ModelUnavailable
from app.models.network import Snapshot
from app.profiles.generation import generate_profile, demand_signature
from app.profiles.config import folder, legacy_snapshot
from app.profiles.identity import fingerprint
from app.profiles.preparation import save, cache_path
from app.scenarios.engine import ScenarioEngine
from app.scenarios.models import ScenarioRequest
from app.optimization.service import OptimizationService
from app.optimization.schemas import RedistributionRequest
from app.services.repository import LocalRepository
from app.main import create_app


@pytest.fixture(scope='module')
def profiles(trained):
    root, original, _ = trained
    for profile in ('constrained','redistribution-ready'):
        generate_profile('BR',profile,root)
    repo=LocalRepository(root)
    return root,repo,original


def test_generation_preserves_source_and_is_deterministic(profiles):
    root,repo,original=profiles
    paths=[legacy_snapshot('BR',root),root/'data/generated/history/BR.json.gz',root/'artifacts/models/BR/bundle.joblib']
    before=[digest(p) for p in paths]
    for profile in ('constrained','redistribution-ready'):
        dest=folder(profile,'BR',root)
        generated=[digest(dest/name) for name in ('network.json','history.json.gz','compatibility.json')]
        generate_profile('BR',profile,root)
        assert generated==[digest(dest/name) for name in ('network.json','history.json.gz','compatibility.json')]
    assert before==[digest(p) for p in paths]
    constrained=repo.profile_snapshot('BR','constrained')
    assert [facility_hash(f) for f in constrained.facilities]==[facility_hash(f) for f in original.facilities]


def test_full_profile_ledger_and_model_inputs(profiles):
    root,repo,_=profiles
    old=Snapshot.model_validate_json(gzip.decompress((root/'data/generated/history/BR.json.gz').read_bytes()))
    new=Snapshot.model_validate_json(gzip.decompress((folder('redistribution-ready','BR',root)/'history.json.gz').read_bytes()))
    assert demand_signature(old)==demand_signature(new)
    assert Counter(new.inventory_roles.values())=={'buffer':2,'balanced':2,'strained':2}
    for a,b in zip(old.facilities,new.facilities):
        for x,y in zip(a.inventory,b.inventory):
            assert x.safety_stock==y.safety_stock
            assert [r.requested for r in x.ledger]==[r.requested for r in y.ledger]
            for prior,row in zip(y.ledger,y.ledger[1:]):
                assert prior.closing==row.opening
                assert row.closing==row.opening+row.received-row.consumed
                assert row.requested==row.consumed+row.unmet_demand
                assert row.transfers_received==row.transfers_sent==0
        for day,h in enumerate(b.history):
            assert h.medicine_units==sum(i.ledger[day].consumed for i in b.inventory)


def test_profile_forecasts_reuse_only_demand_models(profiles):
    root,repo,_=profiles;service=ForecastService(root)
    a=repo.profile_snapshot('BR','constrained');b=repo.profile_snapshot('BR','redistribution-ready')
    first=service.predict(a,a.facilities[0].id,'medicine','PCM')
    second=service.predict(b,b.facilities[0].id,'medicine','PCM')
    assert first.forecast==second.forecast
    assert first.stockout.current_stock!=second.stockout.current_stock
    assert second.provenance.operational_profile=='redistribution-ready'
    assert first.provenance.model_sha256==second.provenance.model_sha256
    assert first.provenance.operational_history_sha256!=second.provenance.operational_history_sha256
    assert fingerprint(a,a.facilities)!=fingerprint(b,b.facilities)
    identical=a.model_copy(deep=True);identical.operational_profile='redistribution-ready'
    assert fingerprint(a,a.facilities)!=fingerprint(identical,identical.facilities)


@pytest.mark.parametrize('profile',['constrained','redistribution-ready'])
def test_batched_saved_model_predictions_are_identical(profiles,profile):
    root,repo,_=profiles;s=repo.profile_snapshot('BR',profile)
    serial=ForecastService(root);batched=ForecastService(root)
    batched.prepare_predictions(s,s.facilities)
    for f in s.facilities:
        for target,resource in [('footfall','footfall'),('admissions','admissions')]+[('medicine',i.medicine_id) for i in f.inventory]:
            a=serial.predict(s,f.id,target,resource);b=batched.predict(s,f.id,target,resource)
            assert a==b


@pytest.fixture(scope='module')
def positive(profiles):
    root,repo,_=profiles;s=repo.profile_snapshot('BR','redistribution-ready')
    engine=ScenarioEngine(ForecastService(root));planner=OptimizationService(engine)
    scenario=engine.run(s,ScenarioRequest(profile='redistribution-ready',country_id='BR',scenario_type='DENGUE_SURGE'))
    req=RedistributionRequest(profile='redistribution-ready',country_id='BR',scenario_id=scenario.scenario.scenario_id)
    result=planner.run(s,req)
    return s,engine,planner,scenario,req,result


def test_positive_generated_problem_and_conservation(positive):
    s,engine,planner,scenario,req,result=positive
    assert result.preview.safe_capacity>0 and result.impact.transferred_units>0
    assert len({d.facility_id for d in result.preview.donors})>=2
    assert any(sum(e.receiver==ri for e in result.preview.edges)>=2 for ri in range(len(result.preview.receivers)))
    assert result.solver.status=='OPTIMAL'
    assert result.impact.after.target_deficit<result.impact.before.target_deficit
    assert result.impact.after.expected_unmet<result.impact.before.expected_unmet
    assert result.impact.donor_safety_violations==result.impact.new_donor_risks==0
    assert all(v['before']==v['after'] for v in result.impact.conservation.values())
    assert all(t.donor_protected_minimum_after>=t.donor_protected_reserve for t in result.transfers)
    assert all(t.quantity>0 and t.provenance['operational_profile']=='redistribution-ready' for t in result.transfers)
    assert any(t.receiver_risk_after['14']<t.receiver_risk_before['14'] or t.receiver_warning_after!=t.receiver_warning_before for t in result.transfers)


def test_positive_runs_are_solver_generated_and_immutable(positive):
    s,engine,planner,scenario,req,result=positive
    before=s.model_dump_json();saved=engine.store.get(req.scenario_id,'BR',req.profile).model_dump_json()
    again=planner.run(s,req)
    assert again.run_id!=result.run_id
    assert [(t.donor_id,t.receiver_id,t.quantity) for t in again.transfers]==[(t.donor_id,t.receiver_id,t.quantity) for t in result.transfers]
    assert s.model_dump_json()==before
    assert engine.store.get(req.scenario_id,'BR',req.profile).model_dump_json()==saved
    again.transfers.clear()
    assert planner.get(again.run_id,'BR',req.profile).transfers
    # Removing one resource changes the generated problem; no stored answer is used.
    smaller=planner.run(s,req.model_copy(update={'resources':['IVF']}))
    assert all(t.resource_id=='IVF' for t in smaller.transfers)


def test_cross_profile_scenarios_plans_and_requests_rejected(profiles,positive):
    root,repo,_=profiles;s,engine,planner,scenario,req,result=positive
    with pytest.raises(LookupError): engine.store.get(req.scenario_id,'BR','constrained')
    with pytest.raises(LookupError): planner.get(result.run_id,'BR','constrained')
    with pytest.raises(ValueError,match='profile'): engine.run(s,ScenarioRequest(country_id='BR',scenario_type='DENGUE_SURGE'))
    with pytest.raises(ValueError,match='profile'): planner.preview(s,RedistributionRequest(country_id='BR'))
    with pytest.raises(LookupError): planner.preview(repo.profile_snapshot('BR','constrained'),req.model_copy(update={'profile':'constrained'}))


@pytest.mark.parametrize('name', ['network.json','history.json.gz','compatibility.json'])
def test_stale_profile_artifacts_invalidate_warm_bindings(profiles,tmp_path,name):
    root,_,_=profiles
    shutil.copytree(root,tmp_path,dirs_exist_ok=True)
    service=ForecastService(tmp_path);service.bundle('BR','redistribution-ready')
    path=folder('redistribution-ready','BR',tmp_path)/name
    if name=='compatibility.json':
        value=json.loads(path.read_text());value['model_sha256']='stale';path.write_text(json.dumps(value))
    else: path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ModelUnavailable): service.bundle('BR','redistribution-ready')


def test_stale_facility_rejected_even_with_matching_profile(profiles):
    root,repo,_=profiles;s=repo.profile_snapshot('BR','redistribution-ready').model_copy(deep=True)
    s.facilities[0].name='changed'
    with pytest.raises(ModelUnavailable): ForecastService(root).predict(s,s.facilities[0].id,'medicine','PCM')


def test_prepared_cache_roundtrip_and_copy_isolation(profiles):
    root,repo,_=profiles;s=repo.profile_snapshot('BR','redistribution-ready')
    original=ScenarioEngine(ForecastService(root));before,_=original.baseline(s,s.facilities)
    report=save(original,s);assert report['disk_bytes']>0
    restored=ScenarioEngine(ForecastService(root));after,_=restored.baseline(s,s.facilities)
    assert before==after and restored.disk_hits==1
    after.facilities[0].resources.clear()
    assert restored.baseline(s,s.facilities)[0]==before
    bundle=restored.forecasts.bundle('BR',s.operational_profile)
    assert restored.key(s,s.facilities[0],bundle)!=restored.key(s.model_copy(update={'operational_profile':'constrained'}),s.facilities[0],bundle)
    assert restored.key(s,s.facilities[0],bundle)!=restored.key(s,s.facilities[0],{**bundle,'artifact_sha256':'new'})


@pytest.mark.parametrize('field,value', [('profile','constrained'),('model_sha256','stale'),('origin','2000-01-01'),('calculation_version','old'),('snapshot','old')])
def test_disk_cache_identity_invalidation(profiles,tmp_path,field,value):
    root,repo,_=profiles;s=repo.profile_snapshot('BR','redistribution-ready')
    shutil.copytree(root,tmp_path,dirs_exist_ok=True)
    engine=ScenarioEngine(ForecastService(tmp_path));save(engine,s)
    path=cache_path(s,tmp_path);envelope=json.loads(gzip.decompress(path.read_bytes()))
    envelope['identity'][field]=value;path.write_bytes(gzip.compress(json.dumps(envelope).encode()))
    fresh=ScenarioEngine(ForecastService(tmp_path));fresh.baseline(s,s.facilities[:1])
    assert fresh.disk_hits==0


def test_api_profile_validation_and_headers(profiles):
    root,repo,_=profiles
    with TestClient(create_app(repo,ForecastService(root))) as client:
        assert client.get('/api/overview?profile=unknown').status_code==422
        response=client.get('/api/overview?country_id=BR&profile=redistribution-ready')
        assert response.status_code==200
        assert response.headers['X-Operational-Profile']=='redistribution-ready'
        assert response.json()['operational_profile']=='redistribution-ready'
        body={'country_id':'BR','profile':'redistribution-ready','scenario_type':'DENGUE_SURGE'}
        assert client.post('/api/scenarios?profile=constrained',json=body).status_code==422
        response=client.post('/api/scenarios',json=body)
        assert response.status_code==201
        assert response.headers['X-Operational-Profile']=='redistribution-ready'
        sid=response.json()['scenario']['scenario_id']
        assert client.get(f'/api/scenarios/{sid}?country_id=BR&profile=constrained').status_code==404
        assert client.get(f'/api/scenarios/{sid}?country_id=BR&profile=redistribution-ready').status_code==200
        assert client.get('/api/scenarios?country_id=BR&profile=constrained').json()==[]


def test_prepared_problem_cache_keys_and_isolation(profiles,positive):
    root,repo,_=profiles;s,engine,planner,scenario,req,result=positive
    first=planner.preview(s,req)
    second=planner.preview(s,req.model_copy(update={'time_limit_seconds':2}))
    assert 'prepared_memory_loading' in second.diagnostics
    assert second.request.time_limit_seconds==2
    assert second.donors==first.donors
    second.donors.clear()
    assert planner.preview(s,req).donors
    different=planner.preview(s,req.model_copy(update={'resources':['IVF']}))
    assert all(d.resource_id=='IVF' for d in different.donors)
    changed=s.model_copy(deep=True);changed.facilities[0].name='changed snapshot'
    with pytest.raises(ValueError): planner.preview(changed,req)
    isolated=planner.preview(repo.profile_snapshot('BR','constrained'),RedistributionRequest(country_id='BR'))
    assert isolated.snapshot_id!=first.snapshot_id


def test_corrupt_prepared_payload_is_cache_miss(profiles,tmp_path):
    root,repo,_=profiles;s=repo.profile_snapshot('BR','redistribution-ready')
    shutil.copytree(root,tmp_path,dirs_exist_ok=True)
    engine=ScenarioEngine(ForecastService(tmp_path));save(engine,s)
    path=cache_path(s,tmp_path);envelope=json.loads(gzip.decompress(path.read_bytes()))
    envelope['payload']='{}';path.write_bytes(gzip.compress(json.dumps(envelope).encode()))
    fresh=ScenarioEngine(ForecastService(tmp_path));fresh.baseline(s,s.facilities[:1])
    assert fresh.disk_hits==0
