"""Diagnose retained evidence, mock two candidates, then at most two targeted live sends.

Second live send requires the first independent Flash-Lite smoke to pass.
No matrix, provider retry, failover, full workflow or historical-ledger reset.
"""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter, monotonic, sleep
from verify_gemini import (ROOT, AIConfig, CopilotRequest, CopilotService, CopilotError,
    GeminiTransport, DemoTransport, LocalRepository, ScenarioEngine, OptimizationService,
    QUESTIONS, validate_response)
from app.ai.tools import ToolExecutor
from app.ai.protocol import compact, model_record, byte_size
from app.ai.citations import sanitize_diagnostic
from app.ai.schemas import DraftAnswer
from app.ai.system_prompt import VERSION as PROMPT_VERSION

MODELS=('gemini-3.5-flash-lite','gemini-3.6-flash')
CONTEXT=dict(country_id='IN',state_id='MH',district_id='MH-PUNE',profile='redistribution-ready')
LEDGER=ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL=ROOT/'artifacts/phase6-numeric-live-sends.json'
LEASE=ROOT/'artifacts/gemini-verifier.lock'
ALLOWED={'backend/app/ai/citations.py','backend/app/ai/orchestrator.py',
    'backend/app/ai/protocol.py','backend/app/ai/schemas.py','backend/app/ai/system_prompt.py'}


def stamp(): return datetime.now(timezone.utc).isoformat()


def preserved(*, after_live=False):
    before=json.loads((ROOT/'artifacts/phase6-grounding-preservation-before.json').read_text())
    ledger_path='artifacts/gemini-verification-budget-live.json'
    journalled=JOURNAL.exists()
    if journalled:
        journal=json.loads(JOURNAL.read_text())
        sends=journal['new_provider_requests']
        assert journal['initial_historical_requests']==22 and journal['authorized_maximum_new_requests']==2 and 1<=sends<=2
        historical=json.loads(LEDGER.read_text())
        historical['used']-=sends
        historical['per_model'][MODELS[0]]-=sends
        # Validate the entire original ledger, including date and every other model.
        assert hashlib.sha256(json.dumps(historical).encode('utf-8')).hexdigest()==before[ledger_path], 'Historical ledger changed'
    assert not after_live or journalled, 'Live preservation requires its retained send journal'
    allowed=ALLOWED | ({ledger_path} if journalled else set())
    for path,digest in before.items():
        if path not in allowed:
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, 'Locked file changed: '+path
    return {'checked':len(before),'unchanged':sum(p not in allowed for p in before),'environment_unchanged':True,
        'ui_unchanged':True,'existing_tests_unchanged':True,'operational_assets_unchanged':True}


def diagnose():
    original=json.loads((ROOT/'docs/evaluation/phase85-gemini-availability.json').read_text())
    request=CopilotRequest(**CONTEXT,message=QUESTIONS['model-smoke'],mode='gemini')
    repo=LocalRepository();engine=ScenarioEngine();executor=ToolExecutor(repo,engine,OptimizationService(engine),request)
    evidence=[]
    for index,name in enumerate(('get_network_summary','get_warning_summary'),1):
        result=executor.execute(name,CONTEXT)
        evidence.append({'evidence_id':f'e{index}','tool':name,'result':compact(name,result)})
    rows=[]
    for row in original['attempts']:
        if row.get('http_status')==200:
            rows.append({'model':row['model'],'attempt':row['attempt'],'error_class':row['error_class'],
                'exact_unsupported_number':None,'sentence_or_field':None,'classification':'NOT_RECOVERABLE',
                'model_error_vs_validator_error':'UNDETERMINED',
                'reason':'The Phase 8.5 verifier did not persist the rejected draft, numeric token or cited paths.',
                'supplied_evidence':'reconstructed_authoritative_evidence'})
    return {'status':'DIAGNOSIS_LIMITED_BY_RETAINED_TRACE','timestamp':stamp(),'provider_requests':0,
        'baseline_commit':'7cec2c6','historical_rejections':rows,
        'reconstructed_authoritative_evidence':evidence,
        'reconstruction_notice':'Local tool reads against unchanged origin/profile assets; not a retained provider response or wire capture.',
        'observed_contract_gaps':['Old validator admitted rounded forms and automatic risk percentage conversion.',
            'Old prompt did not explicitly forbid every derived number or prefer qualitative text.',
            'Final resilience context included irrelevant nationwide geography catalogues.',
            'Rejections omitted exact claim/reference diagnostics.'],
        'historical_cause_notice':'These observed gaps cannot be assigned as the cause of an individual historical rejection.',
        'preservation':preserved()}


