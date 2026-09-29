"""Budgeted, resumable acceptance. --mock is cost-free; --live is explicit opt-in."""
import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter, monotonic, sleep
from datetime import datetime, timezone
from uuid import uuid4
from importlib.metadata import version
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.ai.config import AIConfig, DEFAULT_CHAIN, VERSION as CONFIG_VERSION
from app.ai.schemas import CopilotRequest
from app.ai.orchestrator import CopilotService, context_key
from app.ai.client import CopilotError, GeminiTransport
from app.ai.budget import RequestBudget
from app.ai.tools import ToolExecutor, plan_summary
from app.ai.tool_registry import declarations, SUBSETS, TOOLS, json_schema
from app.ai.system_prompt import VERSION as PROMPT_VERSION, SYSTEM
from app.ai.protocol import byte_size
from app.profiles.config import VERSION as PROFILE_VERSION
from app.profiles.identity import fingerprint
from app.services.repository import LocalRepository
from app.scenarios.engine import ScenarioEngine
from app.optimization.service import OptimizationService

EXPECTED={'positive':4,'followup':1,'constrained':2,'provenance':1,'risk':4,'resilience':1,'model-smoke':1}
QUESTIONS={
    'positive':'Simulate a severe 14-day dengue surge in Pune, identify the most serious resource risks, and find the safest redistribution plan.',
    'followup':'Why were these donors selected, and what shortages remain?',
    'constrained':'Can this constrained Pune scenario be solved by redistribution?',
    'provenance':'Is this live government inventory, and how should I interpret the forecast accuracy?',
    'risk':"Summarize Pune's current resilience risks.",
    'resilience':'Summarize the current resource resilience status in Pune.',
    'model-smoke':'Summarize the current resource resilience status in Pune.',
}


def historical_diagnostics():
    baseline='914ff4a'
    source=subprocess.check_output(['git','show',f'{baseline}:backend/app/ai/tool_registry.py'],cwd=ROOT,text=True)
    node=next(n.value for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=='TOOLS' for t in n.targets))
    old=[{'type':'function','name':ast.literal_eval(k),'description':ast.literal_eval(v.args[1]),
        'parameters':json_schema(TOOLS[ast.literal_eval(k)].schema)} for k,v in zip(node.keys,node.values)]
    source=subprocess.check_output(['git','show',f'{baseline}:backend/app/ai/system_prompt.py'],cwd=ROOT,text=True)
    system=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=='SYSTEM' for t in n.targets))
    history=json.loads((ROOT/'docs/evaluation/phase6-mock.json').read_text(encoding='utf-8'))
    return {'baseline_commit':baseline,'old_schema_bytes_per_turn':byte_size(old),'old_system_bytes_per_turn':len(system.encode()),
        'new_system_bytes_per_turn':len(SYSTEM.encode()),'old_authoritative_result_bytes_by_case':{
            t['label']:sum(byte_size(r['result']) for r in t['response']['operational_results']) for t in history['tests']}}


