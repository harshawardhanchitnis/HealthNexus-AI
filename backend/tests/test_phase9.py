"""Real saved profiles/engines; no live provider or map service requests."""
from datetime import timedelta
from types import SimpleNamespace
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import create_app
from app.geospatial import read_map
from app.map_coordinates import map_coordinates, DISTRICT_CENTRES
from app.optimization.distance import haversine
from app.optimization.schemas import RedistributionRequest
from app.optimization.candidates import make_edges
from app.scenarios.models import ScenarioRequest
from app.services.repository import LocalRepository
from test_optimization import candidate


@pytest.fixture(scope='module')
def actual():
    repo = LocalRepository()
    app = create_app(repository=repo)
    app.state.copilot.transport_factory = lambda *_: (_ for _ in ()).throw(AssertionError('Live Gemini prohibited'))
    engine, planner = app.state.copilot.engine, app.state.copilot.planner
    cases = {}
    for profile in ('redistribution-ready', 'constrained'):
        snapshot = repo.profile_snapshot('IN', profile)
        scenario = engine.run(snapshot, ScenarioRequest(country_id='IN', profile=profile, state_id='MH',
            district_id='MH-PUNE', scenario_type='DENGUE_SURGE', severity='severe', duration=14, seed=42))
        req = RedistributionRequest(country_id='IN', profile=profile, state_id='MH', district_id='MH-PUNE',
                                    scenario_id=scenario.scenario.scenario_id, scope='cross_district')
        cross = planner.run(snapshot, req)
        district = planner.run(snapshot, req.model_copy(update={'scope': 'district'}))
        cases[profile] = snapshot, scenario, cross, district
    with TestClient(app) as client:
        yield repo, engine, planner, cases, client


def map_case(actual, profile='redistribution-ready', **changes):
    _, engine, planner, cases, _ = actual
    snapshot, scenario, cross, _ = cases[profile]
    context = dict(mode='redistribution', state_id='MH', district_id='MH-PUNE',
                   scenario_id=scenario.scenario.scenario_id, run_id=cross.run_id, donor_scope='cross_district')
    context.update(changes)
    return read_map(snapshot, engine, planner, **context)


@pytest.mark.parametrize('scope,count', [('district',1), ('cross_district',1), ('state',2), ('national',3)])
def test_exact_donor_geography_not_labels(scope, count):
    donors = [candidate('local',10), candidate('otherdistrict',10,district='MH-NAGPUR'),
              candidate('otherstate',10,state='KA',district='KA-BLR')]
    receiver = candidate('receiver',deficit=20)
    physical = {c.facility_id: SimpleNamespace(latitude=18.,longitude=73.+i) for i,c in enumerate(donors+[receiver])}
    edges = make_edges(donors,[receiver],physical,'IN',scope)
    assert len(edges) == count
    if scope == 'cross_district': assert edges[0].donor == 1


def test_unit_mismatch_is_not_a_lane():
    d, r = candidate('d',10,district='MH-NAGPUR'), candidate('r',deficit=10)
    d.unit = 'tablets'
    assert make_edges([d],[r],{},'IN','cross_district') == []


@pytest.mark.parametrize('changes', [{'country_id':'BR'}, {'state_id':None}, {'district_id':None}, {'scope':'international'}])
def test_cross_scope_request_requires_indian_state_and_receiver(changes):
    body = dict(country_id='IN', state_id='MH', district_id='MH-PUNE', scope='cross_district')
    with pytest.raises(ValidationError): RedistributionRequest(**(body|changes))


