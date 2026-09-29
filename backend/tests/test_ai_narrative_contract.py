"""Ordinary narratives exclude statuses; explicit status questions remain grounded."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_phase6_completion import CompletionBudget,MODEL,old_failures,MAX_SENDS
from app.ai.synthesis import provider_view,synthesis_input,instruction,status_topics,validate_narrative
from app.ai.client import CopilotError
from app.ai.action_state import advisory_state
from app.ai.schemas import CopilotRequest,FactDraftAnswer
from app.ai.facts import FactCatalogue
from test_profiles import profiles,trained


def setup(message='Explain the recommended plan and remaining shortages.'):
    req=CopilotRequest(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',message=message)
    records={'e1':{'tool':'get_optimization_result','payload':{
        'context':{'country_id':'IN','profile':'redistribution-ready','origin':'2026-09-27'},
        'solver':{'status':'OPTIMAL'},'action_state':advisory_state(),'safe_capacity':17745,
        'capacity_by_resource':{'IVF':200},'transfers':[],
        'impact':{'transferred_units':15679,'after':{'target_deficit':26084}}}}}
    catalog=FactCatalogue();catalog.envelope('e1',records['e1']['tool'],records['e1']['payload'])
    return req,records,catalog


def draft(catalog,text,paths=('action_state.plan_mode',)):
    ids=[next(f.fact_id for f in catalog.facts.values() if f.path==p) for p in paths]
    return FactDraftAnswer.model_validate({'situation':{'text':text,'evidence_refs':ids}})


@pytest.mark.parametrize('text',[
    'The advisory plan recommends redistribution.',
    'The proposed redistribution identifies safe donor capacity while substantial shortages remain.',
    'Recommended transfer lanes could reduce resource pressure, but the district retains unresolved demand.',
    'The plan is advisory.',
])
def test_required_safe_language_passes_existing_facts_and_new_narrative_guard(text):
    req,records,catalog=setup()
    resolved,_,_=catalog.validate(draft(catalog,text,('action_state.plan_mode','safe_capacity','impact.after.target_deficit')),records,req,'2026-09-27')
    validate_narrative(resolved,req,records)


def test_full_authoritative_statuses_and_original_catalogue_remain_immutable():
    req,records,catalog=setup();before=deepcopy((catalog.facts,catalog.envelopes,records))
    views,schema=provider_view(catalog,req)
    ids=schema['properties']['situation']['properties']['evidence_refs']['items']['enum']
    paths={catalog.facts[fid].path for fid in ids}
    assert 'action_state.plan_mode' in paths and 'safe_capacity' in paths
    assert 'solver.status' not in paths and 'action_state.physical_execution' not in paths and 'action_state' not in paths
    assert all('result' not in v for v in views)
    assert before==(catalog.facts,catalog.envelopes,records)
    assert records['e1']['payload']['solver']['status']=='OPTIMAL'
    assert records['e1']['payload']['action_state']==advisory_state()


@pytest.mark.parametrize('question',[
    'Have these transfers been executed?', 'Was the plan authorized?', 'Did hospitals approve the plan?',
    'What is the transfer status?', 'Were resources moved?', 'Have hospitals been contacted?',
])
def test_direct_action_questions_get_current_authoritative_status_facts(question):
    req,records,catalog=setup(question);views,_=provider_view(catalog,req)
    ids={f['fact_id'] for f in views[0]['facts']};paths={catalog.facts[fid].path for fid in ids}
    assert 'action_state.physical_execution' in paths and 'action_state.externally_authorized' in paths
    assert 'solver.status' not in paths
    assert status_topics(req)['action'] and 'EXPLICIT STATUS QUESTION' in instruction(req)


def test_direct_solver_question_is_allowed_with_unchanged_scalar_status_citation():
    req,records,catalog=setup('What status did the solver return?')
    views,_=provider_view(catalog,req)
    assert any(catalog.facts[f['fact_id']].path=='solver.status' for f in views[0]['facts'])
    resolved,_,_=catalog.validate(draft(catalog,'The solver returned OPTIMAL.',('solver.status',)),records,req,'2026-09-27')
    validate_narrative(resolved,req,records)


def test_direct_action_question_can_state_cited_false_status_but_never_fabricate_execution():
    req,records,catalog=setup('Have these transfers been executed?')
    resolved,_,_=catalog.validate(draft(catalog,'These transfers have not been physically executed.',('action_state.physical_execution',)),records,req,'2026-09-27')
    validate_narrative(resolved,req,records)
    with pytest.raises(CopilotError):catalog.validate(draft(catalog,'These transfers were executed.',('action_state.physical_execution',)),records,req,'2026-09-27')


@pytest.mark.parametrize('text,path',[
    ('The solver returned OPTIMAL.','solver.status'),
    ('The advisory plan is optimal.','solver.status'),
    ('These transfers have not been physically executed.','action_state.physical_execution'),
    ('No hospital approved these transfers.','action_state.externally_authorized'),
])
def test_correct_status_still_not_requested_in_ordinary_narrative(text,path):
    req,records,catalog=setup()
    data=draft(catalog,text,(path,'action_state.plan_mode'))
    resolved,_,_=catalog.validate(data,records,req,'2026-09-27')
    with pytest.raises(CopilotError) as e:validate_narrative(resolved,req,records)
    assert e.value.code=='narrative_scope'


def test_native_result_continuation_keeps_actual_call_id_and_supplies_current_evidence_only():
    req,records,catalog=setup();envelope=catalog.envelopes['e1']
    raw=[{'type':'function_result','name':'get_optimization_result','call_id':'opaque-native-call',
        'result':[{'type':'text','text':json.dumps(envelope)}]}]
    transformed,_=synthesis_input(catalog,req,raw)
    assert transformed[0]['call_id']=='opaque-native-call'
    view=json.loads(transformed[0]['result'][0]['text'])
    assert view['current_evidence_catalogue'] and 'result' not in view
    assert json.loads(raw[0]['result'][0]['text'])==envelope


def test_fresh_request_uses_fresh_ids_without_path_repair():
    req,records,catalog=setup();other=FactCatalogue();other.envelope('e1','get_optimization_result',records['e1']['payload'])
    assert not set(catalog.facts)&set(other.facts)
    with pytest.raises(CopilotError):catalog.validate(draft(other,'The plan is advisory.'),records,req,'2026-09-27')


def test_all_three_exact_old_failed_phrases_remain_rejected():
    assert all(x['status']=='REJECTED' for x in old_failures())


def budget(tmp_path):
    old={'day':'retained-original-day','used':30,'per_model':{MODEL:11,'other':19},'extra':'retain'}
    path=tmp_path/'ledger.json';path.write_text(json.dumps(old));journal=tmp_path/'journal.json'
    return CompletionBudget(path,journal),path,journal,old


def test_six_send_budget_is_global_preserves_history_and_cannot_replay(tmp_path):
    b,path,journal,old=budget(tmp_path)
    b.preflight();assert json.loads(path.read_text())==old and not journal.exists()
    for label in ('positive','positive','positive','followup','constrained','provenance'):b.record_send(MODEL,label)
    expected=deepcopy(old);expected['used']=36;expected['per_model'][MODEL]=17
    assert json.loads(path.read_text())==expected
    saved=json.loads(journal.read_text());assert saved['historical_ledger']==old
    assert saved['sends_per_case']=={'positive':3,'followup':1,'constrained':1,'provenance':1}
    with pytest.raises(CopilotError):b.record_send(MODEL,'extra')
    with pytest.raises(CopilotError):CompletionBudget(path,journal)
    path.write_text(json.dumps(old))
    with pytest.raises(CopilotError):CompletionBudget(path,journal)


def test_budget_rejects_other_models_and_terminal_run(tmp_path):
    b,path,journal,old=budget(tmp_path)
    with pytest.raises(CopilotError):b.record_send('gemini-3.6-flash','positive')
    assert json.loads(path.read_text())==old and not journal.exists()
    b.record_send(MODEL,'positive');b.stop()
    assert json.loads(journal.read_text())['terminal'] is True
    with pytest.raises(CopilotError):b.record_send(MODEL,'followup')


def test_pacing_is_bounded_and_does_not_change_send_accounting(tmp_path,monkeypatch):
    import verify_phase6_completion as verifier
    b,path,journal,old=budget(tmp_path);wait=[]
    monkeypatch.setattr(verifier,'monotonic',lambda:100.)
    monkeypatch.setattr(verifier,'sleep',wait.append)
    b.record_send(MODEL,'positive');b.preflight()
    assert wait==[20.] and json.loads(path.read_text())['used']==31


def test_no_global_status_word_ban_for_non_plan_provenance():
    req,records,catalog=setup('Explain the data provenance.')
    records['e1']['tool']='get_data_provenance'
    validate_narrative(draft(catalog,'The solver metadata and execution state are server owned.'),req,records)


def test_explicit_solver_words_still_need_exact_scalar_status_reference():
    req,records,catalog=setup('What did the solver return?')
    resolved,_,_=catalog.validate(draft(catalog,'The solver returned a recommendation.',('safe_capacity','action_state.plan_mode')),records,req,'2026-09-27')
    with pytest.raises(CopilotError) as e:validate_narrative(resolved,req,records)
    assert e.value.code=='solver_terminology'


@pytest.mark.parametrize('message,text,field,passes',[
    ('Explain the recommended plan.','The plan remains advisory.','action_state.plan_mode',True),
    ('Have these transfers been executed?','These transfers have not been physically executed.','action_state.physical_execution',True),
    ('Explain the recommended plan.','Resources were moved.','safe_capacity',False),
])
def test_production_preserves_exact_raw_draft_on_success_and_rejection(profiles,message,text,field,passes):
    from test_ai import service,Scripted,final,turn,call
    from verify_gemini import fixture
    from frame_fixture import mock_frame
    class FrameScripted(Scripted):
        def create(self,**body):
            if 'response_format' not in body:return super().create(**body)
            self.bodies.append(body);frame=mock_frame(body)
            if not passes:next(iter(frame['claims'].values()))['text']=text
            return {'id':'frame-final','status':'completed','output_text':json.dumps(frame)}
    fake=FrameScripted([])
    svc,repo=service(profiles,lambda _:fake)
    snapshot=repo.profile_snapshot('BR','redistribution-ready');state=snapshot.facilities[0].state_id
    sid,rid=fixture(svc,repo,'redistribution-ready',country='BR',state=state,district=None)
    fake.turns=iter([turn([call('get_optimization_result',{'country_id':'BR','profile':'redistribution-ready','state_id':state,'run_id':rid})]),final(text,field)])
    req=CopilotRequest(country_id='BR',profile='redistribution-ready',state_id=state,
        message=message,scenario_id=sid,optimization_run_id=rid)
    if passes:
        response=svc.run(repo,req);assert response.metadata['prose_author']=='HealthNexus deterministic renderer'
        assert svc.audit[-1]['server_rendered_claims']['situation']['text']==response.answer
    else:
        with pytest.raises(CopilotError) as e:svc.run(repo,req)
        assert e.value.code=='response_schema'
        legacy_req,legacy_records,legacy_cat=setup(message)
        with pytest.raises(CopilotError) as old:legacy_cat.validate(draft(legacy_cat,text,('safe_capacity',)),legacy_records,legacy_req,'2026-09-27')
        assert old.value.code=='unsafe_claim'
    raw=svc.audit[-1]['provider_draft']
    assert 'claims' in json.loads(raw)
    if not passes:assert next(iter(json.loads(raw)['claims'].values()))['text']==text
    else:assert all('text' not in c for c in json.loads(raw)['claims'])
    assert svc.audit[-1]['provider_semantic_frame']==raw
    assert next(reversed(svc.requests.values()))['provider_draft']==raw
    assert 'tools' not in fake.bodies[-1] and fake.bodies[-1]['store'] is True


@pytest.mark.parametrize('fault,code,sends',[('429','rate_limited',1),('503','provider_unavailable',1),('unsafe_final','response_schema',3)])
def test_official_sdk_stop_after_any_failure_keeps_raw_draft_no_retry_no_next_case(tmp_path,fault,code,sends):
    from verify_phase6_completion import run
    report=run(False,mock_fault=fault,output=tmp_path/'fault.json')
    assert report['status']=='STOPPED_AFTER_FAILURE' and report['new_provider_requests']==0
    assert len(report['tests'])==1 and report['tests'][0]['error_code']==code
    assert report['mock_http_sends']==sends and report['retries']==report['fallbacks']==0
    if fault=='unsafe_final':
        raw=report['tests'][0]['provider_attempts'][-1]['raw_provider_draft']
        assert 'Resources were moved.' in raw
        assert next(iter(json.loads(raw)['claims'].values()))['text']=='Resources were moved.'
