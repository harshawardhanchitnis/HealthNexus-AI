"""Exact request-local numeric evidence; no provider calls or engine changes."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.ai.citations import build_evidence
from app.ai.client import CopilotError
from app.ai.schemas import DraftAnswer
from app.ai.protocol import model_record
from app.ai.system_prompt import SYSTEM
from test_profiles import profiles, trained
from test_ai import service, request
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_gemini import DemoTransport


def records(**values):
    return {'e1':{'tool':'get_network_summary','payload':{
        'context':{'country_id':'IN','profile':'redistribution-ready','origin':'2026-09-27'},
        'summary':values,'model_version':'saved-test-model'}}}


def draft(text, field='summary.value', eid='e1'):
    return DraftAnswer.model_validate({'situation':{'text':text,
        'references':[{'evidence_id':eid,'field':field}]}})


@pytest.mark.parametrize('value,text,accepted',[
    (3,'There are 999 facilities.',False),
    (3,'There are 3 facilities.',True),
    (15679,'The plan recommends 15,679 accounting items.',True),
    (37.5428010439863,'The resolved fraction is 37.5.',False),
    (37.5428010439863,'The resolved fraction is 37.5428010439863.',True),
    (3.079865,'WAPE is 3.08.',False),
    (3.079865,'WAPE is 3.079865.',True),
    (0,'There are 0 transfers.',True),
    (0,'There are 0.0 transfers.',True),
    (-7.25,'The change is -7.25.',True),
    (-7.25,'The change is 7.25.',False),
    (7.25,'The change is -7.25.',False),
    (1000,'The quantity is 1e3.',True),
    (0.125,'The fraction is .125.',True),
    (0.125,'The fraction is .13.',False),
    (0.125,'The fraction is -.125.',False),
    (-0.125,'The fraction is -.125.',True),
    (3,'The report says COVID19.',False),
    (0.125,'The fraction is 12.5 percent.',False),
    (0.125,'The fraction is 0.125%.',False),
    (0.125,'The fraction is 0.125.',True),
    (0.0895,'Forecast accuracy is 91.05%.',False),
    (0.0895,'Forecast accuracy is 0.0895%.',False),
])
def test_exact_numeric_claims(value,text,accepted):
    if accepted:
        assert build_evidence(draft(text),records(value=value))[0].value==value
    else:
        with pytest.raises(CopilotError) as error: build_evidence(draft(text),records(value=value))
        assert error.value.code=='unsupported_number'


@pytest.mark.parametrize('text',['Medicine availability is 66.7%.','Medicine availability is 66.7 percent.'])
def test_existing_server_percentage_can_be_quoted(text):
    assert build_evidence(draft(text,'summary.medicine_availability'),
        records(medicine_availability=66.7))[0].value==66.7


def test_derived_fact_requires_actual_server_field():
    source=records(transferred=15679,target=41763)
    with pytest.raises(CopilotError):
        build_evidence(draft('The resolved share is 37.5428010439863%.','summary.transferred'),source)
    source['e1']['payload']['impact']={'percent_deficit_resolved':37.5428010439863}
    assert build_evidence(draft('The resolved share is 37.5428010439863%.',
        'impact.percent_deficit_resolved'),source)[0].value==37.5428010439863


def test_uncited_and_wrong_path_values_remain_rejected():
    source=records(value=2,other=3)
    with pytest.raises(CopilotError) as error:build_evidence(draft('There are 3 facilities.'),source)
    assert error.value.code=='unsupported_number'
    with pytest.raises(CopilotError) as error:build_evidence(draft('There are 3 facilities.','summary.absent'),source)
    assert error.value.code=='evidence_invalid'


def test_dotted_identifier_cannot_hide_an_unsupported_numeric_segment():
    with pytest.raises(CopilotError) as error:
        build_evidence(draft('The model version is v3.8.123.'),records(value='v3.8.0'))
    assert error.value.code=='unsupported_number'


def test_duplicate_values_do_not_merge_evidence_identity():
    source=records(value=3)
    source['e2']={'tool':'get_warning_summary','payload':{
        'context':source['e1']['payload']['context'],'summary':{'total':3}}}
    answer=build_evidence(draft('There are 3 warnings.','summary.total','e2'),source)
    assert answer[0].evidence_id=='e2' and answer[0].tool=='get_warning_summary'
    with pytest.raises(CopilotError):build_evidence(draft('There are 3 warnings.','summary.total','e1'),source)


@pytest.mark.parametrize('country,profile',[('BR','redistribution-ready'),('IN','constrained')])
def test_cross_context_evidence_is_rejected(country,profile):
    source=records(value=3)
    source['e1']['payload']['context'].update(country_id=country,profile=profile)
    context=SimpleNamespace(country_id='IN',profile='redistribution-ready',compare_profiles=False)
    with pytest.raises(CopilotError) as error:
        build_evidence(draft('There are 3 facilities.'),source,context=context)
    assert error.value.code=='evidence_invalid'


def test_authorized_profile_comparison_keeps_country_boundary():
    source=records(value=3);source['e1']['payload']['context']['profile']='constrained'
    context=SimpleNamespace(country_id='IN',profile='redistribution-ready',compare_profiles=True)
    assert build_evidence(draft('There are 3 facilities.'),source,context=context)[0].profile=='constrained'
    source['e1']['payload']['context']['country_id']='BR'
    with pytest.raises(CopilotError):build_evidence(draft('There are 3 facilities.'),source,context=context)


def test_rejection_diagnostic_preserves_exact_claim_and_references():
    source=records(value=37.5428010439863)
    with pytest.raises(CopilotError) as error:build_evidence(draft('The share is 37.5.'),source)
    diagnostic=error.value.grounding_diagnostic
    assert diagnostic['claim_field']=='situation.text'
    assert diagnostic['claim_text']=='The share is 37.5.'
    assert diagnostic['unsupported_numbers']==['37.5']
    assert diagnostic['references'][0]['field']=='summary.value'
    assert diagnostic['references'][0]['value']==37.5428010439863


def test_model_numeric_catalog_is_exact_bounded_and_resolvable():
    payload=records(value=3,medicine_availability=66.7)['e1']['payload']
    row=model_record('e1','get_network_summary',payload)
    facts={f['path']:f for f in row['numeric_facts']}
    assert facts['summary.value']['value']==3 and facts['summary.medicine_availability']['unit']=='%'
    assert facts['summary.medicine_availability']['quote']=='66.7'
    assert facts['summary.value']['evidence_id']=='e1'
    assert facts['summary.value']['provenance']['origin']=='2026-09-27'
    assert len(model_record('e1','test',{'values':list(range(200))})['numeric_facts'])<=32


def test_catalog_never_converts_fraction_or_rounds():
    row=model_record('e1','get_model_performance',{'targets':{'medicine':{
        'models':{'actual-model':{'test':{'wape':0.03079865}}}}}})
    fact=row['numeric_facts'][0]
    assert fact['value']==0.03079865 and fact['quote']=='0.03079865'
    assert fact['unit']=='WAPE fraction' and '3.08' not in json.dumps(row)
    assert 'Do not calculate, estimate, round, derive, convert or infer' in SYSTEM


def test_original_unit_is_retained_without_conversion():
    source=records(value=7);source['e1']['payload']['unit']='bags'
    answer=build_evidence(draft('The proposed quantity is 7 bags.'),source)
    assert answer[0].value==7 and answer[0].unit=='bags'


def test_same_country_profile_cannot_reuse_another_geography():
    source=records(value=3);source['e1']['request_scope']={'district_id':'OTHER'}
    context=SimpleNamespace(country_id='IN',profile='redistribution-ready',district_id='MH-PUNE',compare_profiles=False)
    with pytest.raises(CopilotError):build_evidence(draft('There are 3 facilities.'),source,context=context)


def test_origin_and_request_local_evidence_id_are_not_reused():
    source=records(value=3)
    with pytest.raises(CopilotError):build_evidence(draft('There are 3 facilities.'),source,origin='2026-09-28')
    with pytest.raises(CopilotError):build_evidence(draft('There are 3 facilities.',eid='previous-request-e1'),source)


def test_api_key_pattern_is_redacted_in_diagnostic():
    key='AIza'+'x'*35
    with pytest.raises(CopilotError) as error:build_evidence(draft(f'{key}: there are 999 facilities.'),records(value=3))
    assert key not in json.dumps(error.value.grounding_diagnostic)


def test_targeted_verifier_preserves_global_budget_and_has_no_reset():
    from verify_numeric_grounding import Allowance
    allowance=Allowance(live=False)
    allowance.consume();allowance.consume()
    assert allowance.initial==22 and allowance.saved['used']==24
    assert allowance.saved['per_model']=={'gemini-3.5-flash-lite':2}
    with pytest.raises(AssertionError):allowance.consume()
    assert allowance.used==2


def test_targeted_verifier_refuses_replay_without_touching_ledger(tmp_path,monkeypatch):
    import verify_numeric_grounding as verifier
    ledger=tmp_path/'ledger.json';journal=tmp_path/'journal.json'
    content=json.dumps({'day':'retained-day','used':22,'per_model':{'legacy-unattributed':7}})
    ledger.write_text(content);journal.write_text('{}')
    monkeypatch.setattr(verifier,'LEDGER',ledger);monkeypatch.setattr(verifier,'JOURNAL',journal)
    with pytest.raises(AssertionError):verifier.Allowance(live=True)
    assert ledger.read_text()==content


@pytest.mark.parametrize('tamper',[False,True])
def test_post_smoke_mock_preservation_checks_original_ledger(tmp_path,monkeypatch,tamper):
    import hashlib
    import verify_numeric_grounding as verifier
    folder=tmp_path/'artifacts';folder.mkdir()
    ledger=folder/'gemini-verification-budget-live.json';journal=folder/'phase6-numeric-live-sends.json'
    original={'day':'retained-day','used':22,'per_model':{'legacy-unattributed':7,'gemini-3.5-flash-lite':3}}
    digest=hashlib.sha256(json.dumps(original).encode()).hexdigest()
    (folder/'phase6-grounding-preservation-before.json').write_text(json.dumps({
        'artifacts/gemini-verification-budget-live.json':digest}))
    updated=json.loads(json.dumps(original));updated['used']+=1;updated['per_model']['gemini-3.5-flash-lite']+=1
    if tamper:updated['per_model']['legacy-unattributed']-=1
    ledger.write_text(json.dumps(updated));journal.write_text(json.dumps({
        'initial_historical_requests':22,'authorized_maximum_new_requests':2,'new_provider_requests':1}))
    monkeypatch.setattr(verifier,'ROOT',tmp_path);monkeypatch.setattr(verifier,'LEDGER',ledger)
    monkeypatch.setattr(verifier,'JOURNAL',journal)
    if tamper:
        with pytest.raises(AssertionError):verifier.preserved()
    else:assert verifier.preserved()['unchanged']==0


@pytest.mark.parametrize('model',['gemini-3.5-flash-lite','gemini-3.6-flash'])
def test_live_capable_models_share_mock_grounding_contract(profiles,model):
    fake=DemoTransport(None);svc,repo=service(profiles,lambda _:fake,model=model,failover_enabled=False)
    response=svc.run(repo,request().model_copy(update={
        'message':'Summarize the current resource resilience status in Pune.'}))
    assert response.metadata['provider_requests']==1 and response.metadata['local_tool_calls']==2
    assert response.evidence and response.metadata['effective_model']==model
    input_data=json.loads(fake.bodies[0]['input'])
    assert all(e['numeric_facts'] for e in input_data['server_prefetched_evidence'])
