"""Stage budgets and one-send final acceptance. No live provider calls."""
from copy import deepcopy
from dataclasses import replace
import json
import sys
from pathlib import Path
import pytest
import httpx
from google import genai
from google.genai import types
from app.ai.config import AIConfig,DEFAULT_CHAIN
from app.ai.client import CopilotError,GeminiTransport
from app.ai.failover import FailoverSession
from app.ai.facts import FactCatalogue
from app.ai.schemas import CopilotRequest
from app.ai.system_prompt import SYSTEM,SYNTHESIS
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_positive_final import (OneSendBudget,MODEL,synthesis_body,validate_final,mock_draft)
from test_ai_failover import Failing,unavailable
from test_ai import Scripted


def prepared():
    req=CopilotRequest(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',
        message='Explain the advisory plan.',allow_planning=True)
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':'2026-09-27'},
        'solver':{'status':'OPTIMAL'},'safe_capacity':17745,
        'impact':{'transferred_units':15679,'after':{'target_deficit':26084}}}
    records={'e2':{'tool':'optimize_redistribution','payload':payload,
        'request_scope':{'state_id':'MH','district_id':'MH-PUNE','facility_id':None}}}
    catalog=FactCatalogue();envelope=catalog.envelope('e2','optimize_redistribution',payload)
    return req,catalog,records,[envelope]


def result(catalog,**changes):
    return {'id':'test-final','status':'completed','output_text':json.dumps(mock_draft(catalog)),**changes}


def test_stage_defaults_and_server_owned_bounds():
    cfg=AIConfig(api_key='test')
    assert cfg.generation()=={'thinking_level':'medium','max_output_tokens':2400}
    assert cfg.generation(True)=={'thinking_level':'low','max_output_tokens':4096}
    assert cfg.chain==DEFAULT_CHAIN
    req,catalog,records,envelopes=prepared()
    body=synthesis_body(cfg,req,catalog,envelopes)
    assert body['system_instruction']==SYSTEM+SYNTHESIS
    assert 'tools' not in body and 'previous_interaction_id' not in body
    assert body['generation_config']==cfg.generation(True)
    assert body['response_format']['schema']==catalog.schema()


def test_invalid_synthesis_setting_fails_configuration(monkeypatch):
    monkeypatch.setenv('GEMINI_SYNTHESIS_THINKING_LEVEL','invented')
    assert AIConfig(api_key='test').error()[0]=='thinking_configuration'


@pytest.mark.parametrize('final',[False,True])
def test_failover_preserves_stage_budget_with_fresh_handoff(final):
    made=[]
    def factory(cfg):
        fake=Failing(unavailable()) if not made else Scripted([{'id':'connected'}])
        made.append(fake);return fake
    cfg=AIConfig(api_key='test')
    session=FailoverSession(cfg,factory,lambda:json.dumps({'validated_local_evidence':True}))
    try:
        body={'input':'Original question','previous_interaction_id':'old-model-id',
            'generation_config':{'thinking_level':'high','max_output_tokens':99999}}
        if final:body['response_format']={'type':'text','mime_type':'application/json'}
        session.create(**body)
        assert all(t.bodies[0]['generation_config']==cfg.generation(final) for t in made)
        assert 'previous_interaction_id' not in made[1].bodies[0]
        assert session.effective_model==DEFAULT_CHAIN[1]
    finally:session.close()


@pytest.mark.parametrize('model',[MODEL,'gemini-3.6-flash'])
@pytest.mark.parametrize('provider_id',['sdk-final',''])
def test_official_sdk_complete_compact_final_uses_low_4096(model,provider_id):
    req,catalog,records,envelopes=prepared();cfg=AIConfig(api_key='unit-test-placeholder',model=model,same_model_attempts=1)
    sent=[]
    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200,json={'id':provider_id,'status':'completed','model':model,
            'steps':[{'type':'model_output','content':[{'type':'text','text':json.dumps(mock_draft(catalog))}]}]})
    transport=GeminiTransport(cfg);transport.client.close()
    transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handler)}))
    try:
        response=transport.create(**synthesis_body(cfg,req,catalog,envelopes))
        resolved,evidence,audits=validate_final(response,catalog,records,req,'2026-09-27')
        assert len(sent)==1 and transport.provider_requests==1
        assert sent[0]['generation_config']=={'thinking_level':'low','max_output_tokens':4096}
        assert len(audits)==4 and evidence and resolved.remaining_gaps
        assert not any(a['unknown_fact_ids'] for a in audits)
    finally:transport.close()


