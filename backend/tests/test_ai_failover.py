"""Scripted availability failures, real local engines, and SDK wire checks; no live calls."""
import json
from dataclasses import replace
import httpx
import pytest
from google import genai
from google.genai import types
from test_ai import service, request, Scripted, turn, call, ready, final
from test_profiles import profiles, trained
from test_ai_budget import scoped
from verify_gemini import DemoTransport
from app.ai.config import AIConfig, DEFAULT_CHAIN
from app.ai.client import CopilotError, GeminiTransport
from app.ai.failover import FailoverSession
from app.ai.budget import RequestBudget


def unavailable(code='provider_unavailable', status=503, **extra):
    e=CopilotError(code,'Sanitized test failure')
    e.diagnostic={'http_status':status,'provider_message':'HIGH DEMAND',**extra}
    return e


class Failing:
    def __init__(self, error, budget=None, model=None):
        self.error, self.budget, self.model=error,budget,model
        self.provider_requests=0;self.bodies=[];self.closed=False
    def create(self, **body):
        if self.budget:self.budget.consume(self.model)
        self.provider_requests+=1;self.bodies.append(body)
        raise self.error
    def close(self):self.closed=True


@pytest.mark.parametrize('failures', [1,2,3,4])
def test_exact_order_and_fresh_handoff(failures):
    made=[]
    def factory(cfg):
        fake=Failing(unavailable()) if len(made)<failures else Scripted([{'id':'connected'}])
        made.append((cfg.model,fake));return fake
    session=FailoverSession(AIConfig(api_key='test'),factory,lambda:json.dumps({'question':'Original question','server_prefetched_evidence':[]}))
    session.create(input='Original question',previous_interaction_id='foreign-id')
    assert [m for m,_ in made]==list(DEFAULT_CHAIN[:failures+1])
    assert session.effective_model==DEFAULT_CHAIN[failures]
    assert session.provider_requests==failures+1
    assert len(session.handoffs)==failures
    assert all('previous_interaction_id' not in fake.bodies[0] for _,fake in made[1:])
    assert session.metadata()['fallback_used'] and session.metadata()['fallback_reason']=='high_demand'
    session.close();assert all(fake.closed for _,fake in made)


def test_all_unavailable_and_global_budget():
    budget=RequestBudget(5)
    session=FailoverSession(AIConfig(api_key='test'),lambda cfg:Failing(unavailable(),budget,cfg.model),lambda:'facts')
    with pytest.raises(CopilotError) as e:session.create(input='question')
    assert e.value.code=='provider_unavailable_all_models'
    assert session.metadata()['effective_model'] is None
    assert session.provider_requests==budget.used==5
    assert budget.per_model==dict.fromkeys(DEFAULT_CHAIN,1)
    assert all(c['failed_attempts']==1 for c in session.per_model.values())
    session.close()
    budget=RequestBudget(2)
    session=FailoverSession(AIConfig(api_key='test'),lambda cfg:Failing(unavailable(),budget,cfg.model),lambda:'facts')
    with pytest.raises(CopilotError) as e:session.create(input='question')
    assert e.value.code=='quota_budget_exhausted_locally'
    assert session.provider_requests==budget.used==2
    session.close()


@pytest.mark.parametrize('error',[
    unavailable('authentication',401), unavailable('authentication',403),
    unavailable('provider_configuration',400), unavailable('response_schema',400),
    unavailable('evidence_invalid',None), unavailable('unsupported_number',None),
    unavailable('tools_unavailable',None), unavailable('conversation_context',409),
    unavailable('rate_limited',429,quota_kind='RPD',model_specific_quota=False),
    unavailable('model_unavailable',404,model_endpoint_unavailable=False),
    unavailable('provider_unavailable',500),
])
def test_defects_auth_and_ambiguous_quota_never_failover(error):
    made=[]
    def factory(cfg):made.append(cfg.model);return Failing(error)
    session=FailoverSession(AIConfig(api_key='test'),factory,lambda:'facts')
    with pytest.raises(CopilotError) as e:session.create(input='question')
    assert e.value is error and made==[DEFAULT_CHAIN[0]]
    session.close()


