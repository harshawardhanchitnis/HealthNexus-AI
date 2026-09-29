"""One gated six-send Phase 6 run. Mocks use the official SDK and real local engines."""
import argparse
from copy import deepcopy
from dataclasses import replace
from importlib.metadata import version
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic,perf_counter,sleep
from uuid import uuid4
import xml.etree.ElementTree as ET
import httpx
from google import genai
from google.genai import types
from verify_gemini import (ROOT,AIConfig,CopilotRequest,CopilotError,GeminiTransport,
    CopilotService,LocalRepository,ScenarioEngine,OptimizationService,fixture,QUESTIONS,validate_response)
from verify_live_workflow import check_calls,native_trace
from verify_positive_final import stamp,digest
from verify_demo import secret_scan
from app.ai.action_state import advisory_state,check_action_claim
from app.ai.schemas import FactDraftAnswer
from app.ai.tool_registry import declarations
from app.ai.facts import fact_label
from app.ai.citations import sanitize_diagnostic
from app.ai.synthesis import VERSION as NARRATIVE_VERSION
from app.ai.system_prompt import VERSION as PROMPT_VERSION

MODEL='gemini-3.5-flash-lite'
MAX_SENDS=6
LABELS=('positive','followup','constrained','provenance')
MESSAGES={'positive':QUESTIONS['positive'],'followup':'Why were these donors selected, and what shortages remain?',
    'constrained':'Explain why HealthNexus recommends no redistribution in this scenario.',
    'provenance':'Is this live government inventory, and how should I interpret the forecast performance?'}
LEDGER=ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL=ROOT/'artifacts/phase6-slots-live-sends.json'
BASELINE=ROOT/'artifacts/phase6-slots-preservation-before.json'
GATE=ROOT/'docs/evaluation/phase6-slots-preflight.json'
LEASE=ROOT/'artifacts/gemini-verifier.lock'
ALLOWED={'backend/app/ai/frames.py','scripts/frame_fixture.py','scripts/verify_phase6_frames.py','backend/tests/test_ai_frames.py','backend/app/ai/facts.py','backend/app/ai/schemas.py','backend/app/ai/orchestrator.py',
    'scripts/verify_gemini.py','scripts/verify_phase6_completion.py','backend/tests/test_ai.py',
    'backend/tests/test_ai_narrative_contract.py','README.md','docs/gemini.md',
    'docs/phase6-report.md','docs/validation.md','docs/phase6-final-acceptance-report.md'}


def preserved():
    before=json.loads(BASELINE.read_text());allowed=set(ALLOWED)
    if JOURNAL.exists():
        saved=json.loads(JOURNAL.read_text());old=saved['historical_ledger'];n=saved['new_provider_requests']
        assert old==before['historical_ledger'] and old['used']==36 and 1<=n<=MAX_SENDS
        expected=deepcopy(old);expected['used']+=n;expected['per_model'][MODEL]+=n
        assert json.loads(LEDGER.read_text())==expected,'Historical accounting changed'
        allowed.add('artifacts/gemini-verification-budget-live.json')
    for p,sha in before['files'].items():
        if p not in allowed:assert digest(ROOT/p)==sha,'Protected file changed: '+p
    # The prior gate also freezes ignored model/history/planning/frontend assets.
    # Retain those original identities; Git's inventory omits ignored files.
    older=json.loads((ROOT/'artifacts/phase6-completion-preservation-before.json').read_text())
    inherited={p:sha for p,sha in older['files'].items() if p not in before['files']}
    for p,sha in inherited.items():assert digest(ROOT/p)==sha,'Inherited protected artifact changed: '+p
    original=subprocess.check_output(['git','show','a62f098:backend/app/ai/facts.py'],cwd=ROOT,text=True)
    current=(ROOT/'backend/app/ai/facts.py').read_text()
    def exact(s):return s[s.index('    def resolve_draft'):s.index('\ndef semantic_error')]
    assert exact(original)==exact(current),'Exact fact/numeric validation changed'
    return {'status':'PASS','dirty_start_preserved':True,'original_file_identities':len(before['files']),
        'inherited_ignored_file_identities':len(inherited),
        'exact_fact_numeric_context_validation_unchanged':True,'action_semantic_guard_unchanged':True,
        'env_ui_fallback_engines_artifacts_federation_unchanged':True,'historical_evidence_unchanged':True}


