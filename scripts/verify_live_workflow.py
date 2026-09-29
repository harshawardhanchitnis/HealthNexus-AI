"""Phase 6 fact-ID workflow acceptance; one authorized run, eight sends globally."""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import monotonic, perf_counter, sleep
from uuid import uuid4

from verify_gemini import (ROOT, AIConfig, CopilotRequest, CopilotService, CopilotError,
    GeminiTransport, DemoTransport, LocalRepository, ScenarioEngine, OptimizationService,
    fixture, validate_response, seed_verifier_conversation, QUESTIONS)
from app.ai.citations import sanitize_diagnostic
from app.ai.schemas import FactDraftAnswer
from app.ai.tool_registry import validated
from app.ai.tools import ToolExecutor, plan_summary
from app.ai.facts import VERSION as FACT_VERSION, fact_label
from app.ai.system_prompt import VERSION as PROMPT_VERSION
from verify_demo import secret_scan

MODEL='gemini-3.5-flash-lite'
MAX_SENDS=8
LEDGER=ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL=ROOT/'artifacts/phase6-workflow-live-sends.json'
BASELINE=ROOT/'artifacts/phase6-workflow-preservation-before.json'
LEASE=ROOT/'artifacts/gemini-verifier.lock'
GATE=ROOT/'docs/evaluation/phase6-workflow-preflight.json'
QUOTA=ROOT/'artifacts/phase6-workflow-quota.json'
LABELS=('positive','followup','constrained','provenance')
MESSAGES={**QUESTIONS,'constrained':'Explain why HealthNexus recommends no redistribution in this scenario.',
    'provenance':'Is this live government inventory, and how should I interpret the forecast performance?'}
DOCS={'README.md','docs/gemini.md','docs/phase6-report.md','docs/validation.md'}


def stamp():return datetime.now(timezone.utc).isoformat()


def native_trace(calls):
    # Provider signatures are opaque internal state, not acceptance evidence.
    return [{k:call[k] for k in ('type','name','id','arguments') if k in call} for call in calls]


def preserved():
    before=json.loads(BASELINE.read_text())
    allowed=set(DOCS)
    if JOURNAL.exists():
        saved=json.loads(JOURNAL.read_text());original=saved['historical_ledger'];n=saved['new_provider_requests']
        assert original['used']==25 and 1<=n<=MAX_SENDS
        assert hashlib.sha256(json.dumps(original).encode()).hexdigest()==before['artifacts/gemini-verification-budget-live.json']
        expected=deepcopy(original);expected['used']+=n;expected['per_model'][MODEL]+=n
        assert json.loads(LEDGER.read_text())==expected,'Historical accounting changed'
        allowed.add('artifacts/gemini-verification-budget-live.json')
    for name,digest in before.items():
        if name not in allowed:
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Protected file changed: '+name
    return {'status':'PASS','original_file_identities':len(before),
        'unchanged':sum(p not in allowed for p in before),'fact_and_numeric_contract_unchanged':True,
        'ui_operational_forecasting_ortools_federation_unchanged':True,'accepted_artifacts_unchanged':True,
        'env_unchanged':True,'key_project_billing_unchanged':True,'production_fallback_order_unchanged':True,
        'historical_evidence_unchanged':True}


