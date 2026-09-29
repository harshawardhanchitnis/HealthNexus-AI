"""The targeted fact verifier's wire counter and all-or-nothing smoke gate."""
import json
import sys
from pathlib import Path
import httpx
import pytest
from google import genai
from google.genai import types
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_fact_citations import Allowance,accepted,MODEL
from app.ai.client import GeminiTransport,CopilotError
from app.ai.config import AIConfig
from app.ai.facts import FactCatalogue
from app.ai.schemas import FactDraftAnswer


def ledger(tmp_path):
    path=tmp_path/'ledger.json';original={'day':'retained-original-day','used':23,
        'per_model':{MODEL:4,'legacy-unattributed':7,'gemini-3.8-flash':3},'extra_historical_metadata':'retained'}
    path.write_text(json.dumps(original));return path,original


def test_preflight_alone_does_not_append_a_provider_send(tmp_path):
    path,original=ledger(tmp_path);allowance=Allowance(path,tmp_path/'journal.json')
    allowance.preflight();assert json.loads(path.read_text())==original and allowance.used==0


def test_send_cap_is_global_and_preserves_every_historical_field(tmp_path):
    path,original=ledger(tmp_path);journal=tmp_path/'journal.json';allowance=Allowance(path,journal)
    allowance.record_send();allowance.record_send()
    expected=json.loads(json.dumps(original));expected['used']+=2;expected['per_model'][MODEL]+=2
    assert json.loads(path.read_text())==expected
    assert json.loads(journal.read_text())['historical_ledger']==original
    with pytest.raises(AssertionError):allowance.record_send()
    with pytest.raises(AssertionError):Allowance(path,journal)


@pytest.mark.parametrize('key',['schema_valid','fact_ids_valid','qualitative_evidence_valid','numeric_grounding_valid',
    'context_valid','http_status','unknown_fact_ids','unsupported_numeric_claims'])
def test_second_smoke_cannot_be_authorized_by_a_partial_pass(key):
    row=dict(schema_valid=True,fact_ids_valid=True,qualitative_evidence_valid=True,numeric_grounding_valid=True,
        context_valid=True,http_status=200,unknown_fact_ids=0,unsupported_numeric_claims=0)
    assert accepted(row)
    row[key]=503 if key=='http_status' else 1 if key in ('unknown_fact_ids','unsupported_numeric_claims') else False
    assert not accepted(row)


@pytest.mark.parametrize('status',[200,503])
def test_official_sdk_fact_schema_and_send_hook_count_exactly_one_wire_attempt(tmp_path,status):
    path,original=ledger(tmp_path);allowance=Allowance(path,tmp_path/'journal.json')
    catalog=FactCatalogue('0123456789abcdef')
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':'2026-09-27'},
        'summary':{'bed_utilisation':79.8}}
    envelope=catalog.envelope('e1','get_network_summary',payload,summary_only=True)
    fact=next(f for f in envelope['facts'] if f['label']=='Summary / Bed utilisation');sent=[]
    def handle(request):
        body=json.loads(request.content);sent.append(body)
        assert body['response_format']['schema']['properties']['situation']['properties']['evidence_refs']['items']['enum']==list(catalog.facts)
        if status==503:return httpx.Response(503,json={'error':{'code':503,'message':'Mock high demand','status':'UNAVAILABLE'}})
        text=json.dumps({'situation':{'text':'Bed utilisation reflects operational pressure.','evidence_refs':[fact['fact_id']]}})
        return httpx.Response(200,json={'id':'mock-wire-fact','status':'completed','model':MODEL,
            'steps':[{'type':'model_output','content':[{'type':'text','text':text}]}]})
    transport=GeminiTransport(AIConfig(api_key='unit-test-placeholder',model=MODEL,same_model_attempts=1))
    transport.client.close();transport.client=genai.Client(api_key='unit-test-placeholder',http_options=types.HttpOptions(
        client_args={'transport':httpx.MockTransport(handle)},retry_options=types.HttpRetryOptions(attempts=0)))
    transport.before_request=allowance.preflight
    transport.client.interactions.sdk_configuration.client.event_hooks.setdefault('request',[]).append(lambda _:allowance.record_send())
    body=dict(model=MODEL,input=json.dumps({'server_prefetched_evidence':[envelope]}),
        response_format={'type':'text','mime_type':'application/json','schema':catalog.schema()})
    try:
        if status==503:
            with pytest.raises(CopilotError):transport.create(**body)
        else:
            result=transport.create(**body);draft=FactDraftAnswer.model_validate_json(result['output_text'])
            assert catalog.validate(draft,{'e1':{'tool':'get_network_summary','payload':payload}})[1][0].value==79.8
    finally:transport.close()
    assert len(sent)==transport.provider_requests==allowance.used==1
    expected=json.loads(json.dumps(original));expected['used']+=1;expected['per_model'][MODEL]+=1
    assert json.loads(path.read_text())==expected
