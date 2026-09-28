import json
from types import SimpleNamespace
import httpx
import pytest
from fastapi.testclient import TestClient
from test_profiles import profiles, trained
from app.ai.config import AIConfig, MODEL
from app.ai.client import CopilotError, GeminiTransport, provider_error
from app.ai.schemas import CopilotRequest, DraftAnswer
from app.ai.tool_registry import TOOLS, declarations, validated
from app.ai.tools import ToolExecutor
from app.ai.orchestrator import CopilotService
from app.ai.citations import build_evidence
from app.ai.fallback import clinical_request
from app.forecasting.prediction import ForecastService
from app.scenarios.engine import ScenarioEngine
from app.optimization.service import OptimizationService
from app.main import create_app


def service(profiles, factory=None, **config):
    root,repo,_=profiles
    engine=ScenarioEngine(ForecastService(root));planner=OptimizationService(engine)
    return CopilotService(engine,planner,AIConfig(api_key='unit-test-placeholder',**config),
        **({'transport_factory':factory} if factory else {})),repo


def request(**kwargs):
    return CopilotRequest(country_id='BR',profile='redistribution-ready',message='Summarize current network risks',**kwargs)


class Scripted:
    def __init__(self, turns): self.turns=iter(turns);self.bodies=[];self.closed=False
    def create(self,**body): self.bodies.append(body);return next(self.turns)
    def close(self): self.closed=True


def call(name,args,id='c1'):
    return {'type':'function_call','name':name,'arguments':args,'id':id}


def turn(calls,id='interaction1'):
    return {'id':id,'steps':calls,'usage':{'total_input_tokens':11,'total_output_tokens':7,'total_tokens':18}}


def final(text='The selected network has resource risks.',field='summary.facilities',eid='e1'):
    return {'id':'interaction-final','output_text':json.dumps({'situation':{'text':text,
        'references':[{'evidence_id':eid,'field':field}]},'key_risks':[],
        'recommended_actions':[],'remaining_gaps':[]})}


def ready():
    return {'id':'evidence-ready','status':'completed','output_text':'Evidence ready.'}


@pytest.mark.parametrize('name',list(TOOLS))
def test_native_tool_declarations_strict(name):
    declaration=next(d for d in declarations() if d['name']==name)
    schema=declaration['parameters']
    assert declaration['type']=='function' and len(declaration['description'])>50
    assert schema['type']=='object' and schema['additionalProperties'] is False
    assert {'country_id','profile'} <= set(schema['required'])
    assert schema['properties']['profile']['enum']==['constrained','redistribution-ready']
    assert '$ref' not in json.dumps(schema)


@pytest.mark.parametrize('args',[{'country_id':'IN','profile':'redistribution-ready'},
    {'country_id':'BR','profile':'constrained'},
    {'country_id':'BR','profile':'redistribution-ready','arbitrary':'code'}])
def test_context_and_extra_argument_rejection(args):
    with pytest.raises(ValueError): validated('get_network_summary',args,request())


def test_no_arbitrary_code_or_unauthorized_planning():
    with pytest.raises(ValueError): validated('exec',{},request())
    with pytest.raises(ValueError): validated('optimize_redistribution',{'country_id':'BR','profile':'redistribution-ready'},request())
    with pytest.raises(ValueError): validated('get_network_summary',{'country_id':'BR','profile':'redistribution-ready','state_id':'OTHER'},request(state_id='BR-SP'))
    assert validated('get_network_summary',{'country_id':'BR','profile':'constrained'},request(compare_profiles=True)).profile=='constrained'