@pytest.mark.parametrize('profile,expected', [('redistribution-ready',(41763,17745,15679,10,26084)),('constrained',(30230,0,0,0,30230))])
def test_canonical_and_cross_safety(actual, profile, expected):
    from verify_cross_district import validate
    snapshot, scenario, cross, district = actual[3][profile]
    baseline = snapshot.model_dump_json(); definition = scenario.model_dump_json()
    assert (district.preview.total_deficit,district.preview.safe_capacity,district.impact.transferred_units,
            len(district.transfers),district.impact.after.target_deficit) == expected
    assert validate(cross,snapshot,actual[2]) == 'PASS'
    if profile == 'redistribution-ready':
        assert len(cross.transfers)>0 and cross.preview.safe_capacity>0 and cross.impact.transferred_units>0
        assert cross.impact.after.target_deficit < cross.impact.before.target_deficit
        assert cross.impact.after.expected_unmet < cross.impact.before.expected_unmet
    else: assert cross.transfers==[] and cross.preview.safe_capacity==0
    assert baseline==snapshot.model_dump_json() and definition==scenario.model_dump_json()


def test_geometry_is_actual_optimizer_edges_with_separate_map_coordinates(actual):
    view = map_case(actual); snapshot, _, plan, _ = actual[3]['redistribution-ready']
    lookup = {f.id:f for f in snapshot.facilities}
    assert len(view['transfers']['features'])==len(plan.transfers)==10
    assert view['summary']['plan']['geography']['donor_districts']==[{'id':'MH-NAGPUR','name':'Nagpur'}]
    for feature, transfer in zip(view['transfers']['features'],plan.transfers):
        p = feature['properties']; d, r = lookup[transfer.donor_id], lookup[transfer.receiver_id]
        assert feature['geometry']['coordinates']==[map_coordinates(d),map_coordinates(r)]
        assert p['distance_km']==transfer.distance_km
        dc, rc = feature['geometry']['coordinates']
        assert p['map_distance_km']==haversine(dc[1],dc[0],rc[1],rc[0])
        assert 600 < p['map_distance_km'] < 700
        assert p['quantity']==transfer.quantity and p['unit']==transfer.unit and p['cross_district']
        assert p['action_state']['physical_execution'] is False
    donor_ids = {t.donor_id for t in plan.transfers}
    assert donor_ids <= {f['id'] for f in view['facilities']['features']}
    assert all(f['geometry']['coordinates']==map_coordinates(lookup[f['id']]) for f in view['facilities']['features'])


def test_constrained_has_pressure_no_fabricated_lanes(actual):
    view = map_case(actual,'constrained')
    assert view['transfers']['features']==[] and view['summary']['plan']['unresolved']==30230
    assert any(f['properties']['status']=='CRITICAL' for f in view['facilities']['features'])


@pytest.mark.parametrize('mode',['network','forecast','emergency'])
def test_other_modes_never_draw_plan_lines(actual, mode):
    view = map_case(actual,mode=mode)
    assert view['metadata']['mode']==mode and view['transfers']['features']==[]
    assert view['metadata']['live_government_inventory'] is False
    assert view['metadata']['profile']=='redistribution-ready'
    if mode != 'network': assert any(f['properties']['forecast_signals'] for f in view['facilities']['features'])


def test_scenario_warning_signals_match_existing_engine(actual):
    view = map_case(actual,mode='emergency'); scenario=actual[3]['redistribution-ready'][1]
    assert {w['warning_id'] for f in view['facilities']['features'] for w in f['properties']['warnings']} == {w.warning_id for w in scenario.warnings_created.items}
    for f in view['facilities']['features']:
        p = next(p for p in scenario.scenario_result.facilities if p.facility_id==f['id'])
        assert f['properties']['source_status']==p.status
        assert f['properties']['forecast_signals'][0]['stockout_risk_14']==p.resources[0].stockout.probabilities['14']


@pytest.mark.parametrize('changes', [{'district_id':'MH-NAGPUR'}, {'state_id':'KA'}, {'scenario_id':None}, {'donor_scope':'district'}])
def test_plan_context_mismatch_rejected(actual, changes):
    with pytest.raises((ValueError,LookupError)): map_case(actual,**changes)


@pytest.mark.parametrize('mode', ['emergency','redistribution'])
def test_explicit_handles_required(actual, mode):
    with pytest.raises(ValueError): map_case(actual,mode=mode,scenario_id=None,run_id=None)