@pytest.mark.parametrize('code,status,extra',[
    ('provider_timeout',504,{}),('model_unavailable',404,{'model_endpoint_unavailable':True}),
    *[('rate_limited',429,{'quota_kind':k,'model_specific_quota':True}) for k in ('RPM','TPM','RPD')],
])
def test_only_explicit_model_availability_can_failover(code,status,extra):
    made=[]
    def factory(cfg):
        fake=Failing(unavailable(code,status,**extra)) if not made else Scripted([{'id':'connected'}])
        made.append(fake);return fake
    session=FailoverSession(AIConfig(api_key='test'),factory,lambda:'facts')
    session.create(input='question');assert session.effective_model==DEFAULT_CHAIN[1]
    session.close()


@pytest.mark.parametrize('model',DEFAULT_CHAIN)
def test_each_model_official_sdk_wire_protocol_and_medium(model):
    sent=[]
    def handle(req):
        sent.append(json.loads(req.content))
        return httpx.Response(200,json={'id':'wire-ok','status':'completed','model':model,'output_text':'{}'})
    cfg=AIConfig(api_key='test',model=model)
    transport=GeminiTransport(cfg);transport.client.close()
    transport.client=genai.Client(api_key='test',http_options=types.HttpOptions(client_args={'transport':httpx.MockTransport(handle)}))
    session=FailoverSession(cfg,lambda _:transport,lambda:'facts')
    session.create(input='question',tools=[{'type':'function','name':'test','parameters':{'type':'object'}}])
    session.create(input=[{'type':'function_result','name':'test','call_id':'native',
        'result':[{'type':'text','text':'{}'}]}],previous_interaction_id='wire-ok',
        response_format={'type':'text','mime_type':'application/json','schema':{'type':'object'}})
    assert all(b['model']==model and b['generation_config']['thinking_level']=='medium' for b in sent)
    assert sent[1]['input'][0]['call_id']=='native' and sent[1]['previous_interaction_id']=='wire-ok'
    assert session.metadata()['effective_model']==model
    session.close()