def test_sequential_interactions_and_fresh_evidence(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    fake=Scripted([turn([call('get_network_summary',args)]),turn([call('get_warning_summary',args)],'interaction2'),
        ready(),final('Structured warnings identify operational pressure.','summary.total','e2')])
    svc,repo=service(profiles,lambda config:fake)
    result=svc.run(repo,request())
    assert [t.tool for t in result.tools_used]==['get_network_summary','get_warning_summary']
    assert result.mode=='gemini' and result.evidence[0].value>0
    assert fake.bodies[1]['previous_interaction_id']=='interaction1'
    assert fake.bodies[1]['input'][0]['call_id']=='c1'
    assert fake.bodies[2]['previous_interaction_id']=='interaction2'
    assert all(b['model']==MODEL and b['generation_config']['thinking_level']=='medium' for b in fake.bodies)
    assert all(b['tools'] and 'response_format' not in b for b in fake.bodies[:-1])
    assert 'tools' not in fake.bodies[-1] and fake.bodies[-1]['response_format']['schema']
    assert fake.bodies[-1]['previous_interaction_id']=='evidence-ready'
    assert result.metadata['interaction_count']==4
    assert result.metadata['usage'][0]['total_tokens']==18
    assert fake.closed and result.metadata['tool_seconds']>0
    assert result.metadata['interaction_id']=='interaction-final'
    assert svc.progress(result.request_id,'BR','redistribution-ready')['status']=='completed'
    with pytest.raises(LookupError):svc.progress(result.request_id,'IN','redistribution-ready')
    with pytest.raises(LookupError):svc.discard(result.conversation_id,'BR','constrained')
    svc.discard(result.conversation_id,'BR','redistribution-ready')
    assert result.conversation_id not in svc.conversations and not svc.audit


def test_bad_tool_call_can_be_corrected_without_execution(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    fake=Scripted([turn([call('execute_transfer',args)]),turn([call('get_network_summary',args)],'i2'),ready(),final()])
    svc,repo=service(profiles,lambda config:fake)
    result=svc.run(repo,request())
    assert result.tools_used[0].status=='error' and result.tools_used[1].status=='success'
    assert 'error' in json.loads(fake.bodies[1]['input'][0]['result'][0]['text'])


def test_tool_limit_bounds_loop(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    fake=Scripted([turn([call('get_scenario_presets',args)])]*4)
    svc,repo=service(profiles,lambda config:fake,max_calls=2)
    with pytest.raises(CopilotError,match='limit'):svc.run(repo,request())
    assert len(fake.bodies)==3 and fake.closed


@pytest.mark.parametrize('response,code',[
    ({'id':'bad','steps':[{'type':'function_call','name':'get_network_summary','arguments':'text'}]},'malformed_tool_call'),
    ({'id':'bad','output_text':'not json'},'response_schema'),
    (final(field='invented.field'),'evidence_invalid'),
    (final(text='There are 999999 donors.'),'unsupported_number'),
    (final(text='An optimal plan exists.'),'solver_terminology'),
    (final(text='The medicines were dispatched.'),'unsafe_claim'),
])
def test_invalid_model_outputs_are_rejected(profiles,response,code):
    args={'country_id':'BR','profile':'redistribution-ready'}
    responses=[turn([call('get_network_summary',args)]),response] if code=='malformed_tool_call' else [turn([call('get_network_summary',args)]),ready(),response]
    fake=Scripted(responses)
    svc,repo=service(profiles,lambda config:fake)
    with pytest.raises(CopilotError) as error: svc.run(repo,request())
    assert error.value.code==code


@pytest.mark.parametrize('status,code',[(401,'authentication'),(403,'authentication'),(404,'model_unavailable'),
    (429,'rate_limited'),(400,'provider_configuration'),(500,'provider_unavailable')])
def test_provider_errors_are_sanitized(status,code):
    error=provider_error(SimpleNamespace(code=status))
    assert error.code==code and 'unit-test-placeholder' not in error.message


def test_timeout_mapping():
    assert provider_error(httpx.ReadTimeout('secret')).code=='provider_timeout'


def test_exact_model_missing_key_and_offline(profiles):
    svc,repo=service(profiles,model='other-model')
    with pytest.raises(CopilotError) as error:svc.run(repo,request())
    assert error.value.code=='model_configuration'
    svc.config=AIConfig(api_key='')
    assert svc.status()['configuration_status']=='missing_key'
    with pytest.raises(CopilotError) as error:svc.run(repo,request())
    assert error.value.code=='missing_key'
    result=svc.run(repo,request(mode='offline'))
    assert result.mode=='offline' and result.metadata['model'] is None
    assert result.metadata['gemini_network_seconds']==0
    assert 'unit-test-placeholder' not in result.model_dump_json()


@pytest.mark.parametrize('message',[
    'What medicine should I personally take for dengue?', 'Diagnose my symptoms',
    'Prescribe medication for my fever', 'Interpret these patient records',
])
def test_clinical_scope_is_rejected_before_transport(profiles,message):
    assert clinical_request(message)
    svc,repo=service(profiles,lambda config:pytest.fail('No patient text may reach Gemini'))
    result=svc.run(repo,request().model_copy(update={'message':message}))
    assert result.status=='refused' and result.tools_used==[] and not svc.audit


def test_offline_positive_solver_result_and_immutability(profiles):
    svc,repo=service(profiles)
    before=repo.profile_snapshot('BR','redistribution-ready').model_dump_json()
    result=svc.run(repo,request(mode='offline',allow_planning=True).model_copy(update={'message':'Simulate severe dengue for 14 days and optimize redistribution'}))
    plan=next(r['result'] for r in result.operational_results if r['tool']=='optimize_redistribution')
    assert plan['solver']['status']=='OPTIMAL' and plan['impact']['transferred_units']>0
    assert plan['impact']['after']['target_deficit']<plan['impact']['before']['target_deficit']
    assert plan['impact']['new_donor_risks']==plan['impact']['donor_safety_violations']==0
    assert all(t['donor_protected_minimum_after']>=t['donor_protected_reserve'] for t in plan['transfers'])
    assert svc.engine.store.get(result.scenario_id,'BR','redistribution-ready')
    assert svc.planner.get(result.optimization_run_id,'BR','redistribution-ready').impact.transferred_units==plan['impact']['transferred_units']
    assert repo.profile_snapshot('BR','redistribution-ready').model_dump_json()==before
    followup=svc.run(repo,request(mode='offline',conversation_id=result.conversation_id).model_copy(update={'message':'Why these donors?'}))
    assert followup.tools_used[0].tool=='get_optimization_result'
    with pytest.raises(CopilotError):svc.run(repo,request(mode='offline',conversation_id=result.conversation_id).model_copy(update={'profile':'constrained'}))


def test_tool_geography_horizon_and_provenance(profiles):
    svc,repo=service(profiles);ctx=request();executor=ToolExecutor(repo,svc.engine,svc.planner,ctx)
    with pytest.raises(LookupError):executor.execute('get_network_summary',{'country_id':'BR','profile':'redistribution-ready','district_id':'MH-PUNE'})
    snapshot=repo.profile_snapshot('BR','redistribution-ready');fid=snapshot.facilities[0].id
    f=executor.execute('get_forecast',{'country_id':'BR','profile':'redistribution-ready','facility_id':fid,'target':'medicine','resource_id':'IVF','horizon':7})
    assert f['horizon']==7 and f['unit']=='bags' and len(f['forecast'])==7
    assert len(json.dumps(f))<28000 and 'history' not in f
    p=executor.execute('get_data_provenance',{'country_id':'BR','profile':'redistribution-ready'})
    assert p['live_government_inventory'] is False and p['context']['profile']=='redistribution-ready'
    assert p['sources'] and p['seed']==42


def test_api_status_profile_validation_and_clinical_refusal(profiles):
    root,repo,_=profiles
    with TestClient(create_app(repo,ForecastService(root))) as client:
        response=client.get('/api/ai/status');assert response.status_code==200
        assert 'api_key' not in response.text
        body=request(mode='offline').model_dump(mode='json')
        response=client.post('/api/ai/copilot?profile=constrained',json=body);assert response.status_code==422
        response=client.post('/api/ai/copilot',json=body);assert response.status_code==200
        assert response.headers['X-Operational-Profile']=='redistribution-ready'
        cid=response.json()['conversation_id']
        assert client.delete(f'/api/ai/conversations/{cid}?country_id=BR&profile=constrained').status_code!=204
        assert client.delete(f'/api/ai/conversations/{cid}?country_id=BR&profile=redistribution-ready').status_code==204
        body['message']='Diagnose my fever';response=client.post('/api/ai/copilot',json=body)
        assert response.json()['status']=='refused'
        body['message']='x'*2001;assert client.post('/api/ai/copilot',json=body).status_code==422


def test_official_sdk_wire_payload_without_api_cost(monkeypatch):
    from google import genai
    from google.genai import types
    requests=[]
    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200,json={'id':'wire-test','status':'completed','model':MODEL,'output_text':'{}','steps':[]})
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'))
    transport.client.close()
    transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handle)},retry_options=types.HttpRetryOptions(attempts=1)))
    result=transport.create(model=MODEL,input='Test tools only',store=True,tools=declarations(),system_instruction='Test',
        generation_config={'thinking_level':'medium','max_output_tokens':2400})
    transport.create(model=MODEL,input='Test schema only',previous_interaction_id=result['id'],store=True,
        response_format={'type':'text','mime_type':'application/json','schema':DraftAnswer.model_json_schema()})
    transport.close()
    assert result['id']=='wire-test' and requests[0]['model']==MODEL and len(requests[0]['tools'])==13
    assert 'response_format' not in requests[0] and 'tools' not in requests[1]
    assert requests[1]['previous_interaction_id']=='wire-test' and requests[1]['response_format']['schema']


