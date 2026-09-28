"""Cost-free quota/protocol tests: only scripted or HTTP-mocked Gemini transports."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import httpx
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_gemini import DemoTransport, EXPECTED, compatible, fixture, parser, save_pass, seed_verifier_conversation
from app.ai.config import DEFAULT_CHAIN
from test_ai import service, request, Scripted, turn, call, ready, final
from test_profiles import profiles, trained
from app.ai.budget import RequestBudget
from app.ai.client import CopilotError, GeminiTransport, provider_error
from app.ai.config import AIConfig, MODEL
from app.ai.tool_registry import SUBSETS, intent, declarations


def scoped(repo,profile='redistribution-ready',**kwargs):
    f=repo.profile_snapshot('BR',profile).facilities[0]
    return request(state_id=f.state_id,district_id=f.district_id).model_copy(update={'profile':profile,**kwargs})


def test_budget_reserves_before_call_and_persists(tmp_path):
    path=tmp_path/'budget.json';budget=RequestBudget(2,path)
    budget.consume();RequestBudget(2,path).consume()
    blocked=RequestBudget(2,path)
    with pytest.raises(CopilotError) as error:blocked.consume()
    assert error.value.code=='quota_budget_exhausted_locally' and blocked.used==2
    data=json.loads(path.read_text());data['day']='2000-01-01';path.write_text(json.dumps(data))
    fresh=RequestBudget(2,path);assert fresh.used==0
    fresh.consume();assert json.loads(path.read_text())['used']==1


@pytest.mark.parametrize('limit',[0,11,-1])
def test_cannot_configure_above_hard_ten_request_budget(limit):
    with pytest.raises(ValueError):RequestBudget(limit)


def test_sdk_retry_counts_and_local_denial_never_sends_retry(monkeypatch):
    from google import genai
    from google.genai import types
    monkeypatch.setattr('app.ai.client.sleep',lambda _:None)
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'))
    budget=RequestBudget(1);transport.before_request=budget.consume;sent=[]
    def handle(request):
        sent.append(request)
        return httpx.Response(503,json={'error':{'code':503,'message':'Mock unavailable','status':'UNAVAILABLE'}})
    transport.client.close()
    transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handle)},retry_options=types.HttpRetryOptions(attempts=0)))
    with pytest.raises(CopilotError) as error:transport.create(model=MODEL,input='Test')
    transport.close()
    assert error.value.code=='quota_budget_exhausted_locally'
    assert len(sent)==transport.provider_requests==budget.used==1


@pytest.mark.parametrize('message,kind',[
    ('limit: 20 requests per day on Free Tier','RPD'),
    ('RequestsPerMinute limit','RPM'),('TokensPerMinute limit','TPM'),('Unknown quota','unknown')])
def test_distinct_quota_diagnostics_and_no_rpd_retry(monkeypatch,message,kind):
    from google import genai
    from google.genai import types
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'));sent=[]
    def handle(request):
        sent.append(request)
        return httpx.Response(429,headers={'retry-after':'59'},json={'error':{'code':429,'message':message,'status':'RESOURCE_EXHAUSTED'}})
    transport.client.close()
    transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handle)},retry_options=types.HttpRetryOptions(attempts=0)))
    with pytest.raises(CopilotError) as error:transport.create(model=MODEL,input='Test')
    transport.close()
    assert len(sent)==1 and error.value.diagnostic['quota_kind']==kind
    assert error.value.diagnostic['retry_after']=='59' and 'billing' not in error.value.message.lower()


@pytest.mark.parametrize('message,updates,expected',[
    ('Is this live government inventory?',{},'provenance'),
    ('How should I interpret forecast accuracy?',{},'provenance'),
    ('Simulate a surge',{'allow_planning':True},'emergency-planning'),
    ('Why these donors?',{'optimization_run_id':'actual-plan'},'follow-up-plan'),
    ('Can this be solved?',{'optimization_run_id':'actual-plan'},'plan-review'),
    ('Summarize risks',{},'network-risk')])
def test_server_owned_intent_subsets(message,updates,expected):
    ctx=request().model_copy(update={'message':message,**updates})
    assert intent(ctx)==expected
    assert {d['name'] for d in declarations(SUBSETS[expected])}==SUBSETS[expected]
    assert len(declarations(SUBSETS[expected]))<13
    with pytest.raises(ValueError):type(ctx).model_validate({**ctx.model_dump(),'tool_names':['exec']})


def test_registered_but_outside_intent_tool_is_rejected(profiles):
    args={'country_id':'BR','profile':'redistribution-ready'}
    fake=Scripted([turn([call('get_data_provenance',args)]),turn([call('get_network_summary',args)]),ready(),final()])
    svc,repo=service(profiles,lambda _:fake);answer=svc.run(repo,request())
    assert answer.tools_used[0].status=='error'
    assert 'error' in json.loads(fake.bodies[1]['input'][0]['result'][0]['text'])
    assert all(r['tool']!='get_data_provenance' for r in answer.operational_results)


def test_one_interaction_provenance_and_performance_with_fresh_evidence(profiles):
    fake=DemoTransport(None);svc,repo=service(profiles,lambda _:fake)
    response=svc.run(repo,request().model_copy(update={'message':'Is this live government inventory, and how should I interpret the forecast accuracy?'}))
    assert response.metadata['provider_requests']==fake.provider_requests==1
    assert response.metadata['local_tool_calls']==2
    assert all(x['source']=='server-prefetch' for x in response.metadata['execution_sources'])
    assert {'get_data_provenance','get_model_performance'}=={e.tool for e in response.evidence}
    assert 'tools' not in fake.bodies[0] and fake.bodies[0]['response_format']
    assert json.loads(fake.bodies[0]['input'])['server_prefetched_evidence'][0]['result']['live_government_inventory'] is False


def test_optimized_positive_and_one_interaction_stateful_followup(profiles):
    fakes=[]
    def factory(_):
        fake=DemoTransport(None);fakes.append(fake);return fake
    svc,repo=service(profiles,factory)
    ctx=scoped(repo,message='Simulate a severe 14-day dengue surge and find the safest redistribution plan.',allow_planning=True)
    before=repo.profile_snapshot('BR',ctx.profile).model_dump_json()
    positive=svc.run(repo,ctx)
    assert positive.metadata['provider_requests']==4 and positive.metadata['local_tool_calls']==5
    assert [len(b.get('tools',[])) for b in fakes[0].bodies]==[8,8,8,0]
    assert isinstance(fakes[0].bodies[-1]['input'],list)
    assert fakes[0].bodies[-1]['input'][0]['name']=='optimize_redistribution'
    assert fakes[0].bodies[-1]['previous_interaction_id']==positive.metadata['interaction_ids'][-2]
    plan=svc.planner.get(positive.optimization_run_id,'BR',ctx.profile)
    assert plan.impact.transferred_units>0 and plan.impact.donor_safety_violations==plan.impact.new_donor_risks==0
    assert repo.profile_snapshot('BR',ctx.profile).model_dump_json()==before
    followup=svc.run(repo,ctx.model_copy(update={'message':'Why were these donors selected, and what shortages remain?',
        'allow_planning':False,'conversation_id':positive.conversation_id}))
    assert followup.metadata['provider_requests']==followup.metadata['local_tool_calls']==1
    assert fakes[1].bodies[0]['previous_interaction_id']==positive.metadata['interaction_id']
    assert followup.tools_used[0].tool=='get_optimization_result'
    assert followup.evidence[0].evidence_id=='e1'


def test_constrained_minimal_native_result_continuation(profiles):
    fake=DemoTransport(None);svc,repo=service(profiles,lambda _:fake)
    ctx=scoped(repo,'constrained',message='Can this constrained scenario be solved by redistribution?')
    sid,run_id=fixture(svc,repo,'constrained','BR',ctx.state_id,ctx.district_id)
    response=svc.run(repo,ctx.model_copy(update={'scenario_id':sid,'optimization_run_id':run_id}))
    assert response.metadata['provider_requests']==2 and response.metadata['local_tool_calls']==1
    assert len(fake.bodies[0]['tools'])==2 and 'tools' not in fake.bodies[1]
    assert fake.bodies[1]['input'][0]['call_id']=='mock-1-get_optimization_result'
    assert response.operational_results[0]['result']['safe_capacity']==0
    assert response.operational_results[0]['result']['impact']['transferred_units']==0


def test_budget_failure_preserves_exact_attempt_count_in_audit(profiles):
    fake=DemoTransport(None);budget=RequestBudget(3);fake.before_request=budget.consume
    svc,repo=service(profiles,lambda _:fake)
    with pytest.raises(CopilotError) as error:
        svc.run(repo,scoped(repo,message='Simulate severe dengue for 14 days and find a redistribution plan',allow_planning=True))
    assert error.value.code=='quota_budget_exhausted_locally'
    assert fake.provider_requests==svc.audit[-1]['provider_requests']==3
    assert svc.audit[-1]['local_tool_calls']==5


def test_provider_retry_attempts_are_counted_in_service_metadata(profiles,monkeypatch):
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'));sent=[]
    monkeypatch.setattr('app.ai.client.sleep',lambda _:None)
    class Unavailable(Exception):code=503
    args={'country_id':'BR','profile':'redistribution-ready'}
    sequence=iter([turn([call('get_network_summary',args)]),ready(),final()])
    def create(**body):
        sent.append(body)
        if len(sent)==1:raise Unavailable()
        data=next(sequence)
        return SimpleNamespace(model_dump=lambda **_:data,output_text=data.get('output_text',''))
    monkeypatch.setattr(transport.client.interactions,'create',create)
    budget=RequestBudget(4);transport.before_request=budget.consume
    svc,repo=service(profiles,lambda _:transport);response=svc.run(repo,request())
    assert response.metadata['provider_requests']==budget.used==len(sent)==4
    assert response.metadata['interaction_count']==3 and response.metadata['local_tool_calls']==1


def test_positive_valid_alternative_tool_order_is_not_forced(profiles):
    class Alternative(DemoTransport):
        def create(self,**body):
            if self.count==1 and 'response_format' not in body:
                data=json.loads(body['input'][0]['result'][0]['text']);sid=data['result']['scenario_id']
                self.count+=1;self.provider_requests+=1;self.bodies.append(body)
                return {'id':'alternative-batch','steps':[
                    call('get_warnings',{**self.args,'scenario_id':sid},'warnings'),
                    call('optimize_redistribution',{**self.args,'scenario_id':sid,'scope':'state'},'optimizer')]}
            return super().create(**body)
    fake=Alternative(None);svc,repo=service(profiles,lambda _:fake)
    response=svc.run(repo,scoped(repo,message='Simulate severe dengue and optimize redistribution',allow_planning=True))
    assert response.metadata['provider_requests']==3
    assert [t.tool for t in response.tools_used]==['run_emergency_scenario','get_warnings','optimize_redistribution']
    assert response.operational_results[-1]['result']['impact']['transferred_units']>0


def test_official_sdk_function_result_schema_only_continuation(monkeypatch):
    from google import genai
    from google.genai import types
    sent=[]
    def handle(request):
        sent.append(json.loads(request.content));return httpx.Response(200,json={'id':'wire-final','status':'completed','model':MODEL,'output_text':'{}'})
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder'));transport.client.close()
    transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handle)},retry_options=types.HttpRetryOptions(attempts=1)))
    from app.ai.schemas import DraftAnswer
    transport.create(model=MODEL,previous_interaction_id='native-id',input=[{'type':'function_result',
        'name':'get_optimization_result','call_id':'native-call','result':[{'type':'text','text':'{}'}]}],
        response_format={'type':'text','mime_type':'application/json','schema':DraftAnswer.model_json_schema()})
    transport.close()
    assert sent[0]['previous_interaction_id']=='native-id' and sent[0]['input'][0]['call_id']=='native-call'
    assert 'tools' not in sent[0] and sent[0]['response_format']['schema']


def test_pass_evidence_resume_mode_and_material_staleness(tmp_path):
    identity={k:'same' for k in ('git_commit','implementation_sha256','model','sdk_version','system_prompt_version',
        'tool_schema_sha256','profile_version','config_version','artifacts','credential_fingerprint','configuration')}
    path=tmp_path/'positive.json';save_pass(path,'live',identity,{'status':'passed'})
    saved=json.loads(path.read_text());assert compatible(saved,identity,'live')
    assert compatible(saved,{**identity,'git_commit':'docs-only-new-commit'},'live')
    assert not compatible(saved,identity,'mock')
    for key in identity.keys()-{'git_commit'}:assert not compatible(saved,{**identity,key:'changed'},'live'),key
    with pytest.raises(ValueError):save_pass(path,'live',identity,{'status':'failed'})
    assert compatible(json.loads(path.read_text()),identity,'live')
    assert not compatible({'mode':'live','entry':{'status':'passed'}},{},'live')


@pytest.mark.parametrize('case',['positive','constrained','provenance'])
def test_selective_and_resumable_cli(case):
    args=parser().parse_args(['--mock','--case',case,'--resume'])
    assert args.case==case and args.resume and not args.acceptance
    assert sum(EXPECTED[k] for k in ('positive','followup','constrained','provenance'))==8


def test_explicit_fourteen_ceiling_preserves_cumulative_history(tmp_path):
    path=tmp_path/'ledger.json';initial=RequestBudget(10,path)
    for _ in range(10):initial.consume('historical-model')
    historical=json.loads(path.read_text())
    with pytest.raises(ValueError):RequestBudget(14,path)
    extended=RequestBudget(14,path,explicit_override=True)
    assert extended.used==10 and extended.per_model==historical['per_model']
    for _ in range(4):extended.consume(DEFAULT_CHAIN[3])
    with pytest.raises(CopilotError) as e:extended.consume(DEFAULT_CHAIN[4])
    assert e.value.code=='quota_budget_exhausted_locally'
    assert extended.used==14 and json.loads(path.read_text())['per_model']=={'historical-model':10,DEFAULT_CHAIN[3]:4}


@pytest.mark.parametrize('limit',[0,15,100])
def test_explicit_override_still_bounded(limit):
    with pytest.raises(ValueError):RequestBudget(limit,explicit_override=True)


def test_targeted_cli_only_exposes_approved_candidate_and_explicit_budget():
    args=parser().parse_args(['--live','--case','model-smoke','--model',DEFAULT_CHAIN[3],'--budget','14'])
    assert args.model==DEFAULT_CHAIN[3] and args.budget==14 and args.case=='model-smoke'
    assert parser().parse_args(['--mock']).budget is None
    with pytest.raises(SystemExit):parser().parse_args(['--live','--model','gemini-pro'])


def test_targeted_smoke_skips_old_models_and_preserves_production_config(profiles):
    made=[]
    def factory(cfg):
        made.append(cfg.model);return DemoTransport(cfg)
    svc,repo=service(profiles,factory)
    ctx=scoped(repo,message='Summarize the current resource resilience status in Pune.')
    original=svc.config;before=repo.profile_snapshot('BR','redistribution-ready').model_dump_json()
    answer=svc.run(repo,seed_verifier_conversation(svc,repo,ctx,DEFAULT_CHAIN[3]))
    assert made==[DEFAULT_CHAIN[3]] and svc.config is original and svc.config.chain==DEFAULT_CHAIN
    assert answer.metadata['provider_requests']==1 and answer.metadata['fallback_used']
    assert answer.metadata['requested_model']==DEFAULT_CHAIN[0] and answer.metadata['effective_model']==DEFAULT_CHAIN[3]
    assert repo.profile_snapshot('BR','redistribution-ready').model_dump_json()==before
    assert answer.evidence and answer.mode=='gemini'
    followup=svc.run(repo,ctx.model_copy(update={'conversation_id':answer.conversation_id}))
    assert made==[DEFAULT_CHAIN[3],DEFAULT_CHAIN[3]]
    assert followup.metadata['effective_model']==DEFAULT_CHAIN[3]


def test_targeted_three_five_availability_failure_only_reaches_lite(profiles):
    from test_ai_failover import Failing, unavailable
    made=[]
    def factory(cfg):
        made.append(cfg.model)
        return Failing(unavailable()) if cfg.model==DEFAULT_CHAIN[3] else DemoTransport(cfg)
    svc,repo=service(profiles,factory)
    ctx=scoped(repo,message='Summarize the current resource resilience status in Pune.')
    answer=svc.run(repo,seed_verifier_conversation(svc,repo,ctx,DEFAULT_CHAIN[3]))
    assert made==list(DEFAULT_CHAIN[3:]) and answer.metadata['provider_requests']==2
    assert answer.metadata['effective_model']==DEFAULT_CHAIN[4] and answer.metadata['fallback_used']
    assert answer.metadata['fallback_chain_attempted']==list(DEFAULT_CHAIN[3:])


def test_targeted_schema_failure_never_tests_lite(profiles):
    fake=Scripted([{'id':'invalid-final','output_text':'not JSON'}]);made=[]
    def factory(cfg):made.append(cfg.model);return fake
    svc,repo=service(profiles,factory)
    ctx=scoped(repo,message='Summarize the current resource resilience status in Pune.')
    with pytest.raises(CopilotError) as e:svc.run(repo,seed_verifier_conversation(svc,repo,ctx,DEFAULT_CHAIN[3]))
    assert e.value.code=='response_schema' and made==[DEFAULT_CHAIN[3]]