class CompletionBudget:
    def __init__(self,ledger=LEDGER,journal=JOURNAL):
        self.ledger,self.journal=Path(ledger),Path(journal)
        self.original=json.loads(self.ledger.read_text());self.saved=deepcopy(self.original)
        if self.original['used']!=36 or self.journal.exists():
            raise CopilotError('verification_authorization_used','This six-send authorization cannot be replayed.',429)
        self.used=0;self.last=None;self.terminal=False

    def preflight(self):
        if self.terminal or self.used>=MAX_SENDS:
            raise CopilotError('verification_request_ceiling','Six sends globally; no seventh send or replay.',429)
        if self.last is not None:
            delay=20-(monotonic()-self.last)
            if delay>0:sleep(delay)

    def record_send(self,model,label):
        if model!=MODEL:raise CopilotError('verification_model','Only Flash-Lite is authorized.',422)
        if self.terminal or self.used>=MAX_SENDS:
            raise CopilotError('verification_request_ceiling','Six sends globally; no seventh send or replay.',429)
        assert json.loads(self.ledger.read_text())==self.saved,'Concurrent ledger mutation'
        if not self.used:
            with self.journal.open('x',encoding='utf-8') as h:json.dump({'historical_ledger':self.original,
                'new_provider_requests':1,'maximum_new_provider_requests':6,'sends_per_case':{label:1},'timestamp':stamp()},h)
        else:
            data=json.loads(self.journal.read_text());data['new_provider_requests']=self.used+1
            data['sends_per_case'][label]=data['sends_per_case'].get(label,0)+1
            self.journal.write_text(json.dumps(data),encoding='utf-8')
        self.used+=1;self.saved['used']+=1;self.saved['per_model'][MODEL]+=1
        temp=self.ledger.with_suffix('.completion.tmp');temp.write_text(json.dumps(self.saved),encoding='utf-8');temp.replace(self.ledger)
        self.last=monotonic()

    def stop(self):
        self.terminal=True
        if self.journal.exists():
            data=json.loads(self.journal.read_text());data['terminal']=True
            self.journal.write_text(json.dumps(data),encoding='utf-8')


def identity():
    sha=hashlib.sha256()
    paths=sorted((ROOT/'backend/app').rglob('*.py'))+sorted((ROOT/'backend/tests').rglob('*.py'))+[
        Path(__file__),ROOT/'scripts/verify_gemini.py',ROOT/'scripts/frame_fixture.py',ROOT/'backend/requirements.txt']
    for p in paths:sha.update(p.relative_to(ROOT).as_posix().encode());sha.update(p.read_bytes())
    return sha.hexdigest()


def canonical_plan(plan,profile):
    actual=(plan.preview.total_deficit,plan.preview.safe_capacity,plan.impact.transferred_units,
        len(plan.transfers),plan.impact.after.target_deficit)
    expected=(41763,17745,15679,10,26084) if profile=='redistribution-ready' else (30230,0,0,0,30230)
    assert actual==expected,('Canonical plan differs',profile,actual)
    assert plan.solver.status=='OPTIMAL'
    assert plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
    assert sum(t.quantity for t in plan.transfers)==plan.impact.transferred_units
    assert all(t.donor_protected_minimum_after>=t.donor_protected_reserve for t in plan.transfers)
    assert all(v['before']==v['after'] for v in plan.impact.conservation.values())
    return {'target_before':actual[0],'safe_capacity':actual[1],'planned_accounting_items':actual[2],
        'lanes':actual[3],'unresolved':actual[4],'donor_violations':0,'new_donor_risks':0,
        'solver_status':plan.solver.status,'action_state':advisory_state(),'conservation':'PASS'}


