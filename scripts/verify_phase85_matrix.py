"""Phase 8.5 end-only diagnostic: 2 independent attempts/model, 10 sends total.

Reuses the existing model-smoke request, server-prefetch, prompt, schema and
evidence validator. Production orchestration/configuration are never changed.
No retry, model handoff, resumed interaction or full acceptance workflow.
"""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
from time import monotonic, perf_counter, sleep

from verify_gemini import (ROOT, AIConfig, DEFAULT_CHAIN, CopilotRequest, CopilotService,
    CopilotError, GeminiTransport, DemoTransport, LocalRepository, ScenarioEngine,
    OptimizationService, QUESTIONS, validate_response)

MODELS = tuple(DEFAULT_CHAIN)
LEDGER = ROOT/'artifacts/gemini-verification-budget-live.json'
LEASE = ROOT/'artifacts/gemini-verifier.lock'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def classify(row):
    if row['grounded_response_accepted']:
        return 'PASS'
    code = row.get('error_class')
    if row.get('provider_available'):
        return 'GROUNDING_FAILURE' if code in ('evidence_validation', 'ungrounded_response',
            'evidence_invalid', 'unsupported_number', 'solver_terminology', 'unsafe_claim',
            'diagnostic_invariant_failure') else 'SCHEMA_FAILURE' if code in (
            'structured_response_invalid', 'schema_validation', 'invalid_response', 'response_schema') else 'APPLICATION_FAILURE'
    if row.get('http_status') == 429:
        return '429_' + (row.get('quota_kind') or 'UNKNOWN')
    if row.get('http_status') == 503:
        message = str(row.get('provider_message', '')).lower()
        return '503_HIGH_DEMAND' if any(s in message for s in ('high demand', 'high_demand', 'overloaded')) else '503_SERVICE_UNAVAILABLE'
    return {'provider_timeout':'TIMEOUT', 'authentication':'AUTH_FAILURE',
        'model_unavailable':'MODEL_UNAVAILABLE'}.get(code, 'OTHER_PROVIDER_FAILURE')


class MatrixAllowance:
    """Ten additional explicitly authorized sends, with historical ledger retained."""
    def __init__(self, live):
        self.live = live
        self.used = 0
        self.last_send = None
        self.not_before = 0.
        self.saved = json.loads(LEDGER.read_text()) if live else {'day':'mock','used':12,
            'per_model':{'legacy-unattributed':12}}
        self.initial = self.saved['used']
        self.initial_per_model = dict(self.saved.get('per_model', {}))

    def reserve(self, model):
        if self.used >= 10:
            raise CopilotError('matrix_budget_exhausted','Matrix ten-send ceiling reached; no request sent.',429)
        if self.live:
            deadline = max(self.not_before, (self.last_send + 20) if self.last_send is not None else 0.)
            while deadline > monotonic():
                sleep(min(30, deadline - monotonic()))
        self.used += 1
        self.saved['used'] += 1
        counts = self.saved.setdefault('per_model', {})
        counts[model] = counts.get(model, 0) + 1
        if self.live:
            # Preserve every existing field, day and per-model count; no reset.
            temp = LEDGER.with_suffix('.matrix.tmp')
            temp.write_text(json.dumps(self.saved), encoding='utf-8')
            temp.replace(LEDGER)
        self.last_send = monotonic()

    def respect_retry_after(self, diagnostic):
        for field in ('retry_after','retry_delay'):
            value = diagnostic.get(field)
            if not value: continue
            try: delay = float(str(value).rstrip('s'))
            except ValueError:
                try: delay = (parsedate_to_datetime(str(value)) - datetime.now(timezone.utc)).total_seconds()
                except (TypeError, ValueError, OverflowError): continue
            self.not_before = max(self.not_before, monotonic() + max(0,delay))