class Allowance:
    def __init__(self,live):
        self.live=live;self.used=0;self.last=None
        self.saved=json.loads(LEDGER.read_text()) if live else {'used':22,'per_model':{}}
        self.initial=self.saved['used'];self.initial_counts=dict(self.saved.get('per_model',{}))
        if live:
            assert self.initial==22 and not JOURNAL.exists(), 'This authorization must not be replayed or reset'
    def consume(self):
        assert self.used<2, 'At most two new provider sends'
        if self.live and self.last is not None:
            delay=30-(monotonic()-self.last)
            if delay>0:sleep(delay)
        self.used+=1;self.saved['used']+=1
        self.saved.setdefault('per_model',{})[MODELS[0]]=self.saved['per_model'].get(MODELS[0],0)+1
        if self.live:
            temporary=LEDGER.with_suffix('.numeric.tmp')
            temporary.write_text(json.dumps(self.saved),encoding='utf-8');temporary.replace(LEDGER)
            JOURNAL.write_text(json.dumps({'initial_historical_requests':self.initial,
                'authorized_maximum_new_requests':2,'new_provider_requests':self.used,'timestamp':stamp()}),encoding='utf-8')
        self.last=monotonic()


def run(mode):
    live=mode=='live';base=AIConfig() if live else AIConfig(api_key='unit-test-placeholder')
    if live:
        gates=json.loads((ROOT/'docs/evaluation/phase6-numeric-regression.json').read_text())
        assert gates['status']=='PASS' and gates['live_provider_requests_before_smoke']==0
        preserved()
        if base.error():raise ValueError('Configuration unavailable: '+base.error()[0])
    allowance=Allowance(live)
    repo=LocalRepository();engine=ScenarioEngine();planner=OptimizationService(engine)
    report={'timestamp':stamp(),'mode':mode,'system_prompt_version':PROMPT_VERSION,
        'question':QUESTIONS['model-smoke'],'context':CONTEXT,'full_phase6_acceptance':False,
        'live_model_priority':MODELS[0],'maximum_new_provider_requests':2,'failover':False,
        'same_model_retries':0,'sdk_hidden_retries':False,'independent_interactions':True,
        'second_live_attempt_requires_first_pass':True,'attempts':[]}
    targets=[(MODELS[0],1),(MODELS[0],2)] if live else [(m,1) for m in MODELS]
    for model,attempt in targets:
        row={'model':model,'attempt':attempt,'timestamp':stamp(),'provider_available':False,
            'schema_valid':False,'grounding_valid':False,'http_status':None,'provider_seconds':0.,
            'provider_requests':0,'thinking_level':'medium'}
        config=replace(base,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1,thinking='medium')
        def factory(cfg):
            class Recorded(GeminiTransport if live else DemoTransport):
                def create(self,**body):
                    assert body['model']==model and not body.get('previous_interaction_id')
                    assert self.provider_requests==0
                    began=perf_counter()
                    def reserve():
                        nonlocal began
                        allowance.consume()
                        # Exclude verifier pacing from actual provider latency.
                        began=perf_counter()
                    self.before_request=reserve if live else None
                    inputs=json.loads(body['input'])
                    row['supplied_evidence']=sanitize_diagnostic(inputs.get('server_prefetched_evidence',[]),cfg.api_key)
                    row['input_bytes']=byte_size(body['input'])
                    try:
                        result=super().create(**body)
                        row.update(http_status=200,provider_available=True,usage=result.get('usage'))
                        try:
                            draft=DraftAnswer.model_validate_json(result.get('output_text',''))
                            row.update(schema_valid=True,draft=sanitize_diagnostic(draft.model_dump(mode='json'),cfg.api_key))
                        except (ValueError,TypeError):pass
                        return result
                    finally:
                        row.update(provider_requests=self.provider_requests,provider_seconds=perf_counter()-began)
            return Recorded(cfg)
        service=CopilotService(engine,planner,config,transport_factory=factory)
        before=repo.profile_snapshot('IN','redistribution-ready').model_dump_json()
        began=perf_counter()
        try:
            response=service.run(repo,CopilotRequest(**CONTEXT,message=QUESTIONS['model-smoke'],mode='gemini'))
            validate_response(service,repo,response,'model-smoke',before)
            assert response.metadata['effective_model']==model and response.metadata['provider_requests']==1
            row.update(status='PASS',grounding_valid=True,unsupported_numeric_claims=0,
                evidence_validation_passed=True,invalid_tool_calls=0,
                response=response.model_dump(mode='json'),usage=response.metadata.get('usage'),
                tool_seconds=response.metadata['tool_seconds'])
        except (CopilotError,AssertionError) as error:
            row.update(status='FAIL',error_class=error.code if isinstance(error,CopilotError) else 'diagnostic_invariant_failure',
                grounding_diagnostic=getattr(error,'grounding_diagnostic',None))
            if row['grounding_diagnostic']:
                row['unsupported_numeric_claims']=len(row['grounding_diagnostic']['unsupported_numbers'])
            row.update({k:v for k,v in getattr(error,'diagnostic',{}).items() if k in
                ('http_status','exception_type','quota_kind','retry_after','retry_delay','provider_message')})
            audit=service.audit[-1] if service.audit else {}
            row.update(usage=audit.get('usage') or row.get('usage'),tool_calls=audit.get('tools',[]),
                tool_seconds=audit.get('timings',{}).get('tool_seconds'))
        row['total_seconds']=perf_counter()-began
        assert repo.profile_snapshot('IN','redistribution-ready').model_dump_json()==before
        report['attempts'].append(row)
        path=ROOT/f'docs/evaluation/phase6-numeric-{mode}.json'
        report.update(new_provider_requests=sum(r['provider_requests'] for r in report['attempts']),
            historical_requests_preserved=allowance.initial if live else None,
            final_ledger_used=allowance.saved['used'] if live else None)
        path.write_text(json.dumps(sanitize_diagnostic(report,base.api_key),indent=2,allow_nan=False),encoding='utf-8')
        print(model,attempt,row['status'],row['http_status'],round(row['provider_seconds'],3),'s',flush=True)
        if live and row['status']!='PASS':break
    report['status']='PASS' if len(report['attempts'])==2 and all(r['status']=='PASS' for r in report['attempts']) else 'STOPPED_AFTER_FAILURE'
    report['preservation']=preserved(after_live=live)
    path.write_text(json.dumps(sanitize_diagnostic(report,base.api_key),indent=2,allow_nan=False),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    options=parser.add_mutually_exclusive_group(required=True)
    options.add_argument('--diagnose',action='store_true')
    options.add_argument('--mock',action='store_true')
    options.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if args.diagnose:
        path=ROOT/'docs/evaluation/phase6-numeric-diagnosis.json'
        path.write_text(json.dumps(diagnose(),indent=2,allow_nan=False),encoding='utf-8')
        print('Diagnosis retained; exact historical claims unavailable; ZERO live calls')
    elif args.mock:run('mock')
    else:
        LEASE.touch(exist_ok=False)
        try:run('live')
        finally:LEASE.unlink()