@pytest.mark.parametrize('status,retries',[(503,2),(502,2),(429,1),(401,1),(400,1)])
def test_conservative_transport_retry(monkeypatch,status,retries):
    monkeypatch.setattr('app.ai.client.sleep',lambda seconds:None)
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'))
    count=[]
    class ProviderError(Exception): code=status
    def failing(**body):count.append(body);raise ProviderError('provider secret text')
    monkeypatch.setattr(transport.client.interactions,'create',failing)
    with pytest.raises(CopilotError) as error:transport.create(model=MODEL,input='Question')
    transport.close()
    assert len(count)==retries and 'secret' not in str(error.value)


def test_workflow_timeout_and_busy_context_are_bounded(profiles):
    svc,repo=service(profiles,workflow_timeout=-1)
    with pytest.raises(CopilotError) as error:svc.run(repo,request(mode='offline'))
    assert error.value.code=='workflow_timeout'
    svc,repo=service(profiles)
    result=svc.run(repo,request(mode='offline'))
    row=svc.conversations[result.conversation_id];row['busy']=True
    with pytest.raises(CopilotError) as error:svc.run(repo,request(mode='offline',conversation_id=result.conversation_id))
    assert error.value.code=='conversation_busy' and row['busy'] is True
    row['busy']=False


def test_conversation_state_reuses_interaction_but_refreshes_tools(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    fake=Scripted([turn([call('get_network_summary',args)]),ready(),final(),
        turn([call('get_network_summary',args)],'fresh-interaction'),ready(),final()])
    svc,repo=service(profiles,lambda config:fake)
    first=svc.run(repo,request());second=svc.run(repo,request(conversation_id=first.conversation_id))
    assert fake.bodies[3]['previous_interaction_id']=='interaction-final'
    assert len(second.tools_used)==1 and len(second.evidence)==1
    assert second.metadata['transport']=='mock'


def test_credentials_are_not_forwarded_or_logged(profiles):
    svc,repo=service(profiles,lambda config:pytest.fail('No key may reach provider input'))
    with pytest.raises(CopilotError) as error:svc.run(repo,request().model_copy(update={'message':'My key is unit-test-placeholder'}))
    assert error.value.code=='credential_input' and not svc.audit


def test_stale_scenario_rejected_by_tool_wrapper(profiles):
    svc,repo=service(profiles);ctx=request(mode='offline',allow_planning=True)
    executor=ToolExecutor(repo,svc.engine,svc.planner,ctx);args={'country_id':'BR','profile':'redistribution-ready'}
    s=executor.execute('run_emergency_scenario',{**args,'scenario_type':'DENGUE_SURGE'})
    with svc.engine.store.lock:
        stored=svc.engine.store.results[s['scenario_id']]
        stored.scenario.baseline_snapshot_id='stale'
    with pytest.raises(ValueError):executor.execute('get_scenario_comparison',{**args,'scenario_id':s['scenario_id']})


@pytest.mark.parametrize('stage',['gathering','synthesis'])
def test_incomplete_provider_response_is_not_a_valid_answer(profiles,stage):
    args={'country_id':'BR','profile':'redistribution-ready'}
    incomplete={'id':'budget-stop','status':'incomplete','output_text':'Partial answer'}
    turns=[turn([call('get_network_summary',args)])]
    if stage=='synthesis':turns.append(ready())
    turns.append(incomplete)
    svc,repo=service(profiles,lambda config:Scripted(turns))
    with pytest.raises(CopilotError) as error:svc.run(repo,request())
    assert error.value.code=='response_incomplete'


def test_wrapped_timeout_and_safe_provider_diagnostics(monkeypatch):
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'))
    class WrappedTimeout(Exception):pass
    def failing(**body):
        try:raise httpx.ReadTimeout('unit-test-placeholder')
        except httpx.ReadTimeout as cause:raise WrappedTimeout('No private details') from cause
    monkeypatch.setattr(transport.client.interactions,'create',failing)
    with pytest.raises(CopilotError) as error:transport.create(model=MODEL,input='Test')
    transport.close()
    assert error.value.code=='provider_timeout'
    assert error.value.diagnostic['exception_type']=='WrappedTimeout'
    assert 'unit-test-placeholder' not in str(error.value.diagnostic)