class DemoTransport:
    """Scripted provider, actual local engines. No hardcoded routes or quantities."""
    def __init__(self, config):
        self.count=0;self.provider_requests=0;self.before_request=None
        self.records={};self.bodies=[]

    def create(self, **body):
        if self.before_request:self.before_request()
        self.provider_requests+=1;self.count+=1;self.bodies.append(body)
        data=body['input']
        if isinstance(data,str):
            data=json.loads(data)
            if 'context' in data:
                self.context=data['context'];self.question=data['question'].lower()
                self.args={k:self.context[k] for k in ('country_id','profile','state_id','district_id')}
            for item in data.get('server_prefetched_evidence',[]):self.records[item['evidence_id']]=item
        else:
            for item in data:
                returned=json.loads(item['result'][0]['text'])
                if 'error' in returned:raise AssertionError(returned['error'])
                self.records[returned['evidence_id']]={'tool':item['name'],'result':returned['result']}
                if returned['result'].get('scenario_id'):self.sid=returned['result']['scenario_id']
        if 'response_format' in body:
            eid,row=next(reversed(self.records.items()));payload=row['result']
            def claim(text,field,evidence=None):return {'text':text,'references':[{'evidence_id':evidence or eid,'field':field}]}
            risks=[];gaps=[]
            plan=next(((e,r['result']) for e,r in self.records.items() if 'solver' in r['result']),None)
            if plan:
                eid,payload=plan
                situation=claim('OR-Tools proved an optimal recommendation under the configured constraints.','solver.status')
                risks=[claim(f"Safe donor capacity is {payload['safe_capacity']} inventory items.",'safe_capacity')]
                risks.append(claim(f"Transfers total {payload['impact']['transferred_units']} inventory items.",'impact.transferred_units'))
                gaps=[claim(f"Unresolved target is {payload['impact']['after']['target_deficit']} inventory items.",'impact.after.target_deficit')]
                if payload['transfers']:
                    risks.append(claim('Selected donors retain protected reserves under the configured policy.','transfers.0.donor_protected_reserve'))
            elif any('live_government_inventory' in r['result'] for r in self.records.values()):
                eid,payload=next((e,r['result']) for e,r in self.records.items() if 'live_government_inventory' in r['result'])
                situation=claim('This is calibrated simulation, not live government inventory.','live_government_inventory')
                performance=next(((e,r['result']) for e,r in self.records.items() if r['tool']=='get_model_performance'),None)
                if performance:
                    risks=[claim('Forecast evaluation uses simulated operational histories; it does not establish clinical accuracy.','data_type',performance[0])]
                    champion=performance[1]['targets']['medicine']['champion']
                    value=performance[1]['targets']['medicine']['models'][champion]['test']['wape']
                    risks.append(claim(f'Medicine forecast test WAPE is {value} on simulated histories.',
                        f'targets.medicine.models.{champion}.test.wape',performance[0]))
            else:situation=claim('Structured warnings identify operational pressure.','summary.total')
            return {'id':f'mock-final-{uuid4()}','status':'completed','output_text':json.dumps({
                'situation':situation,'key_risks':risks,'recommended_actions':[],'remaining_gaps':gaps})}
        def call(name,extra=None):
            return {'type':'function_call','name':name,'arguments':{**self.args,**(extra or {})},'id':f'mock-{self.count}-{name}'}
        scope='district' if self.context.get('district_id') else 'state' if self.context.get('state_id') else 'national'
        if 'simulate' in self.question:
            if self.count==1:calls=[call('run_emergency_scenario',dict(scenario_type='DENGUE_SURGE',severity='severe',duration=14,seed=42))]
            elif self.count==2:calls=[call('get_scenario_comparison',{'scenario_id':self.sid}),
                call('get_warnings',{'scenario_id':self.sid}),call('get_redistribution_preview',{'scenario_id':self.sid,'scope':scope})]
            else:calls=[call('optimize_redistribution',{'scenario_id':self.sid,'scope':scope})]
        elif self.context.get('optimization_run_id'):
            calls=[call('get_optimization_result',{'run_id':self.context['optimization_run_id']})]
        elif self.count==1:calls=[call('get_network_summary')]
        elif self.count==2:calls=[call('get_warnings')]
        else:return {'id':f'mock-ready-{uuid4()}','status':'completed','output_text':'Evidence ready.'}
        return {'id':f'mock-interaction-{uuid4()}','status':'requires_action','steps':calls}

    def close(self):pass