def check_live_gates():
    gates = json.loads((ROOT/'docs/evaluation/phase85-regression.json').read_text())
    assert gates['status'] == 'PASS' and gates['live_gemini_requests_before_matrix'] == 0
    before = json.loads((ROOT/'artifacts/phase85-preservation-before.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in before.items())
    assert json.loads(LEDGER.read_text())['used'] == 12, 'Historical accounting changed before matrix'


def matrix(mode, output, failure=None):
    live = mode == 'live'
    config = AIConfig() if live else AIConfig(api_key='unit-test-placeholder')
    if live:
        check_live_gates()
        if config.error():
            raise ValueError('Live configuration unavailable: '+config.error()[0])
    allowance = MatrixAllowance(live)
    repo, engine = LocalRepository(), ScenarioEngine()
    planner = OptimizationService(engine)
    report = {'timestamp':stamp(),'mode':mode,'purpose':'availability + grounded model-smoke only',
        'full_phase6_acceptance':False,'models':list(MODELS),'attempts_per_model':2,
        'maximum_new_provider_requests':10,'historical_ledger_preserved':allowance.initial,
        'cross_model_failover':False,'same_model_retries':0,'sdk_hidden_retries':False,
        'fresh_interaction_per_attempt':True,'minimum_send_spacing_seconds':20 if live else 0,
        'question':QUESTIONS['model-smoke'],'context':{'country_id':'IN','state_id':'MH',
            'district_id':'MH-PUNE','profile':'redistribution-ready'},
        'quota_source':'User-confirmed Google AI Studio Free tier headroom; no exact reset timestamp supplied.',
        'quota_remaining_after_run':None,'quota_notice':'Provider dashboard remains authoritative; local accounting is separate.',
        'attempts':[],'status':'completed'}
    stopped = False
    for model in MODELS:
        for attempt in (1,2):
            if stopped:
                report['attempts'].append({'model':model,'attempt':attempt,'status':'NOT_ATTEMPTED_AFTER_STOP',
                    'provider_available':None,'grounded_response_accepted':False,'provider_requests':0})
                continue
            row = {'timestamp':stamp(),'model':model,'attempt':attempt,'provider_available':False,
                'grounded_response_accepted':False,'schema_valid':False,'thinking_level':'medium',
                'http_status':None,'usage':None,'provider_requests':0,'provider_seconds':0.}
            provider = []
            # Isolated verifier config only; the locked production five-model chain is unchanged.
            cfg = replace(config,model=model,fallbacks=(),failover_enabled=False,
                same_model_attempts=1,thinking='medium')
            def factory(local_cfg):
                base = GeminiTransport(local_cfg) if live else DemoTransport(local_cfg)
                class Recorded(GeminiTransport if live else DemoTransport):
                    def __init__(self):
                        self.provider_requests = 0
                    def create(self, **body):
                        assert body['model'] == model and not body.get('previous_interaction_id')
                        assert self.provider_requests == 0, 'One send per independent attempt'
                        allowance.reserve(model)
                        self.provider_requests += 1
                        began = perf_counter()
                        try:
                            if failure:
                                error = CopilotError('rate_limited' if failure == 429 else 'provider_unavailable','Scripted diagnostic failure',failure)
                                error.diagnostic={'http_status':failure,'quota_kind':'RPD' if failure == 429 else None}
                                raise error
                            data = base.create(**body)
                            row.update(provider_available=True,http_status=200,usage=data.get('usage'))
                            return data
                        finally:
                            row.update(provider_requests=self.provider_requests,provider_seconds=perf_counter()-began)
                    def close(self):
                        base.close()
                transport = Recorded()
                provider.append(transport)
                return transport
            service = CopilotService(engine,planner,cfg,transport_factory=factory)
            request = CopilotRequest(**report['context'],message=QUESTIONS['model-smoke'],mode='gemini')
            before = repo.profile_snapshot('IN','redistribution-ready').model_dump_json()
            began = perf_counter()
            try:
                response = service.run(repo,request)
                validate_response(service,repo,response,'model-smoke',before)
                assert response.metadata['effective_model'] == model
                assert response.metadata['provider_requests'] == 1
                row.update(status='ACCEPTED_GROUNDED_SMOKE',grounded_response_accepted=True,
                    schema_valid=True,unsupported_numeric_claims=0,invalid_tool_calls=0,
                    effective_model=response.metadata['effective_model'],answer=response.answer,
                    evidence=[e.model_dump(mode='json') for e in response.evidence],
                    tool_calls=[t.model_dump(mode='json') for t in response.tools_used],
                    tool_seconds=response.metadata['tool_seconds'],usage=response.metadata.get('usage'))
            except (CopilotError, AssertionError) as error:
                row['error_class'] = error.code if isinstance(error,CopilotError) else 'diagnostic_invariant_failure'
                if row['provider_available'] and row['error_class'] in (
                        'evidence_invalid','unsupported_number','solver_terminology','unsafe_claim'):
                    row['schema_valid'] = True
                diagnostic = getattr(error,'diagnostic',{})
                allowance.respect_retry_after(diagnostic)
                for field in ('http_status','exception_type','quota_kind','retry_after','retry_delay','provider_message'):
                    if field in diagnostic:
                        row[field] = diagnostic[field]
                row['status'] = 'PROVIDER_AVAILABLE_APPLICATION_REJECTED' if row['provider_available'] else 'PROVIDER_UNAVAILABLE' if row['provider_requests'] else 'APPLICATION_REJECTED_BEFORE_PROVIDER'
                audit = service.audit[-1] if service.audit else {}
                row['tool_calls'] = audit.get('tools',[])
                row['usage'] = audit.get('usage') or row['usage']
                row['tool_seconds'] = audit.get('timings',{}).get('tool_seconds')
                # Quota/authentication failures end the diagnostic without hammering any model.
                if row['error_class'] in ('rate_limited','authentication','matrix_budget_exhausted'):
                    stopped = True
                    report['status'] = 'stopped_'+row['error_class']
            row['total_seconds'] = perf_counter()-began
            row['classification'] = classify(row)
            row['successful_interaction'] = row['provider_available']
            report['attempts'].append(row)
            report['new_provider_requests'] = allowance.used
            report['final_ledger_used'] = allowance.saved['used']
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
            print(model,attempt,row['status'],row['http_status'],round(row['provider_seconds'],3),'s',flush=True)
    report['new_provider_requests'] = allowance.used
    report['provider_requests_per_model'] = {m:allowance.saved['per_model'].get(m,0)-allowance.initial_per_model.get(m,0) for m in MODELS}
    report['final_ledger_used'] = allowance.saved['used']
    assert allowance.saved['used'] == allowance.initial + allowance.used and allowance.used <= 10
    output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    return report


def self_test():
    output = ROOT/'artifacts/phase85-matrix-self-test.json'
    success = matrix('mock',output)
    assert success['new_provider_requests'] == 10 and all(a['grounded_response_accepted'] for a in success['attempts'])
    unavailable = matrix('mock',output,503)
    assert unavailable['new_provider_requests'] == 10 and len(unavailable['attempts']) == 10
    assert not any(a['provider_available'] for a in unavailable['attempts'])
    quota = matrix('mock',output,429)
    assert quota['new_provider_requests'] == 1 and quota['status'] == 'stopped_rate_limited'
    allowance = MatrixAllowance(False)
    for _ in range(10): allowance.reserve(MODELS[0])
    try: allowance.reserve(MODELS[1])
    except CopilotError: pass
    else: raise AssertionError('Eleventh send was permitted')
    assert classify({'grounded_response_accepted':False,'http_status':503,
        'provider_message':'HIGH DEMAND'}) == '503_HIGH_DEMAND'
    assert classify({'grounded_response_accepted':False,'http_status':503}) == '503_SERVICE_UNAVAILABLE'
    assert classify({'grounded_response_accepted':False,'http_status':429,'quota_kind':'TPM'}) == '429_TPM'
    print('PASS: fresh 2 x 5, success/503/429 classification, no failover, global cap, ledger preservation; ZERO live requests')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--live',action='store_true')
    mode.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        LEASE.touch(exist_ok=False)
        try: matrix('live',ROOT/'docs/evaluation/phase85-gemini-availability.json')
        finally: LEASE.unlink()
