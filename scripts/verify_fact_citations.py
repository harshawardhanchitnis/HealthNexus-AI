"""Fact-ID acceptance: two shared mocks; live first PASS permits one second send only."""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from time import monotonic,perf_counter,sleep
from verify_gemini import (ROOT,AIConfig,CopilotRequest,CopilotService,CopilotError,
    GeminiTransport,DemoTransport,LocalRepository,ScenarioEngine,OptimizationService,QUESTIONS,validate_response)
from app.ai.facts import VERSION as FACT_VERSION
from app.ai.schemas import FactDraftAnswer
from app.ai.citations import sanitize_diagnostic
from app.ai.system_prompt import VERSION as PROMPT_VERSION

MODEL='gemini-3.5-flash-lite'
MODELS=(MODEL,'gemini-3.6-flash')
CONTEXT=dict(country_id='IN',state_id='MH',district_id='MH-PUNE',profile='redistribution-ready')
LEDGER=ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL=ROOT/'artifacts/phase6-facts-live-sends.json'
LEASE=ROOT/'artifacts/gemini-verifier.lock'
ALLOWED={'backend/app/ai/orchestrator.py','backend/app/ai/schemas.py','backend/app/ai/system_prompt.py','backend/app/ai/numeric.py',
    'backend/tests/test_ai.py','backend/tests/test_ai_budget.py','backend/tests/test_ai_failover.py',
    'backend/tests/test_ai_numeric_contract.py'}


def stamp():return datetime.now(timezone.utc).isoformat()


def preserved():
    before=json.loads((ROOT/'artifacts/phase6-facts-preservation-before.json').read_text())
    ledger_path='artifacts/gemini-verification-budget-live.json'
    if JOURNAL.exists():
        journal=json.loads(JOURNAL.read_text());original=journal['historical_ledger']
        assert original['used']==23 and 1<=journal['new_provider_requests']<=2
        assert hashlib.sha256(json.dumps(original).encode()).hexdigest()==before[ledger_path]
        expected=deepcopy(original);sends=journal['new_provider_requests']
        expected['used']+=sends;expected['per_model'][MODEL]+=sends
        assert json.loads(LEDGER.read_text())==expected,'Historical ledger fields changed'
    allowed=ALLOWED | ({ledger_path} if JOURNAL.exists() else set())
    for name,digest in before.items():
        if name not in allowed:
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Locked file changed: '+name
    return {'files_checked':len(before),'unchanged':sum(p not in allowed for p in before),
        'env_unchanged':True,'ui_unchanged':True,'operational_and_federation_assets_unchanged':True,
        'historical_reports_unchanged':True,'production_fallback_order_unchanged':True}


class Allowance:
    """Preflight is read-only. The official SDK's HTTP send hook appends actual attempts."""
    def __init__(self,ledger=LEDGER,journal=JOURNAL):
        self.ledger,self.journal=Path(ledger),Path(journal)
        self.original=json.loads(self.ledger.read_text());self.saved=deepcopy(self.original)
        assert self.original['used']==23 and not self.journal.exists(),'Authorization cannot be reset or replayed'
        self.used=0;self.last=None
    def preflight(self):
        assert self.used<2,'At most two actual sends across this run'
        if self.last is not None:
            delay=30-(monotonic()-self.last)
            if delay>0:sleep(delay)
    def record_send(self):
        assert self.used<2,'Global send ceiling'
        self.used+=1;self.saved['used']+=1;self.saved['per_model'][MODEL]+=1
        temporary=self.ledger.with_suffix('.facts.tmp')
        temporary.write_text(json.dumps(self.saved),encoding='utf-8');temporary.replace(self.ledger)
        self.journal.write_text(json.dumps({'historical_ledger':self.original,
            'maximum_new_provider_requests':2,'new_provider_requests':self.used,'timestamp':stamp()}),encoding='utf-8')
        self.last=monotonic()


def accepted(row):
    return all(row.get(key) is True for key in ('schema_valid','fact_ids_valid','qualitative_evidence_valid',
        'numeric_grounding_valid','context_valid')) and row.get('http_status')==200 and row.get('unknown_fact_ids')==0 and row.get('unsupported_numeric_claims')==0


