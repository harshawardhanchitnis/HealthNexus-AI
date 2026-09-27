from datetime import date
from types import SimpleNamespace
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.optimization.candidates import protection, candidates, make_edges
from app.optimization.distance import haversine
from app.optimization.solver import solve, greedy, objective
from app.optimization.schemas import Candidate, Edge, RedistributionRequest, Preview
from app.optimization.service import OptimizationService
from app.optimization.impact import apply_plan
from app.scenarios.engine import ScenarioEngine
from app.scenarios.models import ScenarioRequest
from app.forecasting.prediction import ForecastService
from app.forecasting.stockout import project_stock
from app.forecasting.schemas import StockRisk
from app.main import create_app
from test_forecasting import trained


def candidate(id, surplus=0, deficit=0, country='IN', state='MH', district='MH-PUNE', resource='IVF', critical=True, weight=100):
    return Candidate(facility_id=id, facility_name=id, country_id=country, state_id=state, district_id=district,
        resource_id=resource, unit='bags', current_stock=1000, protected_reserve=101, safe_surplus=surplus,
        protected_minimum_stock=900, reserve_after_max_donation=900-surplus, deficit=deficit,
        expected_unmet=deficit, depletion_date=None, safety_breach_date=None, risk={'3': 0, '7': 0, '14': 0},
        severity='WARNING', priority=200, critical=critical, shortage_weight=weight)


def edge(d=0, r=0, cost=1, distance=1):
    return Edge(donor=d, receiver=r, distance_km=distance, geographic_penalty=0, unit_cost=cost)


def test_surplus_accounts_for_demand_receipts_and_origin():
    point = np.ones(14)*10
    reserve, minimum, surplus, deficit = protection(300, 50, point, np.tile(point, (500, 1)), np.zeros(14))
    assert (reserve, minimum, surplus, deficit) == (51, 160, 109, 0)
    reserve, minimum, surplus, deficit = protection(30, 50, point, np.tile(point, (500, 1)), np.array([0]*13+[500]))
    assert surplus == 0 and minimum == -100 and deficit == 151  # late receipts cannot fund dispatch now


def test_worst_sample_and_current_cover_are_protected():
    point = np.ones(14)*10
    paths = np.tile(point, (500, 1)); paths[0] *= 2
    _, minimum, surplus, _ = protection(400, 50, point, paths, np.zeros(14))
    assert minimum == 120 and surplus == 69
    assert minimum-surplus >= 51
    assert protection(65, 1, point, np.tile(point, (500, 1)), point)[2] == 0


@pytest.mark.parametrize('scope,count', [('district',1),('state',2),('national',3)])
def test_scope_distance_and_resource_matching(scope, count):
    donors = [candidate('a',10),candidate('b',10,district='MH-NAG'),candidate('c',10,state='KA',district='KA-BLR'),candidate('d',10,resource='PCM')]
    receivers = [candidate('r',deficit=10)]
    physical = {c.facility_id: SimpleNamespace(latitude=18.,longitude=73.+i) for i,c in enumerate(donors+receivers)}
    edges = make_edges(donors, receivers, physical, 'IN', scope)
    assert len(edges) == count
    assert [e.geographic_penalty for e in edges] == [0,1000,10000][:count]
    assert all(e.distance_km > 0 for e in edges)


@pytest.mark.parametrize('country', ['IN','BR','RU','CN','ZA'])
def test_country_isolation(country):
    other = 'BR' if country == 'IN' else 'IN'
    d, r = candidate('d',10,country=country),candidate('r',deficit=10,country=other)
    with pytest.raises(ValueError, match='International'):
        make_edges([d],[r],{},country,'national')
    with pytest.raises(ValueError, match='Invalid transfer edge'):
        solve([d],[r],[edge()])


def test_haversine():
    assert haversine(0,0,0,0) == 0
    assert haversine(0,0,0,1) == pytest.approx(111.195, abs=.001)
    assert haversine(18,73,19,74) == haversine(19,74,18,73)
    with pytest.raises(ValueError): haversine(91,0,0,0)


def test_multiple_donors_receivers_and_determinism():
    ds, rs = [candidate('d1',8),candidate('d2',9)], [candidate('r1',deficit=10),candidate('r2',deficit=7)]
    es = [edge(0,0,1),edge(0,1,8),edge(1,0,8),edge(1,1,1)]
    q, m = solve(ds, rs, es)
    assert m.status == 'OPTIMAL' and q == [8,0,2,7] and sum(q) == 17
    assert all(type(x) is int and x >= 0 for x in q)
    assert solve(ds,rs,es)[0] == q
    assert objective(ds,rs,es,q)[:2] == [0,0]
    assert len(m.stages) == 3 and all(s.status == 'OPTIMAL' for s in m.stages)


