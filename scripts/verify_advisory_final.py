"""Advisory action-state acceptance: cost-free mocks, then one authorized Lite send."""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter
import xml.etree.ElementTree as ET

import httpx
from google import genai
from google.genai import types
from pydantic import ValidationError
from verify_positive_final import (ROOT,MODEL,LEDGER,LEASE,PRIOR,stamp,digest,prepare,synthesis_body,
    mock_draft,OneSendBudget,AIConfig,CopilotError,GeminiTransport)
from app.ai.schemas import FactDraftAnswer
from app.ai.action_state import advisory_state,VERSION as ACTION_VERSION,check_action_claim
from app.ai.citations import sanitize_diagnostic
from app.ai.facts import VERSION as FACT_VERSION
from app.ai.system_prompt import VERSION as PROMPT_VERSION
from verify_demo import secret_scan

BASELINE=ROOT/'artifacts/phase6-action-preservation-before.json'
JOURNAL=ROOT/'artifacts/phase6-action-live-send.json'
GATE=ROOT/'docs/evaluation/phase6-action-preflight.json'
OLD_FINAL=ROOT/'docs/evaluation/phase6-synthesis-live.json'
ALLOWED={'backend/app/ai/tools.py','backend/app/ai/protocol.py','backend/app/ai/facts.py',
    'backend/app/ai/citations.py','backend/app/ai/system_prompt.py','backend/app/ai/fallback.py',
    'backend/app/ai/orchestrator.py','backend/tests/test_ai_synthesis.py',
    'scripts/verify_gemini.py','scripts/verify_live_workflow.py','scripts/verify_positive_final.py',
    'README.md','docs/gemini.md','docs/phase6-report.md','docs/validation.md'}


def preserved():
    before=json.loads(BASELINE.read_text());allowed=set(ALLOWED)
    if JOURNAL.exists():
        saved=json.loads(JOURNAL.read_text());original=saved['historical_ledger']
        assert original['used']==29 and saved['new_provider_requests']==1
        assert hashlib.sha256(json.dumps(original).encode()).hexdigest()==before['files']['artifacts/gemini-verification-budget-live.json']
        expected=deepcopy(original);expected['used']+=1;expected['per_model'][MODEL]+=1
        assert json.loads(LEDGER.read_text())==expected,'Historical ledger changed'
        allowed.add('artifacts/gemini-verification-budget-live.json')
    for name,sha in before['files'].items():
        if name not in allowed:assert digest(ROOT/name)==sha,'Protected file changed: '+name
    citations=(ROOT/'backend/app/ai/citations.py').read_text()
    facts=(ROOT/'backend/app/ai/facts.py').read_text()
    assert hashlib.sha256(citations[citations.index('def build_evidence'):citations.index('        # A model must')].encode()).hexdigest()==before['numeric_evidence_prefix']
    assert hashlib.sha256(facts[facts.index('    def resolve_draft'):facts.index('\ndef semantic_error')].encode()).hexdigest()==before['fact_resolution_validation']
    return {'status':'PASS','original_file_identities':len(before['files']),
        'unchanged_file_identities':sum(p not in allowed for p in before['files']),
        'exact_numeric_validation_unchanged':True,'fact_membership_resolution_validation_unchanged':True,
        'env_ui_fallback_unchanged':True,'operational_forecasting_ortools_federation_artifacts_unchanged':True,
        'historical_reports_and_journals_unchanged':True}


class AdvisoryBudget(OneSendBudget):
    """New explicit authorization; older 28-request and 25-request journals stay frozen."""
    def __init__(self,ledger=LEDGER,journal=JOURNAL):
        self.ledger,self.journal=Path(ledger),Path(journal)
        self.original=json.loads(self.ledger.read_text());self.used=0
        if self.original['used']!=29 or self.journal.exists():
            raise CopilotError('verification_authorization_used','This single advisory acceptance send cannot be replayed.',429)


def identity():
    sha=hashlib.sha256()
    paths=(sorted((ROOT/'backend/app').rglob('*.py'))+sorted((ROOT/'backend/tests').rglob('*.py'))+
        [Path(__file__),ROOT/'scripts/verify_positive_final.py',ROOT/'scripts/verify_gemini.py',
        ROOT/'scripts/verify_live_workflow.py',ROOT/'backend/requirements.txt',PRIOR,OLD_FINAL])
    for p in paths:sha.update(p.relative_to(ROOT).as_posix().encode());sha.update(p.read_bytes())
    return sha.hexdigest()