def evidence_identity(config,repo,engine):
    sources=sorted((ROOT/'backend/app').rglob('*.py'))+[Path(__file__),ROOT/'backend/requirements.txt']
    digest=hashlib.sha256()
    for path in sources:
        digest.update(path.relative_to(ROOT).as_posix().encode());digest.update(path.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    return {'git_commit':commit,'implementation_sha256':digest.hexdigest(),'model':config.model,'sdk_version':version('google-genai'),
        'system_prompt_version':PROMPT_VERSION,'system_prompt_sha256':hashlib.sha256(SYSTEM.encode()).hexdigest(),
        'tool_schema_sha256':hashlib.sha256(json.dumps(declarations(),sort_keys=True).encode()).hexdigest(),
        'profile_version':PROFILE_VERSION,'config_version':CONFIG_VERSION,
        'configuration':{'chain':list(config.chain),'failover_enabled':config.failover_enabled,
            'thinking':config.thinking,'max_calls':config.max_calls,'timeout':config.timeout,
            'workflow_timeout':config.workflow_timeout,'max_output_tokens':config.max_output_tokens},
        'credential_fingerprint':hashlib.sha256(config.api_key.encode()).hexdigest(),
        'artifacts':{p:{'snapshot':fingerprint(repo.profile_snapshot('IN',p),repo.profile_snapshot('IN',p).facilities),
            'model_sha256':engine.forecasts.bundle('IN',p)['artifact_sha256']} for p in ('constrained','redistribution-ready')}}


def compatible(saved, identity, mode):
    # Commit recorded for traceability; docs-only commits can reuse materially identical evidence.
    old=saved.get('identity',{})
    required={'git_commit','implementation_sha256','model','sdk_version','system_prompt_version','tool_schema_sha256','profile_version','config_version','artifacts','credential_fingerprint','configuration'}
    return required <= old.keys() and saved.get('mode')==mode and saved.get('entry',{}).get('status')=='passed' and (
        {k:v for k,v in old.items() if k!='git_commit'}=={k:v for k,v in identity.items() if k!='git_commit'})


def save_pass(path,mode,identity,entry):
    if entry.get('status')!='passed':raise ValueError('Only PASS evidence can be retained')
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps({'mode':mode,'identity':identity,'entry':entry},indent=2),encoding='utf-8')
    temp.replace(path)


