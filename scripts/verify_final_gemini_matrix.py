"""Diagnostic only: fresh application smoke, one optional second attempt/model.

No production modifications. Actual SDK HTTP hooks account for every send.
Live authorization is single-use: an existing journal cannot be replayed.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import subprocess
from time import monotonic, perf_counter, sleep
from uuid import uuid4

import httpx
from google import genai
from google.genai import types
from verify_gemini import (ROOT, AIConfig, DEFAULT_CHAIN, CopilotRequest, CopilotService,
    CopilotError, GeminiTransport, DemoTransport, LocalRepository, ScenarioEngine,
    OptimizationService, validate_response)
from app.ai.schemas import FactDraftAnswer
from app.ai.citations import sanitize_diagnostic

MODELS = tuple(DEFAULT_CHAIN)
QUESTION = 'Summarize the current resource resilience status in Pune.'
CONTEXT = dict(country_id='IN', state_id='MH', district_id='MH-PUNE', profile='redistribution-ready')
LEDGER = ROOT/'artifacts/gemini-verification-budget-live.json'
JOURNAL = ROOT/'artifacts/final-gemini-matrix-live-journal.json'
LEASE = ROOT/'artifacts/gemini-verifier.lock'
OUTPUT = ROOT/'docs/evaluation/final-gemini-model-availability.json'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preservation():
    assert subprocess.check_output(['git','rev-parse','--short','HEAD'],cwd=ROOT,text=True).strip() == '3c144e7'
    names = subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    # Also protect ignored model, planning and federation identities and .env.
    old = json.loads((ROOT/'artifacts/phase9-preservation-before.json').read_text())
    names = set(names) | (set(old['protected']) - {'artifacts/gemini-verification-budget-live.json'})
    return {name:digest(ROOT/name) for name in sorted(names)}


class Allowance:
    def __init__(self, ledger=None, journal=None, pace=20):
        self.ledger, self.journal = ledger, journal
        self.original = json.loads(ledger.read_text()) if ledger else {'day':'mock','used':42,'per_model':{}}
        self.saved = deepcopy(self.original)
        self.sends, self.last, self.not_before, self.pace = [], None, 0., pace
        if journal and journal.exists():
            raise ValueError('This live authorization has already been used; no replay permitted.')

    def wait(self):
        deadline = max(self.not_before, self.last+self.pace if self.last is not None else 0.)
        while deadline > monotonic():
            sleep(min(20,deadline-monotonic()))

    def reserve(self, model, attempt):
        if len(self.sends) >= 10 or any(s['model']==model and s['attempt']==attempt for s in self.sends):
            raise ValueError('Duplicate wire send or global ten-send ceiling; request prohibited.')
        assert model in MODELS and attempt in (1,2)
        if self.ledger:
            assert json.loads(self.ledger.read_text()) == self.saved, 'Concurrent ledger mutation'
        entry = dict(timestamp=stamp(),model=model,attempt=attempt,diagnostic='final-gemini-matrix')
        self.sends.append(entry)
        self.saved['used'] += 1
        counts = self.saved.setdefault('per_model',{})
        counts[model] = counts.get(model,0)+1
        self.saved.setdefault('verification_sends',[]).append(entry)
        if self.journal:
            row = dict(historical_ledger=self.original,maximum_new_sends=10,sends=self.sends,terminal=False)
            if len(self.sends)==1:
                with self.journal.open('x',encoding='utf-8') as handle: json.dump(row,handle)
            else:
                self.journal.write_text(json.dumps(row),encoding='utf-8')
            temp = self.ledger.with_suffix('.final-matrix.tmp')
            temp.write_text(json.dumps(self.saved),encoding='utf-8'); temp.replace(self.ledger)
        self.last = monotonic()

    def retry_after(self, value):
        if value is None: return
        try: delay=float(str(value).rstrip('s'))
        except ValueError:
            try: delay=(parsedate_to_datetime(str(value))-datetime.now(timezone.utc)).total_seconds()
            except (ValueError,TypeError,OverflowError): return
        self.not_before=max(self.not_before,monotonic()+max(0,delay))

    def finish(self):
        if self.journal and self.journal.exists():
            data=json.loads(self.journal.read_text()); data['terminal']=True
            self.journal.write_text(json.dumps(data),encoding='utf-8')


def classify(row):
    if row['accepted']: return 'AVAILABLE_ACCEPTED'
    if row['http_status']==200: return 'AVAILABLE_APPLICATION_REJECTED'
    if row['http_status']==503:
        return '503_HIGH_DEMAND' if any(s in row.get('provider_message','').lower() for s in ('high demand','high_demand','overload')) else '503_SERVICE_UNAVAILABLE'
    return {429:'429_RATE_LIMIT',401:'AUTH_ERROR',403:'AUTH_ERROR',404:'MODEL_UNAVAILABLE',
            400:'CONFIGURATION_UNSUPPORTED'}.get(row['http_status'],'OTHER_PROVIDER_ERROR')


def run(live=False, output=OUTPUT, ledger=LEDGER, journal=JOURNAL, mock_outcomes=None, quota_confirmed=False):
    if live and not quota_confirmed: raise ValueError('Current run provider headroom must be explicitly confirmed.')
    protected=preservation() if live else {}
    cfg=AIConfig() if live else AIConfig(api_key='mock-placeholder',enabled=True)
    if cfg.error(): raise ValueError('Local configuration unavailable: '+cfg.error()[0])
    budget=Allowance(ledger if live else None,journal if live else None,20 if live else 0)
    report=dict(timestamp=stamp(),baseline='3c144e7',live=live,models=list(MODELS),question=QUESTION,
                context=CONTEXT,quota_confirmation='User explicitly confirmed quota available for this run.' if live else 'mock only',
                contract='Frozen resilience-summary FactDraftAnswer + current fact-ID/numeric/qualitative validation',
                semantic_slots=False,prose_author='provider; server validates and resolves evidence',
                status='RUNNING',thinking=cfg.synthesis_thinking,max_output_tokens=cfg.synthesis_max_output_tokens,production_fallback_changed=False,
                fallback=False,sdk_retry=False,maximum_sends=10,attempts=[],ledger_before=budget.original['used'])
    repo=LocalRepository(); engine=ScenarioEngine(); planner=OptimizationService(engine)
    before=repo.profile_snapshot('IN','redistribution-ready').model_dump_json()
    def save():
        report.update(new_provider_sends=len(budget.sends) if live else 0,mock_sends=len(budget.sends) if not live else 0,
                      ledger_after=budget.saved['used'] if live else budget.original['used'])
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(sanitize_diagnostic(report,cfg.api_key),indent=2,allow_nan=False),encoding='utf-8')
    blocked=False
    try:
        for model in MODELS:
            if blocked: break
            for attempt in (1,2):
                budget.wait()
                row=dict(model=model,attempt=attempt,http_status=None,provider_status=None,accepted=False,
                         schema='NOT REACHED',fact_ids='NOT REACHED',grounding='NOT REACHED',
                         unknown_ids=None,unsupported_numbers=None,usage=None,wire_sends=0)
                report['attempts'].append(row)
                local=replace(cfg,model=model,fallbacks=(),failover_enabled=False,same_model_attempts=1)
                def factory(config):
                    class Observed(GeminiTransport):
                        def __init__(self):
                            super().__init__(config)
                            if not live:
                                self.client.close()
                                scripted=DemoTransport(config)
                                def handle(req):
                                    body=json.loads(req.content)
                                    outcome=(mock_outcomes or {}).get((model,attempt),'ok')
                                    if isinstance(outcome,int):
                                        return httpx.Response(outcome,json={'error':{'code':outcome,'message':'HIGH DEMAND' if outcome==503 else 'Mock diagnostic error'}})
                                    result=scripted.create(**body)
                                    if outcome=='schema':result['output_text']='{}'
                                    if outcome=='unknown':
                                        draft=json.loads(result['output_text']);draft['situation']['evidence_refs']=['unknown-id'];result['output_text']=json.dumps(draft)
                                    return httpx.Response(200,json={'id':str(uuid4()),'status':'completed','model':model,
                                        'usage':{'total_input_tokens':10,'total_output_tokens':8,'total_tokens':18},
                                        'steps':[{'type':'model_output','content':[{'type':'text','text':result['output_text']}]}]})
                                self.client=genai.Client(api_key='mock-placeholder',http_options=types.HttpOptions(client_args={'transport':httpx.MockTransport(handle)}))
                        def create(self,**body):
                            assert body['model']==model and 'previous_interaction_id' not in body and 'tools' not in body
                            assert 'response_format' in body and body['generation_config']==local.generation(True)
                            client=self.client.interactions.sdk_configuration.client
                            def on_send(request):
                                if row['wire_sends']:raise ValueError('Hidden SDK retry prohibited.')
                                sent=json.loads(request.content)
                                assert request.method=='POST' and sent['model']==model and not sent.get('previous_interaction_id')
                                budget.reserve(model,attempt);row['wire_sends']+=1;save()
                            def on_response(response):
                                row['http_status']=response.status_code
                                row['retry_after']=response.headers.get('retry-after')
                            client.event_hooks.setdefault('request',[]).append(on_send)
                            client.event_hooks.setdefault('response',[]).append(on_response)
                            began=perf_counter()
                            try:
                                result=super().create(**body)
                                row.update(provider_status=result.get('status'),usage=result.get('usage'))
                                try: FactDraftAnswer.model_validate_json(result.get('output_text',''));row['schema']='PASS'
                                except (ValueError,TypeError):row['schema']='FAIL'
                                if result.get('status')!='completed':raise CopilotError('response_incomplete','Provider synthesis is not completed.')
                                return result
                            finally:row['provider_seconds']=perf_counter()-began
                    return Observed()
                service=CopilotService(engine,planner,local,transport_factory=factory)
                started=perf_counter()
                try:
                    response=service.run(repo,CopilotRequest(**CONTEXT,message=QUESTION))
                    validate_response(service,repo,response,'model-smoke',before)
                    assert response.metadata['provider_requests']==1 and response.metadata['effective_model']==model
                    assert response.metadata['intent']=='resilience-summary' and response.metadata['semantic_frame_version'] is None
                    assert {t.tool for t in response.tools_used}=={'get_network_summary','get_warning_summary'}
                    row.update(accepted=True,schema='PASS',fact_ids='PASS',grounding='PASS',unknown_ids=0,unsupported_numbers=0,
                               answer=response.answer,evidence=[e.model_dump(mode='json') for e in response.evidence],
                               fact_validation=response.metadata['fact_validation'],action_validation=response.metadata['action_state_validation'],
                               tools=[t.model_dump(mode='json') for t in response.tools_used],tool_seconds=response.metadata['tool_seconds'])
                except CopilotError as error:
                    diagnostic=sanitize_diagnostic(getattr(error,'diagnostic',{}),cfg.api_key)
                    for field in ('provider_message','quota_kind','model_specific_quota','retry_delay','retry_after'):
                        if field in diagnostic:row[field]=diagnostic[field]
                    row['error_code']=error.code
                    citation=getattr(error,'citation_diagnostic',{})
                    row['failure_reason']=citation.get('reason') or getattr(error,'narrative_diagnostic',{}).get('reason') or error.code
                    if citation:
                        row.update(fact_ids='FAIL' if citation.get('unknown_fact_ids') else 'PASS',
                                   unknown_ids=len(citation.get('unknown_fact_ids',[])),grounding='FAIL')
                    if getattr(error,'grounding_diagnostic',None): row['grounding']='FAIL'
                    if not row['wire_sends']:raise ValueError('Local failure before provider send: '+error.code) from None
                row['total_seconds']=perf_counter()-started;row['classification']=classify(row)
                budget.retry_after(row.get('retry_after'));budget.retry_after(row.get('retry_delay'))
                assert repo.profile_snapshot('IN','redistribution-ready').model_dump_json()==before
                assert not planner.results
                save();print(model,attempt,row['classification'],row['http_status'],round(row.get('provider_seconds',0),3),'seconds',flush=True)
                # Do not repeat an exhausted quota, invalid key or unsupported configuration.
                if row['accepted'] or row['http_status'] in (400,401,403,404,429):
                    if row['http_status']==429 and not row.get('model_specific_quota'):blocked=True
                    break
    finally:
        budget.finish();save()
    report['status']='STOPPED_PROVIDER_QUOTA_INSTRUCTION' if blocked else 'COMPLETED'
    if live:
        assert all(digest(ROOT/name)==sha for name,sha in protected.items()),'Frozen identity changed'
        assert json.loads(ledger.read_text())==budget.saved
        report['preservation']=dict(status='PASS',frozen_file_identities=len(protected),env_unchanged=True,
                                    production_fallback_unchanged=True,operational_models_federation_evidence_unchanged=True)
    save();return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true');parser.add_argument('--quota-confirmed',action='store_true')
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args()
    if args.live:
        with LEASE.open('x') as handle:handle.write('final-gemini-matrix')
        try:run(True,args.output,quota_confirmed=args.quota_confirmed)
        finally:LEASE.unlink()
    else:run(False,args.output)
