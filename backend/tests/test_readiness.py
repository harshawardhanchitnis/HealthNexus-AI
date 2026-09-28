import json
import shutil
from fastapi.testclient import TestClient
import pytest
from app.core.config import ROOT
from app.federation.service import FederationService
from app.main import create_app
from app.core.readiness import capabilities


def test_health_never_invokes_provider():
    app=create_app()
    app.state.copilot.transport_factory=lambda *_: (_ for _ in ()).throw(AssertionError('provider'))
    with TestClient(app) as client:
        assert client.get('/health').json()=={'status':'ok','service':'HealthNexus AI'}


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