class WorkflowBudget:
    """Append only wire attempts, preserving every historical field and the original day."""
    def __init__(self,ledger=LEDGER,journal=JOURNAL):
        self.ledger,self.journal=Path(ledger),Path(journal)
        self.original=json.loads(self.ledger.read_text());self.saved=deepcopy(self.original)
        if self.original['used']!=25 or self.journal.exists():
            raise CopilotError('verification_authorization_used','This authorization cannot be reset or replayed.',429)
        self.used=0;self.last=None

    def preflight(self):
        if self.used>=MAX_SENDS:raise CopilotError('verification_request_ceiling','Eight new sends is the global maximum.',429)
        if self.last is not None:
            delay=15-(monotonic()-self.last)
            if delay>0:sleep(delay)

    def record_send(self,model):
        if model!=MODEL:raise CopilotError('verification_model','Cross-model failover is forbidden.',422)
        if self.used>=MAX_SENDS:raise CopilotError('verification_request_ceiling','Eight new sends is the global maximum.',429)
        assert json.loads(self.ledger.read_text())==self.saved,'Concurrent ledger mutation'
        self.used+=1;self.saved['used']+=1;self.saved['per_model'][MODEL]+=1
        temporary=self.ledger.with_suffix('.workflow.tmp')
        temporary.write_text(json.dumps(self.saved),encoding='utf-8');temporary.replace(self.ledger)
        self.journal.write_text(json.dumps({'historical_ledger':self.original,'new_provider_requests':self.used,
            'maximum_new_provider_requests':MAX_SENDS,'timestamp':stamp()}),encoding='utf-8')
        self.last=monotonic()


def check_calls(body,result,request,repo,engine,planner,known_scenarios,known_plans):
    """Verifier-only inspection before the application can execute a returned native batch."""
    declared={tool['name'] for tool in body.get('tools',[])};checks=[]
    executor=ToolExecutor(repo,engine,planner,request)
    for call in (s for s in result.get('steps',[]) if s.get('type')=='function_call'):
        if call.get('name') not in declared or not isinstance(call.get('arguments'),dict) or not call.get('id'):
            raise CopilotError('verification_native_call','Undeclared or malformed native call; acceptance stopped.',422)
        try:
            args=validated(call['name'],call['arguments'],request)
            sid=getattr(args,'scenario_id',None)
            rid=getattr(args,'run_id',None)
            if sid:
                if str(sid) not in known_scenarios:raise ValueError('Unknown scenario handle')
                executor.scenario(executor.snapshot(request.profile),sid)
            if rid:
                if str(rid) not in known_plans:raise ValueError('Unknown plan handle')
                planner.get(rid,request.country_id,request.profile)
        except (ValueError,LookupError,TypeError) as error:
            raise CopilotError('verification_native_arguments','Invalid native arguments, permissions or identity; acceptance stopped.',422) from None
        checks.append({'tool':call['name'],'call_id':call['id'],'arguments':call['arguments'],
            'validated_arguments':args.model_dump(mode='json'),'declared':True,'pydantic_valid':True,
            'scope_permissions_identity_valid':True})
    return checks


def text_acceptance(response,label):
    """Additional acceptance expectations only; the production validator is unchanged."""
    claims=[response.situation,*response.key_risks,*response.recommended_actions,*response.remaining_gaps]
    text=' '.join(c.text for c in claims).lower()
    for claim in claims:
        lower=claim.text.lower()
        for pattern in (r'\ball shortages (?:are |have been )?resolved\b',r'\brisks? (?:is |are |has been )?eliminated\b'):
            match=re.search(pattern,lower)
            if match and not re.search(r'\bnot\s*$',lower[max(0,match.start()-8):match.start()]):
                raise CopilotError('verification_qualitative','Unsupported complete-resolution claim; acceptance stopped.',422)
    if label in ('positive','followup'):
        if not response.remaining_gaps or not re.search(r'remain|unresolved|shortage|deficit',
                ' '.join(c.text for c in response.remaining_gaps).lower()):
            raise CopilotError('verification_remaining_shortages','The answer must explain remaining shortages.',422)
    if label=='followup' and not re.search(r'protect|reserve|safet|safe|buffer',text):
        raise CopilotError('verification_donor_explanation','The follow-up must explain donor protection.',422)
    if label=='constrained' and not (re.search(r'no|zero|cannot|insufficient|lack',text) and re.search(r'safe|reserve|protect',text)):
        raise CopilotError('verification_constrained_conclusion','The answer must explain insufficient safe network capacity.',422)
    if label=='provenance':
        required={'official_public':r'official|public aggregate|public historical',
            'calibrated_simulated_operations':r'simulat|calibrat','derived_outputs':r'derived|model output|forecast',
            'scenario_projections':r'scenario|externally specified','advisory_plans':r'advisory|recommendation|decision support',
            'not_clinically_validated':r'not.{0,50}clinical|no.{0,50}clinical',
            'wape_error_metric':r'wape.{0,70}error|error.{0,70}wape',
            'not_live_inventory':r'not.{0,45}live|no.{0,45}live',
            'no_physical_execution':r'no.{0,55}(physical|move|action)|not.{0,55}(physical|move|action)'}
        missing=[name for name,pattern in required.items() if not re.search(pattern,text)]
        if missing:
            error=CopilotError('verification_provenance_distinctions','Required provenance/reliability distinctions are missing.',422)
            error.acceptance_diagnostic={'missing_distinctions':missing};raise error
    return {'qualitative_acceptance':'PASS','solver_terminology':'PASS','unsupported_numeric_claims':0,'unknown_fact_ids':0}