def old_failures():
    records={'e1':{'tool':'optimize_redistribution','payload':{'action_state':advisory_state()}}};out=[]
    for text in ('optimal advisory transfers executed','executing safe transfers','Despite executing authorized transfers','Despite executing recommended transfers'):
        try:check_action_claim(text,[],records)
        except CopilotError as e:out.append({'text':text,'status':'REJECTED','code':e.code})
        else:raise AssertionError('Previous execution claim accepted')
    return out


def acceptance(response,label):
    text=' '.join(c.text for c in [response.situation,*response.key_risks,*response.recommended_actions,*response.remaining_gaps]).lower()
    if label in ('positive','followup'):
        assert response.recommended_actions and re.search(r'recommend|propos|planned',text),'Recommendation not explained'
        assert response.remaining_gaps and re.search(r'remain|unresolved|shortage|deficit',' '.join(c.text for c in response.remaining_gaps).lower()),'Remaining gap not explained'
    if label=='followup':
        assert re.search(r'protect|reserve|safety',text) and re.search(r'resource|capacity',text),'Donor protection/eligibility not explained'
    if label=='constrained':
        assert re.search(r'no|zero|cannot|insufficient',text) and re.search(r'safe|reserve|protect',text),'Zero donor conclusion missing'
    if label=='provenance':
        required={'official public inputs':r'official|public aggregate','simulated operations':r'simulat|calibrat',
            'not live inventory':r'not.{0,70}live|no.{0,70}live','forecast output':r'forecast|model.based|derived model',
            'not clinically validated':r'not.{0,50}clinically|not.{0,50}clinical|no.{0,50}clinical',
            'scenario projection':r'scenario|stress.test','advisory optimization':r'advisory|recommendation',
            'WAPE error metric':r'wape.{0,80}error|error.{0,80}wape','experimental federation':r'federat.{0,80}experiment|experiment.{0,80}federat',
            'no real connections':r'no.{0,90}(government|hospital).{0,90}connect|not.{0,90}connect'}
        missing=[k for k,v in required.items() if not re.search(v,text)]
        if missing:
            e=CopilotError('verification_provenance_distinctions','Required provenance distinctions missing.',422)
            e.acceptance_diagnostic={'missing_distinctions':missing};raise e
    return {'schema':'PASS','fact_ids':'PASS','numeric_grounding':'PASS','qualitative_grounding':'PASS',
        'context':'PASS','action_state_semantics':'PASS','solver_terminology':'PASS (unrequested status omitted)',
        'unknown_fact_ids':0,'unsupported_numbers':0,'unsupported_execution_claims':0}