def test_stale_origin_and_model_do_not_reuse_overlay(actual, monkeypatch):
    snapshot, _, cross, _ = actual[3]['redistribution-ready']
    stale = snapshot.model_copy(update={'as_of':snapshot.as_of+timedelta(days=1)})
    with pytest.raises(ValueError,match='stale'): read_map(stale,actual[1],actual[2],mode='redistribution',state_id='MH',district_id='MH-PUNE',run_id=cross.run_id,scenario_id=cross.preview.request.scenario_id)
    old = actual[1].forecasts.bundle
    monkeypatch.setattr(actual[1].forecasts,'bundle',lambda *a:old(*a)|{'artifact_sha256':'different-model'})
    with pytest.raises(ValueError,match='model identity'): map_case(actual)


@pytest.mark.parametrize('country',['IN','BR','RU','CN','ZA'])
def test_map_country_profile_isolation(actual, country):
    client=actual[4]
    for profile in ('constrained','redistribution-ready'):
        response=client.get('/api/geospatial',params={'country_id':country,'profile':profile})
        assert response.status_code==200
        view=response.json()
        assert view['metadata']['country_id']==country and view['metadata']['profile']==profile
        assert all(f['properties']['country_id']==country for f in view['facilities']['features'])
        assert len({f['id'] for f in view['facilities']['features']})==len(view['facilities']['features'])
        assert all(-180<=f['geometry']['coordinates'][0]<=180 and -90<=f['geometry']['coordinates'][1]<=90 for f in view['facilities']['features'])


@pytest.mark.parametrize('params,code', [({'profile':'invalid'},422),({'country_id':'US'},422),({'mode':'live'},422),
    ({'donor_scope':'international'},422),({'resource':'unlisted'},422),({'state_id':'unlisted'},404),
    ({'scenario_id':'gone','mode':'emergency'},404),({'run_id':'gone','mode':'redistribution'},404)])
def test_api_context_validation(actual, params, code):
    assert actual[4].get('/api/geospatial',params=params).status_code==code


def test_cross_profile_and_country_handles_rejected(actual):
    cross=actual[3]['redistribution-ready'][2]
    for changes in ({'profile':'constrained'},{'country_id':'BR'}):
        query=dict(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',mode='redistribution',run_id=cross.run_id,scenario_id=cross.preview.request.scenario_id)
        assert actual[4].get('/api/geospatial',params=query|changes).status_code==404


def test_filters_are_display_only_and_do_not_change_plan(actual):
    plan=actual[3]['redistribution-ready'][2]; old=plan.model_dump_json()
    view=map_case(actual,resource='IVF')
    assert all(f['properties']['resource_id']=='IVF' for f in view['transfers']['features'])
    assert view['summary']['plan']['planned_accounting_items']==plan.impact.transferred_units
    assert view['summary']['visible_lanes']==len(view['transfers']['features'])
    assert plan.model_dump_json()==old


def test_accepted_phase6_and_ledger_remain_frozen():
    from verify_phase9_preservation import preserved
    assert preserved()['status']=='PASS'


def test_district_catalogue_is_complete_stable_and_display_only(actual):
    repo = actual[0]
    ready = repo.profile_snapshot('IN','redistribution-ready')
    constrained = repo.profile_snapshot('IN','constrained')
    assert set(DISTRICT_CENTRES) == {d.id for d in ready.districts}
    original = ready.model_dump_json()
    for a, b in zip(ready.facilities, constrained.facilities):
        assert a.id == b.id and map_coordinates(a) == map_coordinates(b)
        lon, lat = map_coordinates(a)
        anchor = DISTRICT_CENTRES[a.district_id]
        assert 0.49 < haversine(lat,lon,*anchor) < 3.01
    assert ready.model_dump_json() == original
    assert (actual[3]['redistribution-ready'][2].preview.safe_capacity,
            actual[3]['redistribution-ready'][2].impact.transferred_units,
            actual[3]['redistribution-ready'][2].impact.after.target_deficit) == (9307,9307,32456)