def test_critical_priority_cannot_be_outweighed_by_distance():
    ds = [candidate('d',10)]
    rs = [candidate('critical',deficit=10),candidate('routine',deficit=10,critical=False,weight=9999)]
    q,m = solve(ds,rs,[edge(0,0,10_000_000),edge(0,1,0)])
    assert q == [10,0] and m.status == 'OPTIMAL'


def test_partial_and_infeasible_diagnostic():
    ds, rs, es = [candidate('d',3)], [candidate('r',deficit=10)], [edge()]
    q,m=solve(ds,rs,es)
    assert q == [3] and m.objective[0] == 7 and m.status == 'OPTIMAL'
    q,m=solve(ds,rs,es,require_full=True)
    assert q == [0] and m.status == 'INFEASIBLE' and m.objective is None


def test_no_supply_remains_feasible_and_timeout_not_optimal():
    _,m=solve([], [candidate('r',deficit=10)], [])
    assert m.status == 'OPTIMAL' and m.objective[0] == 10
    _,m=solve([candidate('d',10)],[candidate('r',deficit=10)],[edge()],seconds=0)
    assert m.status == 'UNKNOWN' and m.objective is None


def test_budget_expiry_after_first_proved_stage_is_feasible(monkeypatch):
    # Real CP-SAT solves stage one; a controlled clock exhausts the budget before
    # later objectives. The retained incumbent must never be called optimal.
    import app.optimization.solver as module
    times=iter([0.,0.,2.,2.])
    monkeypatch.setattr(module,'perf_counter',lambda:next(times))
    q,m=solve([candidate('d',10)],[candidate('r',deficit=10)],[edge()],seconds=1)
    assert q == [10] and m.status == 'FEASIBLE'
    assert m.termination == 'time_limit_with_incumbent' and len(m.stages) == 1


def test_greedy_comparator_and_resource_rejection():
    ds=[candidate('d1',10),candidate('d2',10)]
    rs=[candidate('r',deficit=12)]
    es=[edge(0,0,20,20),edge(1,0,5,5)]
    assert greedy(ds,rs,es) == [2,10]
    assert solve(ds,rs,es)[0] == [2,10]
    with pytest.raises(ValueError): solve([candidate('d',10,resource='PCM')],rs,[edge()])


@pytest.mark.parametrize('body', [{'resources':['BEDS']},{'resources':['IVF','IVF']},{'scope':'international'},{'scope':'state'},{'scope':'district'},{'horizon':7},{'country_id':'US'},{'resources':[]},{'time_limit_seconds':31},{'allow_donor_violation':True}])
def test_invalid_requests(body):
    with pytest.raises(ValidationError): RedistributionRequest(**body)


@pytest.fixture(scope='module')
def context(trained):
    root,snapshot,_=trained
    e=ScenarioEngine(ForecastService(root))
    return snapshot,e,OptimizationService(e)


def test_scenario_identity_immutability_store_and_recompute(context):
    s,e,o=context
    initial=s.model_dump_json()
    scenario=e.run(s,ScenarioRequest(country_id='BR',scenario_type='DENGUE_SURGE',seed=9))
    saved=scenario.model_dump_json()
    q=RedistributionRequest(country_id='BR',scenario_id=scenario.scenario.scenario_id)
    _, projections, paired, _=o.prepare(s,q)
    for f in projections:
        for r in f.resources:
            check=project_stock(r.stockout.current_stock,r.stockout.safety_stock,
                np.array([p.point for p in r.forecast]),paired[(f.facility_id,r.resource_id)],
                np.array([p.expected_receipts for p in r.stockout.trajectory]),s.as_of)
            assert check['probabilities'] == r.stockout.probabilities
    p=o.run(s,q)
    assert p.preview.scenario_snapshot_id == scenario.scenario.baseline_snapshot_id
    assert s.model_dump_json() == initial and e.store.get(q.scenario_id,'BR').model_dump_json() == saved
    assert p.impact.new_donor_risks == 0 and p.impact.donor_safety_violations == 0
    assert all(v['before'] == v['after'] for v in p.impact.conservation.values())
    with pytest.raises(LookupError): o.get(p.run_id,'IN')
    copy=o.get(p.run_id,'BR');copy.message='changed'
    assert o.get(p.run_id,'BR').message != 'changed'
    stale=s.model_copy(deep=True);stale.facilities[0].inventory[0].current_stock+=1
    with pytest.raises(ValueError,match='identity'): o.preview(stale,q)
    o.discard(p.run_id,'BR')
    with pytest.raises(LookupError): o.get(p.run_id,'BR')
    assert e.store.get(q.scenario_id,'BR').model_dump_json() == saved