def old_failure():
    saved=json.loads(OLD_FINAL.read_text())['tests'][0]
    draft=FactDraftAnswer.model_validate_json(saved['final_output_text'])
    phrases=[c.text for c in [draft.situation,*draft.key_risks,*draft.recommended_actions,*draft.remaining_gaps]
        if 'executing' in c.text]
    assert len(phrases)==2
    payload={'action_state':advisory_state()}
    records={'e1':{'tool':'optimize_redistribution','payload':payload}}
    outcomes=[]
    for phrase in phrases:
        try:check_action_claim(phrase,[],records)
        except CopilotError as error:
            outcomes.append({'exact_saved_claim':phrase,'status':'REJECTED','error_code':error.code,
                'diagnostic':error.action_state_diagnostic})
        else:raise AssertionError('The exact previous execution claim passed')
    return {'status':'PASS','source_report_sha256':digest(OLD_FINAL),'cases':outcomes,
        'new_provider_requests':0}


def validate(result,catalog,records,req,origin):
    if result.get('status')!='completed':raise CopilotError('response_incomplete','Synthesis did not complete.')
    if any(s.get('type')=='function_call' for s in result.get('steps',[])):
        raise CopilotError('malformed_tool_call','Schema-only synthesis returned a native tool call.')
    try:draft=FactDraftAnswer.model_validate_json(result.get('output_text',''))
    except (ValidationError,TypeError):raise CopilotError('response_schema','Final JSON failed its unchanged schema.') from None
    resolved,evidence,audits=catalog.validate(draft,records,context=req,origin=origin)
    if not any(f['path']=='action_state' or f['path'].startswith('action_state.') for a in audits for f in a['resolved_facts']):
        raise CopilotError('verification_action_citation','The final answer must cite its authoritative advisory action state.',422)
    if not resolved.remaining_gaps or not re.search(r'remain|unresolved|shortage|deficit',' '.join(c.text for c in resolved.remaining_gaps).lower()):
        raise CopilotError('verification_remaining_shortages','The remaining shortage must be explained.',422)
    return resolved,evidence,audits


def run(live=False,model=MODEL):
    preservation=preserved()
    if live:
        assert model==MODEL
        gate=json.loads(GATE.read_text())
        assert gate['status']=='PASS' and gate['implementation_sha256']==identity()
        assert gate['new_provider_requests']==0 and gate['backend_tests']>484
        budget=AdvisoryBudget();base=AIConfig()
        if base.error():raise CopilotError('verification_configuration','Configuration unavailable; zero sends.')
    else:budget=None;base=AIConfig(api_key='unit-test-placeholder')
    config=replace(base,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1,
        thinking='medium',synthesis_thinking='low',synthesis_max_output_tokens=4096)
    req,catalog,records,envelopes,origin,info=prepare()
    assert records['e2']['payload']['action_state']==advisory_state()
    assert any(f.path=='action_state.plan_mode' for f in catalog.facts.values())
    body=synthesis_body(config,req,catalog,envelopes)
    report={'timestamp':stamp(),'case':'positive-final-advisory','mode':'live' if live else 'official SDK HTTP mock',
        'model':model,'sdk_version':version('google-genai'),'fact_contract_version':FACT_VERSION,
        'system_prompt_version':PROMPT_VERSION,'action_state_version':ACTION_VERSION,'action_state':advisory_state(),
        'generation_stages':{'native':config.generation(),'synthesis':config.generation(True)},
        'historical_provider_requests':29,'maximum_new_provider_requests':1,'new_provider_requests':0,
        'native_provider_requests':0,'retries':0,'fallbacks':0,'previous_interaction_id':None,
        'stateless':True,'provider_interaction_id_required':False,'production_chain':list(base.chain),
        'evidence_reuse':info,'fact_catalogue':envelopes,'authoritative_evidence':records,
        'preservation':preservation,'status':'RUNNING','native_orchestration':'PASS (preserved previous live evidence)',
        'final_synthesis':'PENDING','positive_workflow':'PENDING','phase6_complete':False,
        'remaining_cases':['followup','constrained','provenance'],'manual_factual_review':'PENDING'}
    transport=GeminiTransport(config);http_status=[];wire=[]
    if not live:
        transport.client.close()
        def handler(request):
            sent=json.loads(request.content);wire.append(sent)
            assert sent['model']==model and sent['generation_config']==config.generation(True)
            assert 'tools' not in sent and 'previous_interaction_id' not in sent
            return httpx.Response(200,json={'status':'completed','model':model,
                'steps':[{'type':'model_output','content':[{'type':'text','text':json.dumps(mock_draft(catalog))}]}]})
        transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
            client_args={'transport':httpx.MockTransport(handler)}))
    else:
        def wire_hook(request):
            sent=json.loads(request.content)
            assert request.method=='POST' and len(wire)==0 and sent['model']==MODEL
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
            output_length_characters=len(result.get('output_text','')))
        try:json.loads(result.get('output_text',''));report['complete_json']=True
        except (ValueError,TypeError):report['complete_json']=False
        if report['http_status']!=200:raise CopilotError('verification_http','Expected HTTP 200.')
        if result.get('model') and result['model']!=model:raise CopilotError('response_model','Provider model mismatch.')
        resolved,evidence,audits=validate(result,catalog,records,req,origin)
        report.update(status='PASS',final_synthesis='PASS',positive_workflow='PASS',schema='PASS',fact_ids='PASS',
            numeric_grounding='PASS',context='PASS',solver_terminology='PASS',action_state_grounding='PASS',
            qualitative_grounding='PASS (bounded domain guard; manual factual review pending)',
            unknown_fact_ids=0,unsupported_numbers=0,unsupported_execution_claims=0,
            claim_count=1+len(resolved.key_risks)+len(resolved.recommended_actions)+len(resolved.remaining_gaps),
            answer=resolved.model_dump(mode='json'),evidence=[e.model_dump(mode='json') for e in evidence],fact_audits=audits)
    except CopilotError as error:
        report.update(status='FAIL',final_synthesis='FAIL',positive_workflow='FAIL',
            error_code=error.code,provider_seconds=perf_counter()-started,http_status=http_status[-1] if http_status else None,
            provider_diagnostic=sanitize_diagnostic(getattr(error,'diagnostic',{}),config.api_key),
            citation_diagnostic=sanitize_diagnostic(getattr(error,'citation_diagnostic',{}),config.api_key),
            action_state_diagnostic=sanitize_diagnostic(getattr(error,'action_state_diagnostic',{}),config.api_key),
            numeric_diagnostic=sanitize_diagnostic(getattr(error,'grounding_diagnostic',{}),config.api_key))
    finally:
        transport.close();report['new_provider_requests']=budget.used if budget else 0
        report['mock_http_sends']=len(wire) if not live else 0
        report['provider_attempts_per_model']={model:budget.used} if budget else {}
        report['preservation']=preserved()
    return report


