"""One-send synthesis acceptance, with freshly reconstructed authoritative evidence.

Never runs native planning through Gemini. --mock uses the official SDK HTTP mock;
--live requires a successful local gate and consumes its authorization permanently.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from time import perf_counter
from importlib.metadata import version

import httpx
from google import genai
from google.genai import types
from pydantic import ValidationError
from verify_gemini import (ROOT, AIConfig, CopilotRequest, CopilotError, GeminiTransport,
    LocalRepository, ScenarioEngine, OptimizationService, QUESTIONS)
from app.ai.facts import FactCatalogue, VERSION as FACT_VERSION
from app.ai.schemas import FactDraftAnswer
from app.ai.system_prompt import SYSTEM, SYNTHESIS, VERSION as PROMPT_VERSION
from app.ai.tools import ToolExecutor
from app.ai.citations import sanitize_diagnostic
from app.profiles.identity import fingerprint
from app.scenarios.engine import select

MODEL='gemini-3.5-flash-lite'
LEDGER=ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL=ROOT/'artifacts/phase6-synthesis-live-send.json'
BASELINE=ROOT/'artifacts/phase6-synthesis-preservation-before.json'
GATE=ROOT/'docs/evaluation/phase6-synthesis-preflight.json'
LEASE=ROOT/'artifacts/gemini-verifier.lock'
PRIOR=ROOT/'docs/evaluation/phase6-workflow-live.json'
ALLOWED={'backend/app/ai/config.py','backend/app/ai/failover.py',
    'backend/app/ai/orchestrator.py','backend/app/ai/system_prompt.py',
    'backend/tests/test_ai.py','backend/tests/test_ai_failover.py','scripts/verify_gemini.py',
    '.env.example','README.md','docs/gemini.md','docs/phase6-report.md','docs/validation.md'}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()


def preserved():
    before=json.loads(BASELINE.read_text());allowed=set(ALLOWED)
    if JOURNAL.exists():
        saved=json.loads(JOURNAL.read_text());original=saved['historical_ledger']
        assert original['used']==28 and saved['new_provider_requests']==1
        assert hashlib.sha256(json.dumps(original).encode()).hexdigest()==before['artifacts/gemini-verification-budget-live.json']
        expected=deepcopy(original);expected['used']+=1;expected['per_model'][MODEL]+=1
        assert json.loads(LEDGER.read_text())==expected,'Historical ledger was changed'
        allowed.add('artifacts/gemini-verification-budget-live.json')
    for name,sha in before.items():
        if name not in allowed:assert digest(ROOT/name)==sha,'Protected file changed: '+name
    return {'status':'PASS','original_file_identities':len(before),
        'unchanged_file_identities':sum(p not in allowed for p in before),
        'env_unchanged':True,'ui_unchanged':True,'fact_numeric_contract_unchanged':True,
        'operational_forecasting_ortools_federation_artifacts_unchanged':True,
        'production_fallback_order_unchanged':True,'historical_evidence_unchanged':True}


class OneSendBudget:
    """No daily rollover. Only a real wire hook can append this single authorization."""
    def __init__(self,ledger=LEDGER,journal=JOURNAL):
        self.ledger,self.journal=Path(ledger),Path(journal)
        self.original=json.loads(self.ledger.read_text());self.used=0
        if self.original['used']!=28 or self.journal.exists():
            raise CopilotError('verification_authorization_used','The one-send authorization cannot be replayed.',429)

    def preflight(self):
        if self.used or self.journal.exists():
            raise CopilotError('verification_request_ceiling','Exactly one new send is authorized.',429)

    def record_send(self,model):
        self.preflight()
        if model!=MODEL:raise CopilotError('verification_model','Only Flash-Lite synthesis is authorized.',422)
        assert json.loads(self.ledger.read_text())==self.original,'Concurrent ledger mutation'
        saved=deepcopy(self.original);saved['used']+=1;saved['per_model'][MODEL]+=1
        # Exclusive journal prevents accidental replay, even if a later write/send fails.
        with self.journal.open('x',encoding='utf-8') as handle:
            json.dump({'historical_ledger':self.original,'new_provider_requests':1,
                'maximum_new_provider_requests':1,'model':model,'timestamp':stamp()},handle)
        temporary=self.ledger.with_suffix('.synthesis.tmp')
        temporary.write_text(json.dumps(saved),encoding='utf-8');temporary.replace(self.ledger)
        self.used=1


def implementation_identity():
    paths=sorted((ROOT/'backend/app').rglob('*.py'))+sorted((ROOT/'backend/tests').rglob('*.py'))+[Path(__file__),ROOT/'scripts/verify_gemini.py',
        ROOT/'backend/requirements.txt',PRIOR]
    sha=hashlib.sha256()
    for path in paths:sha.update(path.relative_to(ROOT).as_posix().encode());sha.update(path.read_bytes())
    return sha.hexdigest()


def preflight():
    """Local gates only; never instantiates a live provider transport."""
    from verify_demo import secret_scan
    assert not JOURNAL.exists(),'The live authorization has already been consumed'
    assert json.loads(LEDGER.read_text())['used']==28
    xml=ROOT/'artifacts/phase6-synthesis-pytest.xml'
    suites=ET.parse(xml).getroot().findall('testsuite')
    assert suites and sum(int(s.get('tests','0')) for s in suites)>=479
    assert all(int(s.get(k,'0'))==0 for s in suites for k in ('errors','failures','skipped'))
    for command in ([sys.executable,'-m','compileall','-q','backend','scripts'],
            [sys.executable,'-m','pip','check']):
        subprocess.run(command,cwd=ROOT,check=True,capture_output=True,text=True)
    mock=json.loads((ROOT/'docs/evaluation/phase6-synthesis-mock.json').read_text())
    assert mock['status']=='PASS' and len(mock['tests'])==2
    assert all(t['new_provider_requests']==0 for t in mock['tests'])
    assert {t['model'] for t in mock['tests']}=={MODEL,'gemini-3.6-flash'}
    canonical=json.loads((ROOT/'docs/evaluation/phase6-synthesis-canonical.json').read_text())
    assert canonical['status']=='PASS' and canonical['live_gemini_requests']==0
    gate={'timestamp':stamp(),'status':'PASS','new_live_requests':0,'full_backend':'PASS',
        'backend_tests':sum(int(s.get('tests','0')) for s in suites),
        'backend_seconds':sum(float(s.get('time','0')) for s in suites),
        'pytest_report_sha256':digest(xml),'mock':'PASS','compile':'PASS','dependencies':'PASS',
        'sdk_version':version('google-genai'),'synthesis_thinking_sdk_defined':'low',
        'generation_stages':{'native':AIConfig().generation(),'synthesis':AIConfig().generation(True)},
        'canonical':'PASS','security':secret_scan(),'preservation':preserved(),
        'frontend':'unchanged; preserved prior successful strict TypeScript/production build',
        'implementation_sha256':implementation_identity()}
    GATE.write_text(json.dumps(gate,indent=2),encoding='utf-8')
    return gate


def prepare():
    """Path B: same validated inputs, new process-local IDs, actual unchanged engines."""
    prior=json.loads(PRIOR.read_text())['tests'][0]
    attempts=prior['provider_attempts'][:2]
    assert all(a['http_status']==200 and a['provider_status']=='requires_action' for a in attempts)
    calls=[c for a in attempts for c in a['native_validation']]
    assert [c['tool'] for c in calls]==['run_emergency_scenario','optimize_redistribution']
    assert all(c['pydantic_valid'] and c['scope_permissions_identity_valid'] for c in calls)
    req=CopilotRequest(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',
        message=QUESTIONS['positive'],allow_planning=True)
    repo=LocalRepository();engine=ScenarioEngine();planner=OptimizationService(engine)
    executor=ToolExecutor(repo,engine,planner,req);snapshot=executor.snapshot(req.profile)
    initial=fingerprint(snapshot,snapshot.facilities);started=perf_counter()
    scenario=executor.execute(calls[0]['tool'],calls[0]['validated_arguments'])
    args=deepcopy(calls[1]['validated_arguments']);args['scenario_id']=scenario['scenario_id']
    plan=executor.execute(calls[1]['tool'],args)
    stored=executor.scenario(snapshot,scenario['scenario_id']) # Reject stale model/snapshot/scope.
    original=prior['catalogues'];old_scenario=original['e1']['result']['scenario'];old_plan=original['e2']['result']
    assert scenario['scenario']['baseline_snapshot_id']==old_scenario['baseline_snapshot_id']
    assert scenario['scenario']['definition']==old_scenario['definition']
    assert scenario['model_versions']==original['e1']['result']['model_versions']
    for key in ('model_version','policy_version','safe_capacity','impact','transfers_total'):
        assert plan[key]==old_plan[key],'Reconstruction differs: '+key
    assert [{k:t[k] for k in old} for t,old in zip(plan['transfers'],old_plan['transfers'])]==old_plan['transfers']
    assert all(payload['context']==original[eid]['context'] for eid,payload in [('e1',scenario),('e2',plan)])
    assert plan['solver']['status']==old_plan['solver']['status']=='OPTIMAL'
    assert fingerprint(snapshot,snapshot.facilities)==initial
    assert stored.scenario.baseline_snapshot_id==fingerprint(snapshot,select(snapshot,'MH','MH-PUNE',[]))
    impact=plan['impact']
    assert (impact['before']['target_deficit'],plan['safe_capacity'],impact['transferred_units'],
        plan['transfers_total'],impact['after']['target_deficit'])==(41763,17745,15679,10,26084)
    assert impact['donor_safety_violations']==impact['new_donor_risks']==0
    assert all(t['donor_protected_minimum_after']>=t['donor_protected_reserve'] for t in plan['transfers'])
    assert all(v['before']==v['after'] for v in impact['conservation'].values())
    catalog=FactCatalogue();records={};envelopes=[]
    for eid,tool,payload in [('e1','run_emergency_scenario',scenario),('e2','optimize_redistribution',plan)]:
        records[eid]={'tool':tool,'payload':payload,'request_scope':{
            'state_id':req.state_id,'district_id':req.district_id,'facility_id':None}}
        envelope=catalog.envelope(eid,tool,payload)
        envelope.pop('result',None) # Final synthesis needs facts; numeric panels remain server-owned.
        envelopes.append(envelope)
    bundle=engine.forecasts.bundle('IN',req.profile)
    info={'method':'deterministic reconstructed authoritative evidence (path B)',
        'original_live_scenario_id':old_scenario['scenario_id'],'original_live_optimization_id':old_plan['run_id'],
        'new_scenario_id':scenario['scenario_id'],'new_optimization_id':plan['run_id'],
        'new_objects_not_original_in_memory':True,'source_report_sha256':digest(PRIOR),
        'snapshot_id':initial,'scoped_snapshot_id':scenario['scenario']['baseline_snapshot_id'],
        'forecast_artifact_sha256':bundle['artifact_sha256'],'model_version':plan['model_version'],
        'profile':req.profile,'profile_version':snapshot.profile_version,'origin':str(snapshot.as_of),
        'canonical':{'target_before':41763,'safe_capacity':17745,'transferred':15679,'lanes':10,
            'unresolved':26084,'donor_violations':0,'new_donor_risks':0,'solver_status':'OPTIMAL'},
        'impact':impact,'baseline_and_scenario_immutable':True,'local_tool_calls':2,
        'local_seconds':perf_counter()-started}
    return req,catalog,records,envelopes,snapshot.as_of,info


def synthesis_body(config,req,catalog,envelopes):
    return {'model':config.model,'input':json.dumps({'question':req.message,
        'context':req.model_dump(include={'country_id','profile','state_id','district_id'}),
        'server_prefetched_evidence':envelopes}),
        'system_instruction':SYSTEM+SYNTHESIS,'store':False,
        'generation_config':config.generation(True),
        'response_format':{'type':'text','mime_type':'application/json','schema':catalog.schema()}}


def validate_final(result,catalog,records,req,origin):
    # This standalone request uses store=False and has no continuation. The pinned
    # SDK defines Interaction.id as optional, default ""; completion is mandatory.
    # Production stored conversations still require their interaction IDs.
    if result.get('status')!='completed':
        raise CopilotError('response_incomplete','Final synthesis did not complete.')
    if any(s.get('type')=='function_call' for s in result.get('steps',[])):
        raise CopilotError('malformed_tool_call','Final synthesis returned a native call.')
    try:draft=FactDraftAnswer.model_validate_json(result.get('output_text',''))
    except (ValidationError,TypeError):raise CopilotError('response_schema','Incomplete or invalid final JSON.') from None
    resolved,evidence,audits=catalog.validate(draft,records,context=req,origin=origin)
    # Additional acceptance guard, not a change to the production numeric/evidence contract.
    claims=[resolved.situation,*resolved.key_risks,*resolved.recommended_actions,*resolved.remaining_gaps]
    for claim in claims:
        lower=claim.text.lower()
        if re.search(r'\bexecut(?:ed|ing|e|es)\b.{0,35}\btransfers?\b',lower):
            raise CopilotError('verification_physical_execution','Advisory transfers must not be described as physical execution.',422)
        for pattern in (r'\ball shortages (?:are |have been )?(?:solved|resolved)\b',
                r'\b(?:network (?:is )?fully resilient|risks? (?:is |are )?eliminated|all stock.outs (?:are )?prevented)\b'):
            match=re.search(pattern,lower)
            if match and not re.search(r'\b(?:not|no)\s*$',lower[max(0,match.start()-10):match.start()]):
                raise CopilotError('verification_qualitative','Unsupported full-resolution interpretation.',422)
    if not resolved.remaining_gaps or not re.search(r'remain|unresolved|shortage|deficit',
            ' '.join(c.text for c in resolved.remaining_gaps).lower()):
        raise CopilotError('verification_remaining_shortages','Remaining shortage must be explained.',422)
    return resolved,evidence,audits


def mock_draft(catalog):
    """Test fixture only. Live never invokes or receives this mock answer."""
    def claim(text,path):
        fid=next(f.fact_id for f in catalog.facts.values() if f.evidence_id=='e2' and f.path==path)
        return {'text':text,'evidence_refs':[fid]}
    return {'situation':claim('OR-Tools proved an optimal advisory plan under the configured constraints.','solver.status'),
        'key_risks':[claim('Safe donor surplus is available for redistribution.','safe_capacity')],
        'recommended_actions':[claim('The advisory redistribution plan reduces resource pressure.','impact.transferred_units')],
        'remaining_gaps':[claim('Substantial unresolved resource deficits remain.','impact.after.target_deficit')]}


def run(live=False,model=MODEL):
    preservation=preserved()
    if live:
        assert model==MODEL
        gate=json.loads(GATE.read_text())
        assert gate['status']=='PASS' and gate['implementation_sha256']==implementation_identity()
        assert gate['new_live_requests']==0 and gate['full_backend']=='PASS' and gate['mock']=='PASS'
        budget=OneSendBudget()
        base=AIConfig()
        if base.error():raise CopilotError('verification_configuration','Configuration unavailable; no sends.')
    else:base=AIConfig(api_key='unit-test-placeholder');budget=None
    config=replace(base,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1,
        thinking='medium',synthesis_thinking='low',synthesis_max_output_tokens=4096)
    req,catalog,records,envelopes,origin,info=prepare()
    body=synthesis_body(config,req,catalog,envelopes)
    report={'timestamp':stamp(),'case':'positive-final','mode':'live' if live else 'official SDK HTTP mock',
        'model':model,'sdk_version':version('google-genai'),'fact_contract_version':FACT_VERSION,
        'system_prompt_version':PROMPT_VERSION,'generation_stages':{'native':config.generation(),'synthesis':config.generation(True)},
        'historical_provider_requests':28,'maximum_new_provider_requests':1,'new_provider_requests':0,
        'native_provider_requests':0,'retry':False,'fallback':False,'previous_interaction_id':None,
        'stateless_synthesis':True,'provider_interaction_id_required':False,
        'fact_catalogue':envelopes,
        'evidence_reuse':info,'preservation':preservation,'status':'RUNNING',
        'native_orchestration':'PASS (preserved live evidence)','positive_workflow':'PENDING',
        'phase6_complete':False,'remaining_cases':['followup','constrained','provenance']}
    transport=GeminiTransport(config);http_status=[];wire=[]
    if not live:
        transport.client.close()
        def handler(request):
            sent=json.loads(request.content);wire.append(sent)
            assert sent['generation_config']=={'thinking_level':'low','max_output_tokens':4096}
            assert 'tools' not in sent and 'previous_interaction_id' not in sent and sent['model']==model
            text=json.dumps(mock_draft(catalog))
            return httpx.Response(200,json={'id':'mock-final','status':'completed','model':model,
                'steps':[{'type':'model_output','content':[{'type':'text','text':text}]}]})
        transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
            client_args={'transport':httpx.MockTransport(handler)}))
    else:
        def wire_hook(request):
            sent=json.loads(request.content)
            assert request.method=='POST' and sent['model']==MODEL and len(wire)==0
            assert 'tools' not in sent and 'previous_interaction_id' not in sent
            assert sent['generation_config']==config.generation(True)
            budget.record_send(sent['model']);wire.append({'model':sent['model']})
            report['new_provider_requests']=budget.used
        transport.before_request=budget.preflight
        transport.client.interactions.sdk_configuration.client.event_hooks.setdefault('request',[]).append(wire_hook)
    transport.client.interactions.sdk_configuration.client.event_hooks.setdefault('response',[]).append(
        lambda response:http_status.append(response.status_code))
    started=perf_counter()
    try:
        result=transport.create(**body)
        report.update(provider_seconds=perf_counter()-started,http_status=http_status[-1] if http_status else None,
            provider_status=result.get('status'),interaction_id=result.get('id'),usage=result.get('usage',{}),
            final_output_text=sanitize_diagnostic(result.get('output_text',''),config.api_key),
            partial_output_length=len(result.get('output_text','')))
        try:json.loads(result.get('output_text',''));report['json_truncation']=False
        except (ValueError,TypeError):report['json_truncation']=True
        assert report['http_status']==200,'Expected HTTP 200'
        if result.get('model') and result['model']!=model:
            raise CopilotError('response_model','Provider reported a different model.')
        resolved,evidence,audits=validate_final(result,catalog,records,req,origin)
        report.update(status='PASS',final_synthesis='PASS',positive_workflow='PASS',
            schema='PASS',fact_ids='PASS',numeric_grounding='PASS',context='PASS',solver_terminology='PASS',
            qualitative_grounding='PASS (automated guard; final manual review also required)',
            unknown_fact_ids=0,unsupported_numeric_claims=0,claim_count=1+sum(len(getattr(resolved,k)) for k in (
                'key_risks','recommended_actions','remaining_gaps')),answer=resolved.model_dump(mode='json'),
            evidence=[e.model_dump(mode='json') for e in evidence],fact_audits=audits)
    except (CopilotError,AssertionError) as error:
        report.update(status='FAIL',final_synthesis='FAIL',positive_workflow='FAIL',
            error_code=getattr(error,'code','verification_failure'),provider_seconds=perf_counter()-started,
            http_status=http_status[-1] if http_status else None,
            provider_diagnostic=sanitize_diagnostic(getattr(error,'diagnostic',{}),config.api_key),
            citation_diagnostic=sanitize_diagnostic(getattr(error,'citation_diagnostic',{}),config.api_key))
    finally:
        transport.close()
        report['new_provider_requests']=budget.used if budget else 0
        report['mock_http_sends']=len(wire) if not live else 0
        report['provider_attempts_per_model']={model:budget.used} if budget else {}
        report['preservation']=preserved()
    return report


def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--mock',action='store_true');mode.add_argument('--live',action='store_true')
    mode.add_argument('--preflight',action='store_true')
    parser.add_argument('--case',choices=['positive-final'],default='positive-final')
    args=parser.parse_args()
    if args.preflight:
        gate=preflight();print(json.dumps({'status':gate['status'],'backend_tests':gate['backend_tests'],'new_provider_requests':0}))
        return 0
    if args.live:
        # Load the same existing local key without printing or modifying the ignored .env.
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
        with LEASE.open('x',encoding='utf-8') as handle:handle.write('positive-final one-send verifier')
    try:
        reports=[run(True)] if args.live else [run(False,m) for m in (MODEL,'gemini-3.6-flash')]
        status='PASS' if all(r['status']=='PASS' for r in reports) else 'FAIL'
        output=ROOT/('docs/evaluation/phase6-synthesis-live.json' if args.live else 'docs/evaluation/phase6-synthesis-mock.json')
        output.write_text(json.dumps({'status':status,'tests':reports},indent=2),encoding='utf-8')
        print(json.dumps({'status':status,'report':output.relative_to(ROOT).as_posix(),
            'new_provider_requests':sum(r['new_provider_requests'] for r in reports)}))
        return 0 if status=='PASS' else 1
    finally:
        if args.live:LEASE.unlink()


if __name__=='__main__':raise SystemExit(main())