@pytest.mark.parametrize('status',['incomplete','failed','requires_action',None])
def test_noncompleted_final_rejected(status):
    req,catalog,records,_=prepared()
    with pytest.raises(CopilotError) as error:
        validate_final(result(catalog,status=status),catalog,records,req,'2026-09-27')
    assert error.value.code=='response_incomplete'


@pytest.mark.parametrize('output',['{"situation":','not JSON','{}'])
def test_truncated_or_invalid_json_rejected(output):
    req,catalog,records,_=prepared()
    with pytest.raises(CopilotError) as error:
        validate_final(result(catalog,output_text=output),catalog,records,req,'2026-09-27')
    assert error.value.code=='response_schema'


@pytest.mark.parametrize('text',[
    'The optimizer completed with an optimal status, executing safe transfers across donor facilities.',
    'Despite executing authorized transfers, unresolved resource need remains.',
    'Execute safe transfers to relieve pressure.',
])
def test_physical_execution_claims_rejected_in_final_acceptance(text):
    req,catalog,records,_=prepared();draft=mock_draft(catalog)
    draft['recommended_actions'][0]['text']=text
    if 'optimal' in text:
        draft['recommended_actions'][0]['evidence_refs'].append(next(f.fact_id for f in catalog.facts.values() if f.path=='solver.status'))
    with pytest.raises(CopilotError) as error:
        validate_final(result(catalog,output_text=json.dumps(draft)),catalog,records,req,'2026-09-27')
    assert error.value.code=='verification_physical_execution'


@pytest.mark.parametrize('change',['unknown','stale','unsupported_number','full_resolution'])
def test_final_contract_not_weakened(change):
    req,catalog,records,_=prepared();draft=mock_draft(catalog)
    if change=='unknown':draft['situation']['evidence_refs']=['unknown-fact-id']
    if change=='stale':
        other=FactCatalogue();other.envelope('e2','optimize_redistribution',records['e2']['payload'])
        draft['situation']['evidence_refs']=mock_draft(other)['situation']['evidence_refs']
    if change=='unsupported_number':draft['key_risks'][0]['text']='Safe donor capacity is 17744 inventory items.'
    if change=='full_resolution':draft['remaining_gaps'][0]['text']='The network is fully resilient; no shortages remain.'
    with pytest.raises(CopilotError):
        validate_final(result(catalog,output_text=json.dumps(draft)),catalog,records,req,'2026-09-27')


def test_budget_appends_one_actual_send_and_preserves_history(tmp_path):
    ledger=tmp_path/'ledger.json';journal=tmp_path/'journal.json'
    original={'day':'2026-09-28','used':28,'per_model':{MODEL:9,'other':19},'extra':'keep'}
    ledger.write_text(json.dumps(original));budget=OneSendBudget(ledger,journal)
    budget.preflight();assert json.loads(ledger.read_text())==original and not journal.exists()
    with pytest.raises(CopilotError):budget.record_send('gemini-3.6-flash')
    assert json.loads(ledger.read_text())==original
    budget.record_send(MODEL)
    expected=deepcopy(original);expected['used']=29;expected['per_model'][MODEL]=10
    assert json.loads(ledger.read_text())==expected
    assert json.loads(journal.read_text())['historical_ledger']==original
    with pytest.raises(CopilotError):budget.record_send(MODEL)
    with pytest.raises(CopilotError):OneSendBudget(ledger,journal)
    assert json.loads(ledger.read_text())==expected


def test_replay_blocked_by_journal_even_if_old_ledger_restored(tmp_path):
    ledger=tmp_path/'ledger.json';journal=tmp_path/'journal.json'
    ledger.write_text(json.dumps({'day':'old','used':28,'per_model':{MODEL:9}}))
    journal.write_text('{}')
    with pytest.raises(CopilotError):OneSendBudget(ledger,journal)


def test_sdk_generated_type_explicitly_defines_low():
    from google.genai._gaos.types.interactions.generationconfig import GenerationConfigParam
    from google.genai._gaos.types.interactions.thinkinglevel import ThinkingLevel
    assert 'thinking_level' in GenerationConfigParam.__annotations__
    assert 'low' in str(ThinkingLevel)