def fixture(service,repo,profile,country='IN',state='MH',district='MH-PUNE'):
    """Actual deterministic setup, outside Gemini; never a saved invented solution."""
    request=CopilotRequest(country_id=country,profile=profile,state_id=state,district_id=district,
        message='Acceptance fixture',allow_planning=True)
    executor=ToolExecutor(repo,service.engine,service.planner,request)
    scope={k:getattr(request,k) for k in ('country_id','profile','state_id','district_id')}
    scenario=executor.execute('run_emergency_scenario',{**scope,'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,'seed':42})
    plan=executor.execute('optimize_redistribution',{**scope,'scenario_id':scenario['scenario_id'],
        'scope':'district' if district else 'state' if state else 'national'})
    return scenario['scenario_id'],plan['run_id']


def validate_response(service,repo,response,label,before):
    assert response.status=='completed' and response.mode!='refusal'
    assert all(t.status=='success' for t in response.tools_used)
    assert before==repo.profile_snapshot('IN',response.context.profile).model_dump_json()
    for row in response.operational_results:
        assert row['result']['context']['country_id']=='IN' and row['result']['context']['profile']==response.context.profile
    if label in ('positive','constrained','followup'):
        plan=service.planner.get(response.optimization_run_id,'IN',response.context.profile)
        payload=next(r['result'] for r in response.operational_results if r['tool'] in ('optimize_redistribution','get_optimization_result'))
        authoritative=plan_summary(plan)
        for key in ('solver','impact','safe_capacity','transfers','request','warnings_before','warnings_after','resource_risks'):
            assert payload[key]==authoritative[key],key
        assert plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
        assert sum(t.quantity for t in plan.transfers)==plan.impact.transferred_units
        assert all(t.donor_protected_minimum_after>=t.donor_protected_reserve for t in plan.transfers)
        if label=='constrained':
            assert plan.preview.safe_capacity==plan.impact.transferred_units==0
            assert plan.impact.after.target_deficit==30230
        else:
            assert plan.impact.transferred_units>0 and plan.impact.after.target_deficit<plan.impact.before.target_deficit
        if label=='positive':
            assert {'run_emergency_scenario','optimize_redistribution'} <= {t.tool for t in response.tools_used}
            scenario=service.engine.store.get(response.scenario_id,'IN',response.context.profile).scenario.definition
            assert scenario.scenario_type.value=='DENGUE_SURGE' and scenario.severity=='severe' and scenario.duration==14
    if label=='provenance':assert {'get_data_provenance','get_model_performance'} <= {t.tool for t in response.tools_used}
    assert response.evidence
    cited={e.field for e in response.evidence}
    if response.mode=='offline':return
    if label in ('positive','constrained'):
        assert {'safe_capacity','impact.transferred_units','impact.after.target_deficit','solver.status'} <= cited
    if label=='followup':
        assert 'impact.after.target_deficit' in cited
        assert any(e.tool=='get_optimization_result' and e.field.startswith('transfers.') and
            'donor_' in e.field for e in response.evidence)
    if label=='provenance':
        assert any(e.tool=='get_data_provenance' and e.field=='live_government_inventory' and e.value is False for e in response.evidence)
        assert any(e.tool=='get_model_performance' for e in response.evidence)


def seed_verifier_conversation(service,repo,request,model,previous=None,conversation_id=None):
    """Verifier-only starting candidate; production config and default chain stay intact."""
    cid=conversation_id or str(uuid4())
    service.conversations[cid]={'key':context_key(request),'origin':str(repo.profile_snapshot(request.country_id,request.profile).as_of),
        'previous':previous,'effective_model':model,'fallback_reason':'verifier_targeted_candidate',
        'scenario_id':None,'run_id':None,'updated':monotonic(),'busy':False}
    return request.model_copy(update={'conversation_id':cid})


def verify(mode, output, case=None, acceptance=False, resume=False, evidence_dir=None, budget_limit=10,
           start_model=None, explicit_budget_override=False):
    config=AIConfig(api_key='unit-test-placeholder') if mode=='mock' else AIConfig()
    if start_model and (mode=='offline' or start_model not in config.chain):
        raise ValueError('--model must be a configured Gemini candidate and cannot be used in offline mode')
    if case=='model-smoke' and not start_model:raise ValueError('model-smoke requires an explicit --model candidate')
    # Validate bounds before touching the lease, artifacts or provider.
    RequestBudget(budget_limit,explicit_override=explicit_budget_override)
    if mode=='live' and config.error():
        report={'mode':mode,'status':'not_run','reason':config.error()[0],'model':config.model}
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report));return 2
    evidence_dir=Path(evidence_dir or ROOT/'artifacts/gemini-acceptance'/mode)
    evidence_dir.mkdir(parents=True,exist_ok=True)
    # A single CLI process owns both evidence and daily ledger; do not run verifiers concurrently.
    lease=ROOT/'artifacts/gemini-verifier.lock';lease.parent.mkdir(parents=True,exist_ok=True)
    try:lease.touch(exist_ok=False)
    except FileExistsError:raise ValueError('Another verifier owns the ledger; wait for it to finish')
    try:return _verify(mode,output,case,acceptance,resume,evidence_dir,budget_limit,config,start_model,explicit_budget_override)
    finally:lease.unlink()