def test_mid_workflow_preserves_fresh_evidence_and_sticks(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    first=Scripted([turn([call('get_network_summary',args)])])
    original=first.create
    def create(**body):
        if first.bodies:raise unavailable()
        return original(**body)
    first.create=create
    fallback=Scripted([ready(),final(),ready(),final()])
    made=[]
    def factory(cfg):
        made.append(cfg.model)
        return first if cfg.model==DEFAULT_CHAIN[0] else fallback
    svc,repo=service(profiles,factory)
    before=repo.profile_snapshot('BR','redistribution-ready').model_dump_json()
    answer=svc.run(repo,request())
    handoff=json.loads(fallback.bodies[0]['input'])
    assert handoff['context']['profile']=='redistribution-ready'
    assert handoff['server_prefetched_evidence'][0]['evidence_id']=='e1'
    from app.ai.facts import fact_label
    assert next(f['value'] for f in handoff['server_prefetched_evidence'][0]['facts']
        if f['label']==fact_label('summary.facilities'))==answer.evidence[0].value
    assert 'previous_interaction_id' not in fallback.bodies[0]
    assert answer.metadata['effective_model']==DEFAULT_CHAIN[1] and len(answer.tools_used)==1
    # New request must retrieve fresh evidence; provider ID stays within the fallback model.
    fallback.turns=iter([turn([call('get_network_summary',args)],'fallback-next'),ready(),final()])
    followup=svc.run(repo,request(conversation_id=answer.conversation_id))
    assert made==[DEFAULT_CHAIN[0],DEFAULT_CHAIN[1],DEFAULT_CHAIN[1]]
    assert fallback.bodies[2]['previous_interaction_id']==answer.metadata['interaction_id']
    assert followup.metadata['effective_model']==DEFAULT_CHAIN[1] and followup.evidence
    assert repo.profile_snapshot('BR','redistribution-ready').model_dump_json()==before
    # Another conversation starts at primary again.
    first.bodies=[];first.turns=iter([turn([call('get_network_summary',args)])])
    fallback.turns=iter([ready(),final()]);svc.run(repo,request())
    assert made[-2:]==[DEFAULT_CHAIN[0],DEFAULT_CHAIN[1]]


@pytest.mark.parametrize('model',DEFAULT_CHAIN)
def test_shared_positive_plan_and_grounding_for_every_candidate(profiles,model):
    svc,repo=service(profiles,lambda _:DemoTransport(None),model=model)
    response=svc.run(repo,scoped(repo,message='Simulate a severe 14-day dengue surge and find the safest redistribution plan.',allow_planning=True))
    plan=svc.planner.get(response.optimization_run_id,'BR','redistribution-ready')
    assert response.metadata['model']==response.metadata['effective_model']==model
    assert plan.impact.transferred_units>0 and plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
    assert all(t.donor_protected_minimum_after>=t.donor_protected_reserve for t in plan.transfers)
    assert response.evidence and all(t.status=='success' for t in response.tools_used)


def test_invalid_output_remains_failure_and_repeated_quality_failures_quarantine(profiles):
    made=[]
    def factory(cfg):
        made.append(cfg.model)
        return Scripted([turn([call('get_network_summary',{'country_id':'BR','profile':'redistribution-ready'})]),ready(),{'id':'invalid','output_text':'not json'}])
    svc,repo=service(profiles,factory)
    for _ in range(2):
        with pytest.raises(CopilotError) as e:svc.run(repo,request())
        assert e.value.code=='response_schema'
    assert made==[DEFAULT_CHAIN[0]]*2
    assert svc.status()['model_quality'][DEFAULT_CHAIN[0]]=='UNSUITABLE_FOR_HEALTHNEXUS'
    assert svc.audit[-1]['effective_model']==DEFAULT_CHAIN[0]


def test_single_synthesis_smoke_and_explicit_offline(profiles):
    svc,repo=service(profiles,lambda _:DemoTransport(None))
    result=svc.run(repo,request().model_copy(update={'message':'Summarize the current resource resilience status in Pune.'}))
    assert result.metadata['provider_requests']==1 and result.metadata['local_tool_calls']==2
    assert result.evidence and {t.tool for t in result.tools_used}=={'get_network_summary','get_warning_summary'}
    offline=svc.run(repo,request(mode='offline'))
    assert offline.metadata['provider_requests']==0 and offline.metadata['effective_model'] is None


def test_environment_precedence_and_allowed_models(monkeypatch):
    monkeypatch.setenv('GEMINI_MODEL_PRIMARY',DEFAULT_CHAIN[1]);monkeypatch.setenv('GEMINI_MODEL',DEFAULT_CHAIN[0])
    assert AIConfig().model==DEFAULT_CHAIN[1]
    monkeypatch.delenv('GEMINI_MODEL_PRIMARY');assert AIConfig().model==DEFAULT_CHAIN[0]
    monkeypatch.setenv('GEMINI_MODEL_FALLBACKS',','.join(DEFAULT_CHAIN[1:]));assert AIConfig().chain==DEFAULT_CHAIN
    monkeypatch.setenv('GEMINI_FAILOVER_ENABLED','false');assert AIConfig().chain==(DEFAULT_CHAIN[0],)
    for invalid in ('gemini-2.5-flash','gemini-3-flash-preview','gemini-pro','non-google'):
        assert AIConfig(model=invalid).error()[0]=='model_configuration'
        assert AIConfig(fallbacks=(invalid,)).error()[0]=='model_configuration'


@pytest.mark.parametrize('dimension,kind,expected',[
    (DEFAULT_CHAIN[0],'RPM',True), (DEFAULT_CHAIN[0],'TPM',True), (DEFAULT_CHAIN[0],'RPD',True),
    ('other-model','RPM',False), (None,'RPD',False),
])
def test_http_quota_dimension_classification(dimension,kind,expected):
    cfg=AIConfig(api_key='test',same_model_attempts=1)
    transport=GeminiTransport(cfg);transport.client.close()
    def handle(req):
        return httpx.Response(429,json={'error':{'code':429,'message':f'{kind} quota exceeded',
            'details':[{'violations':[{'quotaDimensions':{'model':dimension} if dimension else {}}]}]}})
    transport.client=genai.Client(api_key='test',http_options=types.HttpOptions(client_args={'transport':httpx.MockTransport(handle)}))
    with pytest.raises(CopilotError) as e:transport.create(model=DEFAULT_CHAIN[0],input='question')
    assert e.value.diagnostic['model_specific_quota']==expected
    assert e.value.diagnostic['quota_kind']==kind
    transport.close()


def test_mid_schema_handoff_keeps_actual_plan_without_reexecuting_engines(profiles):
    made=[]
    class AtSynthesis(DemoTransport):
        def create(self,**body):
            if 'response_format' in body:
                self.provider_requests+=1;self.bodies.append(body);raise unavailable()
            return super().create(**body)
    def factory(cfg):
        fake=AtSynthesis(None) if cfg.model==DEFAULT_CHAIN[0] else DemoTransport(None)
        made.append(fake);return fake
    svc,repo=service(profiles,factory)
    ctx=scoped(repo,message='Simulate severe dengue for 14 days and find a redistribution plan',allow_planning=True)
    response=svc.run(repo,ctx)
    assert response.metadata['provider_requests']==5 and response.metadata['local_tool_calls']==5
    assert response.metadata['effective_model']==DEFAULT_CHAIN[1]
    body=made[1].bodies[0];handoff=json.loads(body['input'])
    assert 'previous_interaction_id' not in body and 'tools' not in body
    assert handoff['active_optimization_id']==response.optimization_run_id
    assert handoff['active_scenario_id']==response.scenario_id
    assert len(handoff['server_prefetched_evidence'])==5
    plan=svc.planner.get(response.optimization_run_id,'BR','redistribution-ready')
    assert plan.impact.transferred_units>0 and plan.impact.new_donor_risks==0
    followup=svc.run(repo,ctx.model_copy(update={'message':'Why were these donors selected, and what shortages remain?',
        'allow_planning':False,'conversation_id':response.conversation_id}))
    assert followup.metadata['effective_model']==DEFAULT_CHAIN[1]
    assert made[-1].bodies[0]['previous_interaction_id']==response.metadata['interaction_id']
    assert followup.metadata['provider_requests']==1 and followup.optimization_run_id==response.optimization_run_id


def test_known_model_quota_circuit_does_not_revisit_exhausted_primary(profiles):
    made=[]
    def factory(cfg):
        made.append(cfg.model)
        return Failing(unavailable('rate_limited',429,quota_kind='RPD',model_specific_quota=True)) if cfg.model==DEFAULT_CHAIN[0] else DemoTransport(None)
    svc,repo=service(profiles,factory)
    ctx=request().model_copy(update={'message':'Summarize the current resource resilience status in Pune.'})
    first=svc.run(repo,ctx);second=svc.run(repo,ctx)
    assert made==[DEFAULT_CHAIN[0],DEFAULT_CHAIN[1],DEFAULT_CHAIN[1]]
    assert second.metadata['models_skipped']==[{'model':DEFAULT_CHAIN[0],'reason':'known_model_quota_exhausted'}]
    assert first.metadata['provider_requests']==2 and second.metadata['provider_requests']==1
    assert DEFAULT_CHAIN[0] in svc.status()['models_with_known_quota_exhaustion']


def test_failover_disabled_retains_visible_primary_failure():
    session=FailoverSession(AIConfig(api_key='test',failover_enabled=False),lambda _:Failing(unavailable()),lambda:'facts')
    with pytest.raises(CopilotError) as e:session.create(input='question')
    assert e.value.code=='provider_unavailable' and session.provider_requests==1
    assert not session.handoffs
    session.close()


def test_failed_local_tool_never_disappears_in_handoff(profiles):
    fake=Scripted([turn([call('unknown_tool',{})])])
    original=fake.create;made=[]
    def create(**body):
        if fake.bodies:raise unavailable()
        return original(**body)
    fake.create=create
    def factory(cfg):made.append(cfg.model);return fake
    svc,repo=service(profiles,factory)
    with pytest.raises(CopilotError) as e:svc.run(repo,request())
    assert e.value.code=='tools_unavailable' and made==[DEFAULT_CHAIN[0]]
    assert svc.audit[-1]['tools'][0]['status']=='error'