def run(live=False,model=MODEL,review=None,*,mock_fault=None,output=None):
    assert not live or (mock_fault is None and output is None),'Live transport has no draft replacement or alternate evidence path'
    if live:
        assert model==MODEL and review is not None
        quota=json.loads((ROOT/'artifacts/phase6-slots-headroom.json').read_text());assert quota['confirmed_for_this_run'] is True
        gate=json.loads(GATE.read_text());assert gate['status']=='PASS' and gate['implementation_sha256']==identity()
        assert gate['new_provider_requests']==0
        budget=CompletionBudget();base=AIConfig()
        if base.error():raise CopilotError('verification_configuration','Configuration unavailable; no provider sends.')
    else:budget=None;base=AIConfig(api_key='unit-test-placeholder')
    preserved()
    config=replace(base,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1,
        thinking='medium',max_output_tokens=2400,synthesis_thinking='low',synthesis_max_output_tokens=4096)
    repo=LocalRepository();engine=ScenarioEngine();planner=OptimizationService(engine);state={}
    prior_ids=set();known_scenarios=set();known_plans=set();positive=None
    path=Path(output) if output is not None else ROOT/f'docs/evaluation/phase6-slots-{"live" if live else model+"-mock"}.json'
    report={'timestamp':stamp(),'baseline_commit':'a62f098','mode':'live' if live else 'official SDK HTTP mock',
        'model':model,'sdk_version':version('google-genai'),'prompt_version':PROMPT_VERSION,
        'semantic_contract':'grounded-semantic-slots-v2','prose_author':'HealthNexus deterministic renderer','narrative_contract':NARRATIVE_VERSION,'historical_provider_requests':36,'maximum_new_provider_requests':6,
        'new_provider_requests':0,'retries':0,'fallbacks':0,'tests':[],'status':'RUNNING','phase6_fully_live_accepted':False}
    def save():
        report['new_provider_requests']=budget.used if budget else 0
        path.write_text(json.dumps(sanitize_diagnostic(report,config.api_key),indent=2,allow_nan=False),encoding='utf-8')
    def factory(cfg):
        class Observed(GeminiTransport):
            def __init__(self,cfg):
                super().__init__(cfg)
                if not live:
                    self.client.close()
                    def handle(request):
                        sent=json.loads(request.content)
                        if mock_fault in ('429','503'):
                            code=int(mock_fault)
                            return httpx.Response(code,json={'error':{'code':code,'message':'Mock provider availability/quota failure'}})
                        if 'response_format' in sent:
                            from frame_fixture import mock_frame
                            draft=mock_frame(sent)
                            if mock_fault=='unsafe_final':next(iter(draft['claims'].values()))['text']='Resources were moved.'
                            text=json.dumps(draft)
                            result={'id':f'mock-final-{uuid4()}','status':'completed','model':model,
                                'steps':[{'type':'model_output','content':[{'type':'text','text':text}]}]}
                        else:
                            number=len(state['row']['provider_attempts']);scope={k:getattr(state['request'],k) for k in ('country_id','profile','state_id','district_id')}
                            name='run_emergency_scenario' if number==1 else 'optimize_redistribution'
                            args={**scope,**({'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,'seed':42} if number==1 else
                                {'scope':'district','scenario_id':next(iter(known_scenarios))})}
                            result={'id':f'mock-native-{uuid4()}','status':'requires_action','model':model,
                                'steps':[{'type':'function_call','name':name,'id':f'call-{number}','arguments':args}]}
                        return httpx.Response(200,json=result)
                    self.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(client_args={'transport':httpx.MockTransport(handle)}))
            def create(self,**body):
                row=state['row'];req=state['request'];label=state['label'];body=deepcopy(body)
                if 'response_format' not in body:
                    assert label=='positive';body['tools']=declarations({'run_emergency_scenario','optimize_redistribution'})
                else:assert 'tools' not in body
                assert body['model']==model and body['store'] is True
                assert body['generation_config']==config.generation('response_format' in body)
                assert not any(t['status']=='error' for t in state['service'].requests[str(req.request_id)]['tools'])
                data=body['input']
                envelopes=json.loads(data).get('server_prefetched_evidence',[]) if isinstance(data,str) else [json.loads(i['result'][0]['text']) for i in data]
                for envelope in envelopes:
                    assert 'error' not in envelope
                    for view in [envelope,*envelope.get('current_evidence_catalogue',[])]:
                        row['catalogues'][view['evidence_id']]=view
                    payload=envelope.get('result',{})
                    if payload.get('scenario_id'):known_scenarios.add(str(payload['scenario_id']))
                    if payload.get('run_id'):known_plans.add(str(payload['run_id']))
                ids={f['fact_id'] for r in row['catalogues'].values() for f in r.get('facts',[])}
                assert not ids & prior_ids,'Previous request fact IDs reused'
                if 'response_format' in body and label=='positive':
                    assert len(planner.results)==1,'Expected exactly one actual native optimization'
                    result=next(iter(planner.results.values()));row['canonical']=canonical_plan(result,req.profile)
                    assert result.preview.request.scenario_id in known_scenarios
                    # Audit-only engine objects: never appended to provider input or narrative.
                    row['authoritative_plan']=result.model_dump(mode='json')
                    row['authoritative_scenario']=engine.store.get(result.preview.request.scenario_id,'IN',req.profile).model_dump(mode='json')
                elif 'response_format' in body and label in ('followup','constrained'):
                    row['authoritative_plan']=planner.get(req.optimization_run_id,'IN',req.profile).model_dump(mode='json')
                attempt={'number':len(row['provider_attempts'])+1,'model':model,'stage':'synthesis' if 'response_format' in body else 'native',
                    'actual_http_sends':0,'http_status':None,'previous_interaction_id':body.get('previous_interaction_id'),
                    'generation_config':body['generation_config'],'store':True,'declared_tools':[t['name'] for t in body.get('tools',[])],
                    'input':body['input'],'schema':body.get('response_format',{}).get('schema')}
                row['provider_attempts'].append(attempt);started=perf_counter()
                client=self.client.interactions.sdk_configuration.client
                def on_send(request):
                    nonlocal started
                    if attempt['actual_http_sends']:raise AssertionError('SDK retry forbidden')
                    sent=json.loads(request.content);assert request.method=='POST' and sent['model']==model
                    if live:budget.record_send(model,label)
                    attempt['actual_http_sends']+=1;started=perf_counter();save()
                def on_response(response):attempt['http_status']=response.status_code
                client.event_hooks.setdefault('request',[]).append(on_send);client.event_hooks.setdefault('response',[]).append(on_response)
                if live:self.before_request=budget.preflight
                try:
                    result=super().create(**body)
                    attempt.update(provider_status=result.get('status'),interaction_id=result.get('id'),usage=result.get('usage',{}))
                    assert not result.get('model') or result['model']==model,'Provider model mismatch'
                    assert attempt['http_status']==200 and attempt['actual_http_sends']==1
                    calls=[s for s in result.get('steps',[]) if s.get('type')=='function_call']
                    attempt['native_calls']=native_trace(calls)
                    if 'response_format' in body:
                        attempt['raw_provider_draft']=sanitize_diagnostic(result.get('output_text',''),cfg.api_key)
                        attempt['complete_json']=False
                        try:json.loads(result.get('output_text',''));attempt['complete_json']=True
                        except (ValueError,TypeError):pass
                        attempt['raw_provider_frame']=attempt['raw_provider_draft']
                        assert not calls and result.get('status')=='completed' and result.get('id'),'Stored synthesis incomplete'
                    else:
                        expected='run_emergency_scenario' if attempt['number']==1 else 'optimize_redistribution'
                        assert len(calls)==1 and calls[0]['name']==expected and result.get('status')=='requires_action'
                        attempt['native_validation']=check_calls(body,result,req,repo,engine,planner,known_scenarios,known_plans)
                        args=attempt['native_validation'][0]['validated_arguments']
                        if expected=='run_emergency_scenario':
                            assert (args['scenario_type'],args['severity'],args['duration'],args['seed'])==('DENGUE_SURGE','severe',14,42)
                        else:assert args['scope']=='district' and args['scenario_id'] in known_scenarios
                    return result
                except CopilotError as e:
                    attempt.update(error_code=e.code,provider_diagnostic=sanitize_diagnostic(getattr(e,'diagnostic',{}),cfg.api_key));raise
                finally:
                    attempt['provider_seconds']=perf_counter()-started
                    client.event_hooks['request'].remove(on_send);client.event_hooks['response'].remove(on_response);save()
        return Observed(cfg)
    service=CopilotService(engine,planner,config,transport_factory=factory);state['service']=service
    try:
        for label in LABELS:
            req=CopilotRequest(country_id='IN',profile='constrained' if label=='constrained' else 'redistribution-ready',
                state_id='MH',district_id='MH-PUNE',message=MESSAGES[label],allow_planning=label=='positive',request_id=uuid4())
            row={'label':label,'profile':req.profile,'status':'RUNNING','provider_attempts':[],'catalogues':{},'local_factual_review':'PENDING'}
            report['tests'].append(row);state.update(row=row,request=req,label=label)
            before=repo.profile_snapshot('IN',req.profile).model_dump_json()
            if label=='followup':
                req.conversation_id=positive.conversation_id;req.scenario_id=positive.scenario_id;req.optimization_run_id=positive.optimization_run_id
                row['expected_previous_interaction_id']=positive.metadata['interaction_id']
                row['fresh_local_read']='get_optimization_result (production server-prefetch before send)'
            if label=='constrained':
                sid,rid=fixture(service,repo,req.profile);req.scenario_id=sid;req.optimization_run_id=rid
                row['local_setup_tools']=['run_emergency_scenario','optimize_redistribution']
                row['canonical']=canonical_plan(planner.get(rid,'IN',req.profile),req.profile)
            try:
                response=service.run(repo,req)
                row['response']=response.model_dump(mode='json');row['server_audit']=deepcopy(service.audit[-1])
                row['server_metadata_distinct_from_raw_provider_narrative']=True
                row['provider_output']='semantic frame / selected evidence';row['server_output']='deterministically rendered prose'
                row['semantic_frame']=json.loads(row['provider_attempts'][-1]['raw_provider_draft'])
                row['resolved_evidence']=response.model_dump(mode='json')['evidence']
                validate_response(service,repo,response,label,before,require_all_plan_metrics=False)
                row.update(acceptance(response,label));row.update(claim_kind_compatibility='PASS',renderer='PASS',public_response_schema='PASS');row['status']='PASS'
                assert repo.profile_snapshot('IN',req.profile).model_dump_json()==before
                row['baseline_immutable']=True
                if label=='positive':
                    assert len(row['provider_attempts'])==3
                    assert [t.tool for t in response.tools_used]==['run_emergency_scenario','optimize_redistribution']
                    positive=response;row['scenario_id']=response.scenario_id;row['optimization_id']=response.optimization_run_id
                    row['canonical']=canonical_plan(planner.get(response.optimization_run_id,'IN',req.profile),req.profile)
                else:
                    assert len(row['provider_attempts'])==1 and all(not a['declared_tools'] for a in row['provider_attempts'])
                    if label=='followup':
                        assert row['provider_attempts'][0]['previous_interaction_id']==row['expected_previous_interaction_id']
                        assert response.optimization_run_id==positive.optimization_run_id
                        assert response.conversation_id==positive.conversation_id
                        assert [t.tool for t in response.tools_used]==['get_optimization_result']
                        row['conversation_continuity']='PASS'
                        row['canonical']=canonical_plan(planner.get(response.optimization_run_id,'IN',req.profile),req.profile)
                    else:assert row['provider_attempts'][0]['previous_interaction_id'] is None
                prior_ids.update(f['fact_id'] for r in row['catalogues'].values() for f in r.get('facts',[]))
                save()
                if live:
                    verdict=review(row);row['local_factual_review']='PASS' if verdict.strip()=='PASS' else 'FAIL'
                    if verdict.strip()!='PASS':
                        row['local_review_reason']=sanitize_diagnostic(verdict[:500],config.api_key)
                        raise CopilotError('verification_manual_grounding','Local factual review rejected the unchanged draft.',422)
                else:row['local_factual_review']='PASS (scripted fixture; not live evidence)'
            except (CopilotError,AssertionError,ValueError) as e:
                row.update(status='FAIL',error_code=getattr(e,'code','verification_failure'),failure=sanitize_diagnostic(str(e),config.api_key))
                for key in ('citation_diagnostic','grounding_diagnostic','action_state_diagnostic','narrative_diagnostic','acceptance_diagnostic','frame_diagnostic'):
                    if hasattr(e,key):row[key]=sanitize_diagnostic(getattr(e,key),config.api_key)
                row['server_audit']=deepcopy(service.audit[-1]) if service.audit else None
                save();break
            save();print(label,'PASS',flush=True)
        report['status']='PASS' if len(report['tests'])==4 and all(r['status']=='PASS' for r in report['tests']) else 'STOPPED_AFTER_FAILURE'
        report['new_provider_requests']=budget.used if budget else 0
        report['mock_http_sends']=sum(a['actual_http_sends'] for r in report['tests'] for a in r['provider_attempts']) if not live else 0
        if report['status']=='PASS':assert (budget.used if budget else report['mock_http_sends'])==6
        report['preservation']=preserved();report['security']=secret_scan()
        report['final_regression_required']=live and report['status']=='PASS'
        report['remaining_cases_not_attempted']=report['status']!='PASS'
        save();return report
    finally:
        if budget:budget.stop()
        save()


