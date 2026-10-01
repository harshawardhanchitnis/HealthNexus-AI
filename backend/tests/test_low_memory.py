"""Public infrastructure policy must preserve engines, evidence and forecast numbers."""
import json
import sys
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.core.cache import BoundedCache
from app.core.config import ROOT
from app.forecasting.prediction import ForecastService
from app.main import create_app
from app.services.repository import LocalRepository
from app.federation.service import FederationService


def test_lru_eviction_and_updates():
    cache=BoundedCache(2);cache.update(a=1,b=2)
    assert cache.get('a')==1
    cache['c']=3
    assert list(cache)==['a','c'] and 'b' not in cache
    cache.update(d=4,e=5)
    assert list(cache)==['d','e']


def test_light_readiness_never_predicts_deserializes_or_loads_tables(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    forecasts=ForecastService()
    with patch('joblib.load',side_effect=AssertionError('unpickle')), \
         patch.object(ForecastService,'prepare_predictions',side_effect=AssertionError('predict')), \
         patch('app.federation.data.prepare_country',side_effect=AssertionError('training tables')):
        with TestClient(create_app(forecast_service=forecasts)) as client:
            data=client.get('/readiness').json()
            assert data['status']=='ready' and data['operational_countries']==['IN']
            assert set(data['forecast_artifacts'])=={'constrained:IN','redistribution-ready:IN'}
            assert data['gemini']['provider_probed'] is False
            assert 'acceptance completed' in data['gemini']['acceptance_status']
            assert not forecasts.cache and not forecasts.points
            status=client.get('/api/federation/status').json()
            assert status['saved_evidence_available'] and not status['live_training_available']
            assert len(client.get('/api/federation/nodes').json()['items'])==5
            assert client.get('/api/federation/saved-demo').json()['raw_records_shared']==0
            denied=client.post('/api/federation/runs',json=dict(rounds=5,local_epochs=1,seed=42,policy='sample-weighted'))
            assert denied.status_code==409 and 'disabled' in denied.json()['detail']


@pytest.mark.parametrize('country',['BR','RU','CN','ZA'])
def test_foreign_operations_are_explicitly_rejected(monkeypatch,country):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    with TestClient(create_app()) as client:
        assert [c['id'] for c in client.get('/api/countries').json()['items']]==['IN']
        for endpoint in ('overview','facilities','models/forecasting/metrics','geospatial','warnings','scenarios','data-sources'):
            response=client.get('/api/'+endpoint,params=dict(country_id=country))
            assert response.status_code==422 and 'India-operational-only' in response.json()['detail']
        for endpoint in ('scenarios','optimization/redistribution','ai/copilot'):
            response=client.post('/api/'+endpoint,json={'country_id':country})
            assert response.status_code==422 and 'India-operational-only' in response.json()['detail']
        assert client.post('/api/ai/copilot?country_id='+country,json={'country_id':'IN'}).status_code==422
    with pytest.raises(ValueError,match='India-operational-only'):ForecastService().bundle(country)
    with pytest.raises(ValueError,match='India-operational-only'):LocalRepository().profile_snapshot(country)


def test_network_map_does_not_load_forecasts(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    service=ForecastService()
    with patch.object(service,'bundle',side_effect=AssertionError('network must not load models')):
        with TestClient(create_app(forecast_service=service)) as client:
            response=client.get('/api/geospatial?country_id=IN&profile=redistribution-ready&mode=network')
            assert response.status_code==200 and len(response.json()['facilities']['features'])==207


def test_exact_profile_predictions_and_shared_models(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','false')
    repo=LocalRepository();normal=ForecastService()
    expected={}
    for profile in ('constrained','redistribution-ready'):
        snapshot=repo.profile_snapshot('IN',profile)
        for target,resource in [('footfall','footfall'),('admissions','admissions'),('medicine','IVF'),('medicine','PCM')]:
            expected[profile,target,resource]=normal.predict(snapshot,'IN-MH-PUNE-003',target,resource).model_dump_json()
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    low=ForecastService()
    for profile in ('constrained','redistribution-ready'):
        snapshot=repo.profile_snapshot('IN',profile)
        facility=next(f for f in snapshot.facilities if f.id=='IN-MH-PUNE-003')
        for prepared in (False,True):
            if prepared:low.prepare_predictions(snapshot,[facility])
            for target,resource in [('footfall','footfall'),('admissions','admissions'),('medicine','IVF'),('medicine','PCM')]:
                assert low.predict(snapshot,facility.id,target,resource).model_dump_json()==expected[profile,target,resource]
    a=low.bundle('IN','constrained');b=low.bundle('IN','redistribution-ready')
    assert a['models'] is b['models'] and len(low.cache)==1
    for index in range(700):low.points[('measurement',index)]=index
    assert len(low.points)==128 and ('measurement',0) not in low.points


def test_normal_local_operational_countries_remain(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','false')
    with TestClient(create_app()) as client:
        assert len(client.get('/api/countries').json()['items'])==5
        assert client.get('/api/overview?country_id=BR').status_code==200


def test_batched_warning_outputs_are_exact_and_caches_bounded(monkeypatch):
    expected = None
    for mode in ('false','true'):
        monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY',mode)
        forecasts=ForecastService()
        app=create_app(forecast_service=forecasts)
        with TestClient(app) as client:
            data=client.get('/api/warnings?country_id=IN&profile=redistribution-ready&state_id=MH&district_id=MH-PUNE').json()
            assert 'items' in data
            # Request-time timestamps are intentionally different; every warning
            # identity, numeric value, severity and explanation must be exact.
            for warning in data['items']:warning.pop('generated_at')
            if expected is None:expected=data
            else:assert data==expected
            if mode=='true':
                assert app.state.repository._snapshot is None
                assert len(forecasts.cache)==1 and len(forecasts.points)<=128
                engine=app.state.copilot.engine
                assert len(engine.cache)<=6 and len(engine.baseline_cache)<=6


def test_low_memory_store_is_bounded_without_losing_existing_handles(monkeypatch):
    from app.scenarios.state import ScenarioStore
    from types import SimpleNamespace
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    store=ScenarioStore()
    for i in range(2):store.put(SimpleNamespace(scenario=SimpleNamespace(scenario_id=str(i))))
    with pytest.raises(ValueError,match='Scenario limit'):store.put(SimpleNamespace(scenario=SimpleNamespace(scenario_id='extra')))
    assert list(store.results)==['0','1']


def test_corrupt_india_manifest_is_not_ready(monkeypatch,tmp_path):
    from app.core.integrity import india_artifacts
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    (tmp_path/'artifacts').mkdir()
    (tmp_path/'artifacts/deployment-integrity.json').write_text(json.dumps({'artifacts/models/IN/missing':'wrong'}))
    with pytest.raises((ValueError,OSError)):india_artifacts(tmp_path)


def test_simultaneous_profile_requests_share_one_snapshot_load(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from app.models.network import Snapshot
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    repo=LocalRepository()
    with patch.object(Snapshot,'model_validate_json',wraps=Snapshot.model_validate_json) as load:
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _:repo.profile_snapshot('IN','redistribution-ready'),range(6)))
        assert load.call_count==1
        assert all(result is results[0] for result in results)
        assert repo._snapshot is None


def test_one_active_profile_cache_preserves_both_snapshots_and_results(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    repo=LocalRepository()
    ready=repo.profile_snapshot('IN','redistribution-ready')
    original=ready.model_dump_json()
    constrained=repo.profile_snapshot('IN','constrained')
    assert len(repo._profiles)==1 and ('IN','constrained') in repo._profiles
    assert constrained.operational_profile=='constrained'
    # Eviction removes only a repository reference, not a held immutable snapshot.
    assert ready.model_dump_json()==original
    reloaded=repo.profile_snapshot('IN','redistribution-ready')
    assert len(repo._profiles)==1 and reloaded.model_dump_json()==original
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','false')
    repo.profile_snapshot('IN','constrained')
    assert len(repo._profiles)==2