def _verify(mode,output,case,acceptance,resume,evidence_dir,budget_limit,config,start_model,explicit_budget_override):
    engine=ScenarioEngine();planner=OptimizationService(engine);repo=LocalRepository()
    budget=RequestBudget(budget_limit,ROOT/'artifacts/gemini-verification-budget-live.json' if mode=='live' else None,
        explicit_override=explicit_budget_override)
    initial_used=budget.used;last_request=[None]
    def before_request(model):
        # 5 RPM free tier: space live requests conservatively. No automatic 429 retry.
        if budget.used>=budget.limit:budget.consume(model)
        if mode=='live' and last_request[0] is not None:
            delay=13-(monotonic()-last_request[0])
            if delay>0:sleep(delay)
        budget.consume(model);last_request[0]=monotonic()
    def factory(cfg):
        transport=DemoTransport(cfg) if mode=='mock' else GeminiTransport(cfg)
        transport.before_request=lambda:before_request(cfg.model)
        return transport
    service=CopilotService(engine,planner,config,transport_factory=factory)
    identity=evidence_identity(config,repo,engine)
    identity['verification_start_model']=start_model
    labels=[case] if case else ['positive','followup','constrained','provenance']
    report={'mode':mode,'model':config.model if mode!='offline' else None,'status':'passed',
        'live_acceptance':mode=='live','timestamp':datetime.now(timezone.utc).isoformat(),
        'identity':{k:v for k,v in identity.items() if k!='credential_fingerprint'},
        'credential_binding':'Private resumable evidence retains a one-way credential fingerprint; public report omits it.',
        'selected_case':case,'acceptance':acceptance or case is None,'tests':[],
        'verification_start_model':start_model,'production_chain':list(config.chain),
        'existing_daily_sends':initial_used,'explicit_budget_override':explicit_budget_override,
        'newly_authorized_allowance':max(0,budget_limit-initial_used),
        'budget_limit':budget_limit,'expected_provider_requests':sum(EXPECTED[l] for l in labels) if mode!='offline' else 0,
        'maximum_provider_requests':budget_limit,'local_fixture_tool_calls':0,
        'comparison':{'old_suite_expected_provider_requests':23,'old_cases':{'risk':4,'positive':8,'constrained':8,'provenance':3},
            'new_acceptance_expected_provider_requests':8,**historical_diagnostics(),
            'schema_bytes_by_intent':{k:byte_size(declarations(v)) for k,v in SUBSETS.items()},
            'token_estimate_method':'characters / 4; estimates are not Gemini token counts'},
        'resume_invalidated':[]}
    positive=None;session_model=start_model;smoke=None
    smoke_path=evidence_dir/'model-smoke.json'
    if start_model and resume and case!='model-smoke' and smoke_path.exists():
        candidate=json.loads(smoke_path.read_text(encoding='utf-8'))
        if compatible(candidate,identity,mode):
            smoke=candidate['entry']['response'];session_model=smoke['metadata']['effective_model']
            report['resumed_model_smoke']=True
    for label in labels:
        profile='redistribution-ready' if label in ('positive','followup','risk','resilience','model-smoke') else 'constrained'
        path=evidence_dir/f'{label}.json'
        saved=json.loads(path.read_text(encoding='utf-8')) if resume and path.exists() else None
        if saved and compatible(saved,identity,mode):
            entry={**saved['entry'],'reused':True};report['tests'].append(entry)
            if label=='positive':positive=entry['response']
            if start_model:session_model=entry['response']['metadata']['effective_model']
            print(label,'reused compatible',mode,'PASS evidence',flush=True);continue
        if saved:report['resume_invalidated'].append(label)
        before=repo.profile_snapshot('IN',profile).model_dump_json();began=perf_counter()
        context=dict(country_id='IN',profile=profile,state_id='MH',district_id='MH-PUNE')
        request=CopilotRequest(**context,message=QUESTIONS[label],mode='offline' if mode=='offline' else 'gemini',allow_planning=label=='positive')
        try:
            if label=='constrained':
                sid,run_id=fixture(service,repo,profile);report['local_fixture_tool_calls']+=2
                request=request.model_copy(update={'scenario_id':sid,'optimization_run_id':run_id})
            if label=='followup':
                if not positive:raise AssertionError('Follow-up needs compatible positive evidence')
                cid=positive['conversation_id']
                if cid not in service.conversations:
                    # Rebuild current real fixtures when resuming on another day/process.
                    sid,run_id=fixture(service,repo,profile);report['local_fixture_tool_calls']+=2
                    service.conversations[cid]={'key':context_key(request),'origin':str(repo.profile_snapshot('IN',profile).as_of),
                        'previous':positive['metadata']['interaction_id'],'effective_model':positive['metadata'].get('effective_model',config.model),
                        'scenario_id':sid,'run_id':run_id,'updated':monotonic(),'busy':False}
                request=request.model_copy(update={'conversation_id':cid})
            elif session_model:
                use_smoke=smoke if label=='positive' else None
                request=seed_verifier_conversation(service,repo,request,session_model,
                    previous=use_smoke['metadata']['interaction_id'] if use_smoke else None,
                    conversation_id=use_smoke['conversation_id'] if use_smoke else None)
            response=service.run(repo,request)
            validate_response(service,repo,response,label,before)
            if label in ('followup','provenance'):assert response.metadata['provider_requests']==(0 if mode=='offline' else 1)
            entry={'label':label,'profile':profile,'status':'passed','seconds':perf_counter()-began,
                'quality':{'structured_response_valid':True,'evidence_validation_passed':True,
                    'invalid_tool_calls':sum(t.status!='success' for t in response.tools_used),'unsupported_numeric_claims':0},
                'fixture_setup':'actual local scenario + OR-Tools' if label=='constrained' else None,
                'followup_parent_interaction':positive['metadata']['interaction_id'] if label=='followup' else None,
                'response':response.model_dump(mode='json')}
            report['tests'].append(entry)
            if label=='positive':positive=entry['response']
            if start_model:session_model=response.metadata['effective_model']
            save_pass(path,mode,identity,entry)
            print(label,profile,'passed',response.metadata['provider_requests'],'provider requests',len(response.tools_used),'local tools',flush=True)
        except (CopilotError,AssertionError) as error:
            report['status']='failed';report['tests'].append({'label':label,'profile':profile,'status':'failed',
                'code':error.code if isinstance(error,CopilotError) else 'accuracy_failure','seconds':perf_counter()-began,
                'diagnostics':dict(service.audit[-1]) if service.audit else {}})
            print(label,'failed',report['tests'][-1]['code'],flush=True);break
    report['provider_requests']=budget.used-initial_used;report['daily_ledger_used']=budget.used
    report['new_provider_sends']=report['provider_requests'];report['final_cumulative_sends']=budget.used
    report['daily_provider_requests_per_model']=budget.per_model
    reused={t['label'] for t in report['tests'] if t.get('reused')}
    report['expected_provider_requests_this_run']=sum(EXPECTED[l] for l in labels if l not in reused) if mode!='offline' else 0
    report['local_tool_calls']=sum(t.get('response',{}).get('metadata',{}).get('local_tool_calls',
        t.get('diagnostics',{}).get('local_tool_calls',0)) for t in report['tests'] if not t.get('reused'))
    report['retained_pass_cases']=[t['label'] for t in report['tests'] if t['status']=='passed']
    report['capabilities_accepted']=list('ABCDEFGH') if mode=='live' and report['status']=='passed' and set(labels)=={'positive','followup','constrained','provenance'} else []
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return 0 if report['status']=='passed' else 1


