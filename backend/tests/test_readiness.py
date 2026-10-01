import json
import shutil
from contextlib import ExitStack
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import pytest
from app.core.config import ROOT
from app.core.admission import OperationalAdmission
from app.forecasting.prediction import ForecastService
from app.federation.service import FederationService
from app.main import create_app
from app.core.readiness import capabilities
from app.services.repository import LocalRepository


@pytest.mark.parametrize('low_memory', ['false', 'true'])
def test_health_never_invokes_provider(monkeypatch, low_memory):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', low_memory)
    app=create_app()
    provider=Mock(side_effect=AssertionError('provider'))
    app.state.copilot.transport_factory=provider
    with TestClient(app) as client:
        get=client.get('/health')
        assert get.status_code==200
        assert get.content==b'{"status":"ok","service":"HealthNexus AI"}'
        assert get.json()=={'status':'ok','service':'HealthNexus AI'}
        assert get.headers['content-type']=='application/json'
        head=client.head('/health')
        assert head.status_code==200 and head.content==b''
        assert head.headers['content-length']=='0'
        # Only the lightweight liveness endpoint gains HEAD support.
        assert client.head('/api/health').status_code==405
        assert client.head('/readiness').status_code==405
    provider.assert_not_called()


def test_liveness_keeps_low_memory_state_cold_even_when_operational_work_is_busy(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', 'true')
    repository=LocalRepository()
    forecasts=ForecastService()
    app=create_app(repository=repository, forecast_service=forecasts)
    copilot=app.state.copilot
    engine,planner=copilot.engine,copilot.planner
    forbidden=[patch.object(target,name,side_effect=AssertionError('Liveness must not initialize operational work'))
        for target,name in [(repository,'snapshot'),(repository,'country_snapshot'),(repository,'profile_snapshot'),
            (forecasts,'bundle'),(forecasts,'prepare_predictions'),(engine,'run'),(planner,'prepare'),
            (copilot,'transport_factory')]]
    forbidden += [patch(name,side_effect=AssertionError('Liveness must not load artifacts or solve'))
        for name in ['joblib.load','app.services.repository.artifact_bytes',
            'app.optimization.service.solve','app.core.readiness.capabilities']]
    with ExitStack() as stack:
        guards=[stack.enter_context(guard) for guard in forbidden]
        with TestClient(app) as client:
            assert client.head('/health').status_code==200
            admission=app.middleware_stack
            while not isinstance(admission,OperationalAdmission):admission=admission.app
            admission.busy=True
            try:
                for method in ('GET','HEAD'):
                    assert client.request(method,'/health').status_code==200
                    assert admission.busy is True
            finally:admission.busy=False
        for guard in guards:guard.assert_not_called()
    assert repository._snapshot is None and not repository._profiles and not repository._countries
    assert not forecasts.cache and not forecasts.points
    assert not engine.cache and not engine.baseline_cache and not engine.store.results
    assert not planner.prepared and not planner.results


@pytest.fixture
def saved_root(tmp_path):
    shutil.copytree(ROOT/'data/demo/federation',tmp_path/'data/demo/federation')
    return tmp_path


def test_saved_demo_survives_service_restart_and_is_read_only(saved_root):
    for _ in range(2):
        service=FederationService(saved_root)
        try:
            row=service.saved();assert row['saved_demo'] and row['raw_records_shared']==0
            assert row['run_id']=='fdbaaedb-773d-4b67-be50-ad406b130950'
            assert service.store.runs=={} and service.active is None
        finally:service.close()


def test_missing_saved_evidence_is_clean_503(tmp_path):
    with TestClient(create_app(federation_service=FederationService(tmp_path))) as client:
        r=client.get('/api/federation/saved-demo');assert r.status_code==503
        assert 'unavailable' in r.json()['detail']


@pytest.mark.parametrize('filename',['global/model.json','global/parameters.npz','report.json'])
def test_corrupt_saved_evidence_is_rejected(saved_root,filename):
    path=saved_root/'data/demo/federation'/filename
    if filename=='report.json':
        report=json.loads(path.read_text());report['final_checksum']='wrong';path.write_text(json.dumps(report))
    else:path.write_bytes(b'corrupt')
    service=FederationService(saved_root)
    try:
        with pytest.raises((ValueError,OSError)):service.saved()
    finally:service.close()


def test_readiness_without_key_has_no_provider_calls():
    app=create_app()
    from app.ai.config import AIConfig
    app.state.copilot.config=AIConfig(api_key='',enabled=False)
    app.state.copilot.transport_factory=lambda *_: (_ for _ in ()).throw(AssertionError('provider'))
    with TestClient(app) as client:
        r=client.get('/readiness');assert r.status_code==200
        body=r.json();assert body['gemini']['provider_probed'] is False
        assert body['gemini']['configured'] is False
        assert body['federation_saved_run'] and all(body['forecast_artifacts'].values())
        assert 'api_key' not in json.dumps(body)


def test_readiness_missing_models_degraded(tmp_path):
    app=create_app();service=FederationService(tmp_path)
    try:
        result=capabilities(tmp_path,app.state.copilot,service)
        assert result['status']=='degraded' and not result['scenario_engine']
        assert not result['federation_saved_run']
    finally:service.close();app.state.federation.close()