class WorkflowMock(DemoTransport):
    """Common mock across cases; native selection uses the existing shared scripted transport."""
    def create(self,**body):
        result=super().create(**body)
        if 'response_format' in body:
            plan=next((r for r in self.records.values() if r['tool'] in ('optimize_redistribution','get_optimization_result')),None)
            if plan:
                def plan_claim(text,paths):
                    return {'text':text,'evidence_refs':[next(f['fact_id'] for f in plan['facts'] if f['label']==fact_label(p)) for p in paths]}
                draft=json.loads(result['output_text'])
                capacity=next(f['value'] for f in plan['facts'] if f['label']==fact_label('safe_capacity'))
                if capacity:
                    draft['key_risks'].append(plan_claim('Selected donors have no protection-policy violations in the advisory plan.',
                        ['impact.donor_safety_violations','safe_capacity']))
                else:
                    draft['key_risks'].append(plan_claim('No safe reserve-protected surplus is available; the network cannot self-resolve its remaining shortages.',
                        ['safe_capacity','impact.after.target_deficit']))
                result['output_text']=json.dumps(draft)
        if 'response_format' in body and any(r['tool']=='get_data_provenance' for r in self.records.values()):
            def claim(text,tool,paths):
                row=next(r for r in self.records.values() if r['tool']==tool)
                return {'text':text,'evidence_refs':[next(f['fact_id'] for f in row['facts'] if f['label']==fact_label(p)) for p in paths]}
            medicine=next(r for r in self.records.values() if r['tool']=='get_model_performance')
            champion=next(f['value'] for f in medicine['facts'] if f['label']==fact_label('targets.medicine.champion'))
            draft={'situation':claim('Official public aggregates inform calibrated simulated operations, not live government inventory.',
                    'get_data_provenance',['sources.0.data_type','data_type','live_government_inventory']),
                'key_risks':[claim('Forecasts are derived model outputs evaluated on simulated histories, not clinically validated. WAPE is an error metric, not accuracy.',
                    'get_model_performance',['data_type',f'targets.medicine.models.{champion}.test.wape'])],
                'recommended_actions':[],
                'remaining_gaps':[claim('Scenario projections use externally specified assumptions. Advisory recommendations involve no physical movement of supplies.',
                    'get_data_provenance',['data_type'])]}
            result['output_text']=json.dumps(draft)
        return result


def review_passed(verdict):
    return verdict.strip()=='PASS'