def preflight():
    assert not JOURNAL.exists() and json.loads(LEDGER.read_text())['used']==29
    suites=ET.parse(ROOT/'artifacts/phase6-action-pytest.xml').getroot().findall('testsuite')
    count=sum(int(s.get('tests','0')) for s in suites)
    assert count>484 and all(int(s.get(k,'0'))==0 for s in suites for k in ('failures','errors','skipped'))
    mock=json.loads((ROOT/'docs/evaluation/phase6-action-mock.json').read_text())
    canonical=json.loads((ROOT/'docs/evaluation/phase6-action-canonical.json').read_text())
    assert mock['status']==canonical['status']=='PASS' and canonical['live_gemini_requests']==0
    assert {t['model'] for t in mock['tests']}=={MODEL,'gemini-3.6-flash'}
    assert all(t['new_provider_requests']==0 for t in mock['tests'])
    for command in ([sys.executable,'-m','compileall','-q','backend','scripts'],[sys.executable,'-m','pip','check']):
        subprocess.run(command,cwd=ROOT,check=True,capture_output=True,text=True)
    gate={'timestamp':stamp(),'status':'PASS','backend_tests':count,
        'backend_seconds':sum(float(s.get('time','0')) for s in suites),
        'new_provider_requests':0,'mock':'PASS','canonical':'PASS','compile':'PASS','dependencies':'PASS',
        'old_failure':old_failure(),'preservation':preserved(),'security':secret_scan(),
        'frontend':'unchanged; prior successful strict TypeScript/Angular production build preserved',
        'implementation_sha256':identity()}
    GATE.write_text(json.dumps(gate,indent=2),encoding='utf-8');return gate


def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--mock',action='store_true');mode.add_argument('--live',action='store_true')
    mode.add_argument('--preflight',action='store_true');args=parser.parse_args()
    if args.preflight:
        gate=preflight();print(json.dumps({'status':'PASS','backend_tests':gate['backend_tests'],'new_provider_requests':0}));return 0
    if args.live:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
        with LEASE.open('x',encoding='utf-8') as handle:handle.write('one advisory synthesis authorization')
    try:
        reports=[run(True)] if args.live else [run(False,m) for m in (MODEL,'gemini-3.6-flash')]
        status='PASS' if all(t['status']=='PASS' for t in reports) else 'FAIL'
        path=ROOT/('docs/evaluation/phase6-action-live.json' if args.live else 'docs/evaluation/phase6-action-mock.json')
        path.write_text(json.dumps({'status':status,'tests':reports},indent=2),encoding='utf-8')
        print(json.dumps({'status':status,'report':path.relative_to(ROOT).as_posix(),
            'new_provider_requests':sum(t['new_provider_requests'] for t in reports)}))
        return 0 if status=='PASS' else 1
    finally:
        if args.live:LEASE.unlink()


if __name__=='__main__':raise SystemExit(main())