def preflight():
    assert not JOURNAL.exists() and json.loads(LEDGER.read_text())['used']==36
    suites=ET.parse(ROOT/'artifacts/phase6-slots-preflight-pytest.xml').getroot().findall('testsuite')
    assert suites and all(int(s.get(k,'0'))==0 for s in suites for k in ('failures','errors','skipped'))
    count=sum(int(s.get('tests','0')) for s in suites);assert count>=587
    for m in (MODEL,'gemini-3.6-flash'):
        mock=json.loads((ROOT/f'docs/evaluation/phase6-slots-{m}-mock.json').read_text())
        assert mock['status']=='PASS' and mock['new_provider_requests']==0 and mock['mock_http_sends']==6
    canonical=json.loads((ROOT/'docs/evaluation/phase6-slots-canonical.json').read_text())
    assert canonical['status']=='PASS' and canonical['live_gemini_requests']==0
    smoke=json.loads((ROOT/'docs/evaluation/phase6-facts-live.json').read_text())
    assert smoke['status']=='PASS' and len(smoke['attempts'])==2
    assert all(a['status']=='PASS' for a in smoke['attempts'])
    for cmd in ([sys.executable,'-m','compileall','-q','backend','scripts'],[sys.executable,'-m','pip','check']):
        subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True,text=True)
    gate={'timestamp':stamp(),'status':'PASS','backend_tests':count,'backend_seconds':sum(float(s.get('time','0')) for s in suites),
        'new_provider_requests':0,'starting_ledger':36,'maximum_sends':6,'model':MODEL,'provider_headroom':json.loads((ROOT/'artifacts/phase6-slots-headroom.json').read_text()),'mock_models':[MODEL,'gemini-3.6-flash'],
        'shared_mock_cases':list(LABELS),'old_failure_reproduction':old_failures(),'compile':'PASS','dependencies':'PASS',
        'canonical_and_federation':'PASS','previous_smoke_2_of_2_preserved':True,'previous_smoke_sha256':digest(ROOT/'docs/evaluation/phase6-facts-live.json'),
        'preservation':preserved(),'security':secret_scan(),'implementation_sha256':identity(),
        'frontend':'unchanged; preserved prior successful strict TypeScript/Angular production build',
        'provider_quota':'not inferred from local ledger; any provider quota/rate error stops the run'}
    GATE.write_text(json.dumps(gate,indent=2),encoding='utf-8');return gate


def main():
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--mock',action='store_true');mode.add_argument('--preflight',action='store_true');mode.add_argument('--live',action='store_true')
    args=p.parse_args()
    if args.preflight:
        result=preflight();print(json.dumps({'status':result['status'],'backend_tests':result['backend_tests'],'new_provider_requests':0}));return 0
    if args.live:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
        with LEASE.open('x',encoding='utf-8') as h:h.write('Phase 6 final six-send acceptance')
        try:reports=[run(True,review=lambda row:input('PAUSED_FOR_LOCAL_FACTUAL_REVIEW '+row['label']+' (PASS or STOP): '))]
        finally:LEASE.unlink()
    else:reports=[run(False,m) for m in (MODEL,'gemini-3.6-flash')]
    print(json.dumps({'status':[r['status'] for r in reports],'new_provider_requests':sum(r['new_provider_requests'] for r in reports)}))
    return 0 if all(r['status']=='PASS' for r in reports) else 1


if __name__=='__main__':raise SystemExit(main())