def test_actual_transfer_impact_conservation_and_new_donor_risk(context, monkeypatch):
    s,e,_=context
    base,_=e.baseline(s,s.facilities[:2])
    fs=sorted(base.facilities,key=lambda f:f.facility_id)
    paths={}
    for i,f in enumerate(fs):
        r=f.resources[0].model_copy(deep=True);r.resource_id='PCM';r.unit='tablets'
        r.forecast=[p.model_copy(update={k:10. for k in ('point','lower80','upper80','lower95','upper95')}) for p in r.forecast]
        point=np.ones(14)*10; sample=np.tile(point,(500,1));paths[(f.facility_id,'PCM')]=sample
        r.stockout=StockRisk.model_validate(project_stock(1000 if i==0 else 10,50,point,sample,np.zeros(14),s.as_of))
        r.requested_total=140;r.unmet_total=sum(p.unmet_demand for p in r.stockout.trajectory)
        f.resources=[r];f.receipt_changes=[]
    original=[f.model_dump_json() for f in fs]
    ds,rs=candidates(fs,paths,[],s.as_of,{fs[1].facility_id},['PCM'])
    es=[edge()];q,m=solve(ds,rs,es)
    preview=Preview(request=RedistributionRequest(country_id='BR',resources=['PCM']),snapshot_id='fixture',scenario_snapshot_id=None,
        origin=s.as_of,config_version='test',model_version='fixture',receivers=rs,donors=ds,edges=es,
        total_deficit=rs[0].deficit,safe_capacity=ds[0].safe_surplus,capacity_by_resource={'PCM':ds[0].safe_surplus},deficit_by_resource={'PCM':rs[0].deficit},limitations=[])
    impact,transfers,after,_,_=apply_plan(fs,paths,preview,q,s.as_of,'test-run',m.status)
    assert q == [181] and transfers[0].quantity == 181
    assert impact.before.expected_unmet == 130 and impact.after.expected_unmet == 0
    assert impact.after.max_stockout_risk == 0 and impact.new_donor_risks == 0
    assert impact.before.max_stockout_risk == 1
    assert impact.before.critical_resource_warnings == 3 and impact.after.critical_resource_warnings == 0
    assert impact.conservation['PCM'] == {'before':1010,'after':1010}
    assert after[0].resources[0].stockout.current_stock == 819
    assert after[1].resources[0].stockout.current_stock == 191
    assert all(p.closing_stock >= 51 for p in after[0].resources[0].stockout.trajectory)
    assert [f.model_dump_json() for f in fs] == original
    service=OptimizationService(e)
    monkeypatch.setattr(service,'prepare',lambda *_:(preview,fs,paths,None))
    persisted=service.run(s,preview.request)
    assert persisted.transfers[0].quantity == persisted.greedy_transfers[0].quantity == 181
    assert service.get(persisted.run_id,'BR').impact.after.expected_unmet == 0
    with pytest.raises(ValueError): apply_plan(fs,paths,preview,[182],s.as_of,'x','FEASIBLE')
    with pytest.raises(ValueError): apply_plan(fs,paths,preview,[1.5],s.as_of,'x','FEASIBLE')


def test_typed_api(context):
    s,e,_=context
    class Repo:
        mode='test'
        def snapshot(self): return s
        def country_snapshot(self,c): return s
    with TestClient(create_app(Repo(),e.forecasts)) as client:
        assert client.get('/api/optimization/config').json()['version'] == 'redistribution-v1'
        body={'country_id':'BR','resources':['IVF']}
        assert client.post('/api/optimization/preview',json=body).status_code == 200
        response=client.post('/api/optimization/redistribution',json=body)
        assert response.status_code == 201, response.text
        rid=response.json()['run_id']
        assert client.get(f'/api/optimization/runs/{rid}?country_id=IN').status_code == 404
        assert client.get(f'/api/optimization/runs/{rid}?country_id=BR').status_code == 200
        assert client.delete(f'/api/optimization/runs/{rid}?country_id=BR').status_code == 204
        assert client.get(f'/api/optimization/runs/{rid}?country_id=BR').status_code == 404
        assert client.post('/api/optimization/redistribution',json={'scope':'state'}).status_code == 422