def parser():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for mode in ('live','offline','mock'):group.add_argument('--'+mode,action='store_true')
    p.add_argument('--output',type=Path)
    selection=p.add_mutually_exclusive_group()
    selection.add_argument('--case',choices=['risk','positive','constrained','provenance','resilience','model-smoke'])
    selection.add_argument('--acceptance',action='store_true')
    p.add_argument('--resume',action='store_true',help='Reuse only compatible same-mode PASS evidence')
    p.add_argument('--evidence-dir',type=Path)
    p.add_argument('--model',choices=DEFAULT_CHAIN,help='Verifier-only sticky starting candidate; production order is unchanged')
    p.add_argument('--budget',type=int,help='Explicit cumulative ceiling (1–14); omitted uses the normal 1–10 environment/default cap')
    return p


if __name__=='__main__':
    args=parser().parse_args();mode=next(m for m in ('live','offline','mock') if getattr(args,m))
    budget=args.budget if args.budget is not None else int(os.getenv('GEMINI_DAILY_VERIFICATION_BUDGET','10'))
    sys.exit(verify(mode,args.output or ROOT/f'docs/evaluation/phase6-budget-{mode}.json',args.case,
        args.acceptance,args.resume,args.evidence_dir,budget,args.model,args.budget is not None and args.budget>10))
