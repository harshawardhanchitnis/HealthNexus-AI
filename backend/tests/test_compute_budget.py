"""Deployment bounds apply below HTTP without changing operational mathematics."""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.core.admission import OperationalAdmission
from app.core.runtime import ComputeScopeError, compute_scope
from app.main import create_app
from app.forecasting.prediction import ForecastService
from app.scenarios.models import ScenarioRequest
from app.optimization.schemas import RedistributionRequest
from app.services.repository import LocalRepository
from app.ai.schemas import CopilotRequest


@pytest.mark.parametrize('method,path,body', [
    ('GET', '/api/warnings', None),
    ('GET', '/api/warnings/summary', None),
    ('GET', '/api/geospatial?mode=forecast', None),
    ('POST', '/api/scenarios', {'scenario_type':'DENGUE_SURGE','severity':'severe'}),
    ('POST', '/api/optimization/preview', {'scope':'national'}),
    ('POST', '/api/optimization/redistribution', {'scope':'national'}),
    ('POST', '/api/optimization/preview', {'scope':'state','state_id':'MH'}),
])
def test_national_computation_rejected_before_model_loading(monkeypatch,method,path,body):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    with patch.object(ForecastService,'bundle',side_effect=AssertionError('No model loading for denied scope')):
        with TestClient(create_app()) as client:
            response=client.request(method,path,json=body)
            assert response.status_code==422, response.text
            assert 'district' in response.json()['detail']


def test_bounds_apply_to_direct_services_and_copilot_tools(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    app=create_app();service=app.state.copilot
    repo=LocalRepository();snapshot=repo.profile_snapshot('IN','redistribution-ready')
    with patch.object(service.engine.forecasts,'bundle',side_effect=AssertionError('No model loading')):
        with pytest.raises(ComputeScopeError):service.engine.baseline(snapshot,snapshot.facilities)
        with pytest.raises(ComputeScopeError):service.engine.run(snapshot,ScenarioRequest(profile='redistribution-ready',scenario_type='DENGUE_SURGE'))
        with pytest.raises(ComputeScopeError):service.planner.preview(snapshot,RedistributionRequest(profile='redistribution-ready'))
        with TestClient(app) as client:
            response=client.post('/api/ai/copilot',json=CopilotRequest(profile='redistribution-ready',mode='offline',message='Summarize resource resilience').model_dump(mode='json'))
            assert response.status_code==422 and response.json()['detail']['code']=='district_required'
            assert not service.audit and not service.conversations
    assert service.audit_limit==service.request_limit==8 and service.conversation_limit==4


def test_computation_budget_validates_districts_states_and_facility_count(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    facility=lambda state,district:SimpleNamespace(state_id=state,district_id=district)
    a,b=facility('MH','MH-PUNE'),facility('MH','MH-NAGPUR')
    compute_scope([a]*3)
    compute_scope([a]*3+[b]*3,cross_district=True)
    for group,cross in [([a,b],False),([a]*13,False),([a,facility('KA','KA-X')],True),([a,b,facility('MH','MH-X')],True)]:
        with pytest.raises(ComputeScopeError):compute_scope(group,cross_district=cross)
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','false')
    compute_scope([a]*207)


def test_admission_holds_until_final_body_and_allows_status(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    async def check():
        started=asyncio.Event();finish=asyncio.Event();calls=[];messages=[]
        async def app(scope,receive,send):
            calls.append(scope['path'])
            await send({'type':'http.response.start','status':200,'headers':[]})
            if scope['path']=='/api/warnings':
                started.set();await finish.wait()
            await send({'type':'http.response.body','body':b'ok'})
        gate=OperationalAdmission(app)
        async def receive():return {'type':'http.request','body':b''}
        async def send(message):messages.append(message)
        scope=lambda path:{'type':'http','method':'GET','path':path,'headers':[]}
        first=asyncio.create_task(gate(scope('/api/warnings'),receive,send));await started.wait()
        await gate(scope('/api/optimization/preview'),receive,send)
        assert any(m.get('status')==429 for m in messages)
        assert '/api/optimization/preview' not in calls
        await gate(scope('/api/ai/requests/id'),receive,send)
        await gate(scope('/api/countries'),receive,send)
        await gate(scope('/api/regions'),receive,send)
        assert '/api/regions' in calls
        finish.set();await first
        assert not gate.busy
        await gate(scope('/api/geospatial'),receive,send)
        assert '/api/geospatial' in calls
    asyncio.run(check())


def test_admission_releases_on_failure(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    async def broken(scope,receive,send):raise RuntimeError('test')
    async def check():
        gate=OperationalAdmission(broken)
        with pytest.raises(RuntimeError):await gate({'type':'http','method':'GET','path':'/api/scenarios'},None,None)
        assert not gate.busy
    asyncio.run(check())


def test_large_requests_do_not_reach_application(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    with TestClient(create_app()) as client:
        response=client.post('/api/ai/copilot',content=b'x'*32769,headers={'Content-Type':'application/json'})
        assert response.status_code==413
        assert client.get('/api/overview').status_code==200


def test_copilot_history_is_bounded_with_explicit_expired_handles(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY','true')
    app=create_app();service=app.state.copilot
    service.transport_factory=lambda *args:pytest.fail('Offline must never call a provider')
    context={'country_id':'IN','profile':'redistribution-ready','state_id':'MH','district_id':'MH-PUNE',
             'mode':'offline','message':'Is this live government inventory?'}
    with TestClient(app) as client:
        first=None
        for _ in range(10):
            response=client.post('/api/ai/copilot',json=context)
            assert response.status_code==200,response.text
            data=response.json()
            assert data['metadata']['provider_requests']==0 and data['evidence']
            first=first or data['conversation_id']
            assert len(service.conversations)<=4 and len(service.requests)<=8 and len(service.audit)<=8
        assert len(service.conversations)==4 and len(service.requests)==len(service.audit)==8
        expired=client.post('/api/ai/copilot',json=context|{'conversation_id':first})
        assert expired.status_code==404 and expired.json()['detail']['code']=='conversation_missing'