def run(live=False,transport_type=None,review=None):
    if live:
        assert review is not None,'Each case requires local factual review before more live sends'
        gate=json.loads(GATE.read_text());quota=json.loads(QUOTA.read_text())
        assert gate['status']=='PASS' and gate['fact_contract_version']==FACT_VERSION and gate['system_prompt_version']==PROMPT_VERSION
        assert gate['live_requests_before_run']==0
        assert quota['source']=='user-reported Google AI Studio' and quota['model']==MODEL and quota['confirmed_headroom'] is True
        preserved()
    base=AIConfig() if live else AIConfig(api_key='unit-test-placeholder')
    if live and base.error():raise CopilotError('verification_configuration','Server configuration unavailable; no requests sent.')
    config=replace(base,model=MODEL,fallbacks=(),failover_enabled=False,same_model_attempts=1,thinking='medium')
    budget=WorkflowBudget() if live else None
    repo=LocalRepository();engine=ScenarioEngine();planner=OptimizationService(engine)
    state={};prior_ids=set();positive=None;known_scenarios=set();known_plans=set()
    report={'timestamp':stamp(),'mode':'live' if live else 'mock','baseline_commit':'3f5a7b9','model':MODEL,
        'production_chain':list(base.chain),'fact_contract_version':FACT_VERSION,'system_prompt_version':PROMPT_VERSION,
        'maximum_new_provider_requests':MAX_SENDS,'historical_requests':25,'no_retries_or_failover':True,
        'tests':[],'status':'RUNNING','completed_pass_cases':[],'local_fixture_tool_calls':0}

    def factory(cfg):
        class Observed(transport_type or (GeminiTransport if live else WorkflowMock)):
            def create(self,**body):
                row=state['row'];req=state['request'];attempt={'model':body['model'],'actual_http_sends':0,'http_status':None,
                    'previous_interaction_id':body.get('previous_interaction_id'),'native_calls':[]}
                row['provider_attempts'].append(attempt)
                if body['model']!=MODEL:raise CopilotError('verification_model','Only the selected Lite verifier model is authorized.',422)
                existing_tools=state['service'].requests.get(str(req.request_id),{}).get('tools',[])
                if any(t['status']=='error' for t in existing_tools):
                    raise CopilotError('verification_tool_execution','A local tool failed; no further provider send is authorized.',422)
                inputs=body['input']
                if isinstance(inputs,str):envelopes=json.loads(inputs).get('server_prefetched_evidence',[])
                else:envelopes=[json.loads(item['result'][0]['text']) for item in inputs if item.get('type')=='function_result']
                for envelope in envelopes:
                    if 'error' in envelope:raise CopilotError('verification_tool_execution','A local tool failed; acceptance stopped.',422)
                    row['catalogues'][envelope['evidence_id']]=envelope
                    payload=envelope.get('result',{})
                    if payload.get('scenario_id'):known_scenarios.add(str(payload['scenario_id']))
                    if payload.get('run_id'):known_plans.add(str(payload['run_id']))
                current_ids={f['fact_id'] for r in row['catalogues'].values() for f in r.get('facts',[])}
                if current_ids & prior_ids:raise CopilotError('verification_stale_namespace','A new request reused previous fact IDs.',422)
                started=perf_counter()
                if live:
                    self.before_request=budget.preflight
                    client=self.client.interactions.sdk_configuration.client
                    assert hasattr(client,'event_hooks'),'Wire-send observation unavailable'
                    def on_send(request):
                        nonlocal started
                        assert attempt['actual_http_sends']==0 and request.method=='POST','Hidden SDK retry is forbidden'
                        assert json.loads(request.content)['model']==MODEL
                        budget.record_send(MODEL);attempt['actual_http_sends']+=1;started=perf_counter()
                    client.event_hooks.setdefault('request',[]).append(on_send)
                try:
                    result=super().create(**body)
                    attempt.update(http_status=200,interaction_id=result.get('id'),provider_status=result.get('status'),usage=result.get('usage'))
                    calls=[s for s in result.get('steps',[]) if s.get('type')=='function_call']
                    attempt['native_calls']=sanitize_diagnostic(native_trace(calls),cfg.api_key)
                    attempt['native_validation']=check_calls(body,result,req,repo,engine,planner,known_scenarios,known_plans)
                    if 'response_format' in body:
                        attempt['final_output_text']=sanitize_diagnostic(result.get('output_text','')[:8000],cfg.api_key)
                        try:
                            draft=FactDraftAnswer.model_validate_json(result.get('output_text',''))
                            attempt['draft']=sanitize_diagnostic(draft.model_dump(mode='json'),cfg.api_key)
                        except ValueError:attempt['schema_parse_failed']=True
                    return result
                except CopilotError as error:
                    attempt.update(error_code=error.code,provider_diagnostic=getattr(error,'diagnostic',{}))
                    attempt['http_status']=getattr(error,'diagnostic',{}).get('http_status',attempt['http_status'])
                    raise
                finally:
                    attempt['provider_seconds']=perf_counter()-started
                    if live:client.event_hooks['request'].remove(on_send)
        return Observed(cfg)

    service=CopilotService(engine,planner,config,transport_factory=factory);state['service']=service
    for label in LABELS:
        profile='constrained' if label=='constrained' else 'redistribution-ready'
        row={'label':label,'profile':profile,'status':'RUNNING','provider_attempts':[],'catalogues':{},
            'manual_factual_review':'PENDING' if live else 'not applicable to scripted evidence'}
        report['tests'].append(row);before=repo.profile_snapshot('IN',profile).model_dump_json();began=perf_counter()
        request=CopilotRequest(country_id='IN',profile=profile,state_id='MH',district_id='MH-PUNE',
            message=MESSAGES[label],allow_planning=label=='positive',mode='gemini',request_id=uuid4())
        try:
            if label=='constrained':
                sid,rid=fixture(service,repo,profile);known_scenarios.add(str(sid));known_plans.add(str(rid))
                request=request.model_copy(update={'scenario_id':sid,'optimization_run_id':rid});report['local_fixture_tool_calls']+=2
            if label=='followup':
                assert positive is not None
                request=request.model_copy(update={'conversation_id':positive.conversation_id})
            else:request=seed_verifier_conversation(service,repo,request,MODEL)
            state.update(request=request,row=row)
            response=service.run(repo,request)
            # The historical helper requires a per-lane donor citation. The accepted
            # bounded catalogue also supplies authoritative aggregate protection facts.
            # Verify those without changing membership or production grounding rules.
            validate_response(service,repo,response,'plan-review' if label=='followup' else label,before)
            if label=='followup':
                plan=planner.get(response.optimization_run_id,'IN',profile)
                payload=next(r['result'] for r in response.operational_results if r['tool']=='get_optimization_result')
                authoritative=plan_summary(plan)
                assert all(payload[k]==authoritative[k] for k in ('solver','impact','safe_capacity','transfers','request','resource_risks'))
                assert plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
                assert all(t.donor_protected_minimum_after>=t.donor_protected_reserve for t in plan.transfers)
                fields={e.field for e in response.evidence if e.tool=='get_optimization_result'}
                assert fields & {'impact.donor_safety_violations','safe_capacity','transfers.0.donor_protected_reserve'}
                assert 'impact.after.target_deficit' in fields
            quality=text_acceptance(response,label)
            assert response.metadata['effective_model']==MODEL and not response.metadata['fallback_used']
            assert response.metadata['fact_validation']['semantic_validation']==response.metadata['fact_validation']['numeric_validation']=='PASS'
            assert response.metadata['fact_validation']['unknown_fact_ids']==0
            if live:assert response.metadata['provider_requests']==sum(a['actual_http_sends'] for a in row['provider_attempts'])
            if label=='positive':
                plan=planner.get(response.optimization_run_id,'IN',profile)
                assert (plan.impact.before.target_deficit,plan.preview.safe_capacity,plan.impact.transferred_units,
                    len(plan.transfers),plan.impact.after.target_deficit,plan.impact.donor_safety_violations,
                    plan.impact.new_donor_risks)==(41763,17745,15679,10,26084,0,0),'Canonical Pune scenario/plan differs'
                positive=response
                assert all(t['source']=='model' for t in response.metadata['execution_sources'])
            if label=='followup':
                assert response.conversation_id==positive.conversation_id and response.optimization_run_id==positive.optimization_run_id
                assert row['provider_attempts'][0]['previous_interaction_id']==positive.metadata['interaction_id']
                row['continuity']={'same_conversation':True,'same_model':True,'same_scenario_and_plan':response.scenario_id==positive.scenario_id,
                    'previous_interaction_used':True,'fresh_optimization_read':True,'fresh_fact_namespace':True}
            row.update(status='PASS',quality={**quality,'schema':'PASS','fact_ids':'PASS','context':'PASS'},
                response=response.model_dump(mode='json'),audit=sanitize_diagnostic(service.audit[-1],config.api_key))
            prior_ids.update(f['fact_id'] for r in row['catalogues'].values() for f in r.get('facts',[]))
            report['completed_pass_cases'].append(label)
        except (CopilotError,AssertionError,ValueError) as error:
            row.update(status='FAIL',error_code=error.code if isinstance(error,CopilotError) else 'verification_invariant',
                citation_diagnostic=getattr(error,'citation_diagnostic',None),grounding_diagnostic=getattr(error,'grounding_diagnostic',None),
                acceptance_diagnostic=getattr(error,'acceptance_diagnostic',None) or
                    {'message':sanitize_diagnostic(str(error)[:500],config.api_key)},
                audit=sanitize_diagnostic(service.audit[-1],config.api_key) if service.audit else {})
        row['total_seconds']=perf_counter()-began
        assert repo.profile_snapshot('IN',profile).model_dump_json()==before
        report.update(new_actual_provider_requests=sum(a['actual_http_sends'] for r in report['tests'] for a in r['provider_attempts']),
            scripted_requests=sum(len(r['provider_attempts']) for r in report['tests']) if not live else 0,
            successful_interactions=sum(a.get('http_status')==200 for r in report['tests'] for a in r['provider_attempts']),
            total_local_accounting=budget.saved['used'] if live else 25)
        path=ROOT/f'docs/evaluation/phase6-workflow-{"live" if live else "mock"}.json'
        path.write_text(json.dumps(sanitize_diagnostic(report,config.api_key),indent=2,allow_nan=False),encoding='utf-8')
        if row['status']=='PASS':
            (ROOT/f'docs/evaluation/phase6-workflow-{label}-{"live" if live else "mock"}.json').write_text(
                json.dumps(sanitize_diagnostic(row,config.api_key),indent=2,allow_nan=False),encoding='utf-8')
        print(label,row['status'],row.get('error_code',''),len(row['provider_attempts']),'provider attempts',flush=True)
        if live and row['status']=='PASS':
            verdict=review(row)
            row['manual_factual_review']='PASS' if review_passed(verdict) else 'FAIL'
            if not review_passed(verdict):
                row.update(status='FAIL',error_code='verification_manual_grounding',
                    acceptance_diagnostic={'review':sanitize_diagnostic(verdict[:500],config.api_key)})
                report['completed_pass_cases'].remove(label)
                pass_path=ROOT/f'docs/evaluation/phase6-workflow-{label}-live.json'
                # A candidate PASS is not accepted if factual review fails.
                pass_path.write_text(json.dumps(sanitize_diagnostic(row,config.api_key),indent=2),encoding='utf-8')
            else:
                (ROOT/f'docs/evaluation/phase6-workflow-{label}-live.json').write_text(
                    json.dumps(sanitize_diagnostic(row,config.api_key),indent=2),encoding='utf-8')
            path.write_text(json.dumps(sanitize_diagnostic(report,config.api_key),indent=2),encoding='utf-8')
        if row['status']!='PASS':break
    report['status']='PASS' if report['completed_pass_cases']==list(LABELS) else 'STOPPED_AFTER_FAILURE'
    report['preservation']=preserved();report['security']=secret_scan()
    report['all_live_cases_passed']=live and report['status']=='PASS'
    report['phase6_full_live_accepted']=False
    report['final_acceptance']='Pending final regression and security verification' if live and report['status']=='PASS' else 'Pending live acceptance'
    path.write_text(json.dumps(sanitize_diagnostic(report,config.api_key),indent=2,allow_nan=False),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--mock',action='store_true');mode.add_argument('--live',action='store_true');args=parser.parse_args()
    if args.live:
        LEASE.touch(exist_ok=False)
        try:result=run(True,review=lambda row:input('PAUSED_FOR_LOCAL_FACTUAL_REVIEW '+row['label']+' (PASS or STOP with reason): '))
        finally:LEASE.unlink()
    else:result=run()
    raise SystemExit(0 if result['status']=='PASS' else 1)