def run(mode,transport_type=None):
    live=mode=='live';base=AIConfig() if live else AIConfig(api_key='unit-test-placeholder')
    if live:
        gate=json.loads((ROOT/'docs/evaluation/phase6-facts-regression.json').read_text())
        assert gate['status']=='PASS' and gate['live_provider_requests_before_smoke']==0
        assert gate['fact_contract_version']==FACT_VERSION and gate['system_prompt_version']==PROMPT_VERSION
        preserved()
        if base.error():raise ValueError('Configuration unavailable: '+base.error()[0])
    allowance=Allowance() if live else None
    repo=LocalRepository();engine=ScenarioEngine();planner=OptimizationService(engine)
    report={'timestamp':stamp(),'mode':mode,'baseline_commit':'c526378','fact_contract_version':FACT_VERSION,
        'system_prompt_version':PROMPT_VERSION,'context':CONTEXT,'question':QUESTIONS['model-smoke'],
        'maximum_new_provider_requests':2,'historical_ledger_preserved':23,'failover':False,'same_model_retries':0,
        'sdk_hidden_retries':False,'independent_interactions':True,'full_phase6_acceptance':False,'attempts':[]}
    targets=[(MODEL,1),(MODEL,2)] if live else [(m,1) for m in MODELS]
    for model,attempt in targets:
        row={'model':model,'attempt':attempt,'thinking_level':'medium','timestamp':stamp(),'http_status':None,
            'schema_valid':False,'fact_ids_valid':False,'qualitative_evidence_valid':False,
            'numeric_grounding_valid':False,'context_valid':False,'unknown_fact_ids':None,
            'unsupported_numeric_claims':None,'actual_http_sends':0,'provider_requests':0,'provider_seconds':0.}
        cfg=replace(base,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1,thinking='medium')
        def factory(config):
            class Recorded(transport_type or (GeminiTransport if live else DemoTransport)):
                def create(self,**body):
                    assert body['model']==model and not body.get('previous_interaction_id') and self.provider_requests==0
                    row['supplied_catalogues']=sanitize_diagnostic(json.loads(body['input']).get('server_prefetched_evidence',[]),config.api_key)
                    row['input_utf8_bytes']=len(body['input'].encode('utf-8'))
                    began=perf_counter()
                    if live:
                        self.before_request=allowance.preflight
                        client=self.client.interactions.sdk_configuration.client
                        assert hasattr(client,'event_hooks'),'SDK wire hook unavailable; no sends permitted'
                        def on_send(request):
                            nonlocal began
                            assert row['actual_http_sends']==0 and request.method=='POST','One actual HTTP send per smoke'
                            assert json.loads(request.content)['model']==model
                            allowance.record_send();row['actual_http_sends']+=1;began=perf_counter()
                        client.event_hooks.setdefault('request',[]).append(on_send)
                    try:
                        response=super().create(**body)
                        row.update(http_status=200,usage=response.get('usage'))
                        try:
                            draft=FactDraftAnswer.model_validate_json(response.get('output_text',''))
                            row.update(schema_valid=True,draft=sanitize_diagnostic(draft.model_dump(mode='json'),config.api_key))
                        except (ValueError,TypeError):pass
                        return response
                    finally:row.update(provider_requests=self.provider_requests,provider_seconds=perf_counter()-began)
            return Recorded(config)
        service=CopilotService(engine,planner,cfg,transport_factory=factory)
        before=repo.profile_snapshot('IN','redistribution-ready').model_dump_json();began=perf_counter()
        try:
            response=service.run(repo,CopilotRequest(**CONTEXT,message=QUESTIONS['model-smoke'],mode='gemini'))
            validate_response(service,repo,response,'model-smoke',before)
            assert response.metadata['effective_model']==model and response.metadata['provider_requests']==1
            if live:assert row['actual_http_sends']==1
            validation=response.metadata['fact_validation']
            assert validation['unknown_fact_ids']==0 and validation['semantic_validation']==validation['numeric_validation']=='PASS'
            row.update(fact_ids_valid=True,qualitative_evidence_valid=True,numeric_grounding_valid=True,
                context_valid=True,unknown_fact_ids=0,unsupported_numeric_claims=0,response=response.model_dump(mode='json'),
                usage=response.metadata.get('usage'),tool_seconds=response.metadata['tool_seconds'],
                fact_citations=service.audit[-1]['fact_citations'])
        except (CopilotError,AssertionError) as error:
            row.update(error_class=error.code if isinstance(error,CopilotError) else 'verification_invariant',
                citation_diagnostic=getattr(error,'citation_diagnostic',None),
                grounding_diagnostic=getattr(error,'grounding_diagnostic',None))
            if row['citation_diagnostic']:row['unknown_fact_ids']=len(row['citation_diagnostic']['unknown_fact_ids'])
            if row['grounding_diagnostic']:row['unsupported_numeric_claims']=len(row['grounding_diagnostic']['unsupported_numbers'])
            row.update({k:v for k,v in getattr(error,'diagnostic',{}).items() if k in
                ('http_status','exception_type','quota_kind','retry_after','provider_message')})
            audit=service.audit[-1] if service.audit else {}
            row.update(usage=audit.get('usage') or row.get('usage'),tool_calls=audit.get('tools',[]),
                tool_seconds=audit.get('timings',{}).get('tool_seconds'))
        row.update(status='PASS' if accepted(row) else 'FAIL',total_seconds=perf_counter()-began)
        assert repo.profile_snapshot('IN','redistribution-ready').model_dump_json()==before
        report['attempts'].append(row)
        report.update(new_actual_provider_requests=sum(r['actual_http_sends'] for r in report['attempts']),
            scripted_requests=sum(r['provider_requests'] for r in report['attempts']) if not live else 0,
            ledger_after=allowance.saved['used'] if live else 23)
        path=ROOT/f'docs/evaluation/phase6-facts-{mode}.json'
        path.write_text(json.dumps(sanitize_diagnostic(report,base.api_key),indent=2,allow_nan=False),encoding='utf-8')
        print(model,attempt,row['status'],row['http_status'],round(row['provider_seconds'],3),'s',flush=True)
        if live and not accepted(row):break
    report['status']='PASS' if len(report['attempts'])==2 and all(accepted(r) for r in report['attempts']) else 'STOPPED_AFTER_FAILURE'
    report['preservation']=preserved()
    path.write_text(json.dumps(sanitize_diagnostic(report,base.api_key),indent=2,allow_nan=False),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--mock',action='store_true');mode.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if args.mock:run('mock')
    else:
        LEASE.touch(exist_ok=False)
        try:run('live')
        finally:LEASE.unlink()
