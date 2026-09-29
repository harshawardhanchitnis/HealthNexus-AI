"""Authoritative action-state semantics, exact numbers, no live provider calls."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError
from app.ai.action_state import advisory_state,PlanActionState,check_action_claim,normalize
from app.ai.facts import FactCatalogue
from app.ai.client import CopilotError
from app.ai.schemas import FactDraftAnswer,CopilotRequest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_advisory_final import AdvisoryBudget,MODEL,old_failure,validate


def setup():
    req=CopilotRequest(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',message='Explain plan',allow_planning=True)
    payload={'context':{'country_id':'IN','profile':'redistribution-ready','origin':'2026-09-27'},
        'action_state':advisory_state(),'solver':{'status':'OPTIMAL'},'safe_capacity':17745,
        'impact':{'transferred_units':15679,'transfer_count':10,'after':{'target_deficit':26084},
            'donor_safety_violations':0,'new_donor_risks':0}}
    records={'e1':{'tool':'optimize_redistribution','payload':payload,
        'request_scope':{'state_id':'MH','district_id':'MH-PUNE','facility_id':None}}}
    catalog=FactCatalogue();catalog.envelope('e1','optimize_redistribution',payload)
    return req,records,catalog


def draft(catalog,text,paths=('action_state.plan_mode',)):
    ids=[next(f.fact_id for f in catalog.facts.values() if f.path==p) for p in paths]
    return FactDraftAnswer.model_validate({'situation':{'text':text,'evidence_refs':ids}})


@pytest.mark.parametrize('text,paths',[
    ('recommended transfers',('action_state.plan_mode',)),
    ('proposed redistribution',('action_state.plan_mode',)),
    ('10 transfer lanes',('impact.transfer_count',)),
    ('The optimizer returned OPTIMAL.',('solver.status',)),
    ('15,679 accounting items are recommended for redistribution.',('impact.transferred_units','action_state.plan_mode')),
    ('Safe redistribution reduces pressure.',('impact.transferred_units','action_state.plan_mode')),
    ('The plan leaves shortages unresolved.',('impact.after.target_deficit',)),
    ('HealthNexus recommends redistributing resources across 10 lanes.',('impact.transfer_count','action_state.plan_mode')),
    ('The advisory plan allocates 15,679 accounting items.',('impact.transferred_units','action_state.plan_mode')),
    ('The optimizer identifies a safe redistribution plan.',('safe_capacity',)),
    ('The proposed transfers reduce pressure while leaving shortages unresolved.',('impact.after.target_deficit','action_state.plan_mode')),
    ('These transfers are recommendations and have not been physically executed.',('action_state.physical_execution','action_state.plan_mode')),
    ('No resources were moved.',('action_state.physical_execution',)),
    ("The hospitals haven't authorized the transfer.",('action_state.externally_authorized',)),
    ('No hospital was contacted.',('action_state.hospital_contacted',)),
    ('The optimizer completed with status OPTIMAL.',('solver.status',)),
    ('The plan does not eliminate all shortages.',('impact.after.target_deficit',)),
    ('There is no physical execution of these transfers.',('action_state.physical_execution',)),
    ('The transfer status is not_executed.',('action_state.real_world_transfer_status',)),
    ('No transfers were completed and no hospital was contacted.',('action_state.physical_execution','action_state.hospital_contacted')),
    ('Nothing was physically moved.',('action_state.physical_execution',)),
    ('The optimization completed.',('solver.status',)),
])
def test_allowed_matrix_through_unchanged_fact_and_numeric_validation(text,paths):
    req,records,catalog=setup()
    resolved,evidence,audits=catalog.validate(draft(catalog,text,paths),records,req,'2026-09-27')
    assert resolved.situation.text==text and evidence and not any(a['unknown_fact_ids'] for a in audits)


@pytest.mark.parametrize('text,paths',[
    ('executed transfers',('action_state.plan_mode',)),
    ('transfers were completed',('action_state.plan_mode',)),
    ('resources were moved',('action_state.physical_execution',)),
    ('plan was authorized',('action_state.externally_authorized',)),
    ('hospital approved the transfer',('action_state.externally_authorized',)),
    ('OPTIMAL means transfers were executed.',('solver.status',)),
    ('15,679 accounting items were redistributed.',('impact.transferred_units',)),
    ('The plan eliminates all shortages.',('impact.after.target_deficit',)),
    ('Resources have already been delivered.',('action_state.physical_execution',)),
    ('The advisory plan was implemented.',('action_state.plan_mode',)),
    ('The optimizer completed with OPTIMAL, executing safe transfers.',('solver.status',)),
    ('Despite executing authorized transfers, unmet resource needs remain.',('impact.after.target_deficit',)),
    ('The hospitals signed off the transfer plan.',('action_state.externally_authorized',)),
    ('The resources were put into effect through the transfer plan.',('action_state.plan_mode',)),
    ('The hospitals gave the green light to redistribution.',('action_state.externally_authorized',)),
    ('10 transfers were executed.',('impact.transfer_count',)),
    ('The shipment arrived and the resources were received.',('action_state.physical_execution',)),
    ('Resources have been transferred to the receiver.',('action_state.physical_execution',)),
    ('The recommended plan is redistributing resources.',('action_state.plan_mode',)),
    ('No resources were moved, but transfers were completed.',('action_state.physical_execution',)),
    ('Resources were not only moved but also approved.',('action_state.physical_execution',)),
    ('No doubt resources were delivered.',('action_state.physical_execution',)),
    ('The delivery of resources was successful.',('action_state.physical_execution',)),
    ('The transfer is underway.',('action_state.physical_execution',)),
    ('Transfer execution occurred.',('action_state.physical_execution',)),
    ('OPTIMAL implies operational success.',('solver.status',)),
    ('The network is fully resilient.',('impact.after.target_deficit',)),
    ('Approved.',('action_state.externally_authorized',)),
    ('No donor violations occurred and the transfers were executed.',('action_state.physical_execution',)),
    ('There were no shortages, resources were moved.',('action_state.physical_execution',)),
    ('Without consent resources were moved.',('action_state.physical_execution',)),
])
def test_execution_authorization_and_total_resolution_matrix_rejected(text,paths):
    req,records,catalog=setup()
    with pytest.raises(CopilotError) as e:catalog.validate(draft(catalog,text,paths),records,req,'2026-09-27')
    assert e.value.code=='unsafe_claim' and e.value.action_state_diagnostic['reason'] in (
        'unsupported_execution_or_authorization','unresolved_shortages_remain')


@pytest.mark.parametrize('text',[
    'RESOURCES WERE MOVED.', 'Resources were **moved**.', 'Resources were mo\u200bved.',
    'The plan was authoriＳed.', 'The transfer was carried-out.',
])
def test_bounded_normalization_does_not_allow_simple_typographic_evasion(text):
    req,records,catalog=setup()
    with pytest.raises(CopilotError):catalog.validate(draft(catalog,text),records,req,'2026-09-27')


@pytest.mark.parametrize('text',[
    'The plan is advisory.','No transfers have been physically executed.','Safe redistribution reduces pressure.',
])
def test_solver_or_quantities_cannot_substitute_for_action_state_citation(text):
    req,records,catalog=setup()
    with pytest.raises(CopilotError) as e:catalog.validate(draft(catalog,text,('safe_capacity',)),records,req,'2026-09-27')
    assert e.value.action_state_diagnostic['reason']=='action_state_citation_required'


def test_state_cannot_be_overridden_or_mutated_to_authorize_execution():
    for key in ('physical_execution','externally_authorized','hospital_contacted'):
        with pytest.raises(ValidationError):PlanActionState(**{key:True})
    with pytest.raises(ValidationError):PlanActionState(plan_mode='executed')
    state=PlanActionState()
    with pytest.raises(ValidationError):state.physical_execution=True


@pytest.mark.parametrize('text,path',[
    ('The plan is advisory.','action_state.physical_execution'),
    ('No hospital authorized the transfers.','action_state.physical_execution'),
    ('No resources were moved.','action_state.externally_authorized'),
    ('No hospital was contacted.','action_state.plan_mode'),
])
def test_action_state_facets_cannot_substitute_for_each_other(text,path):
    req,records,catalog=setup()
    with pytest.raises(CopilotError) as e:catalog.validate(draft(catalog,text,(path,)),records,req,'2026-09-27')
    assert e.value.action_state_diagnostic['reason']=='action_state_citation_required'


def test_state_leaves_numeric_membership_and_schema_exactness_unchanged():
    req,records,catalog=setup()
    with pytest.raises(CopilotError) as e:
        catalog.validate(draft(catalog,'15,678 accounting items are recommended.',('impact.transferred_units','action_state.plan_mode')),records,req,'2026-09-27')
    assert e.value.code=='unsupported_number'
    other=FactCatalogue();other.envelope('e1','optimize_redistribution',records['e1']['payload'])
    with pytest.raises(CopilotError):catalog.validate(draft(other,'The plan is advisory.'),records,req,'2026-09-27')
    with pytest.raises(ValidationError):FactDraftAnswer.model_validate({'situation':{'text':'advisory','evidence_refs':['id'],'field':'action_state'}})
    original=draft(catalog,'The plan is advisory.')
    records['e1']['payload']['action_state']['plan_mode']='executed'
    with pytest.raises(CopilotError) as e:catalog.validate(original,records,req,'2026-09-27')
    assert e.value.code=='evidence_invalid'


def test_action_facts_survive_bounded_catalogue_without_displacing_key_plan_values():
    req,records,catalog=setup()
    payload=records['e1']['payload'];payload['solver'].update({f'diagnostic_{i}':i for i in range(90)})
    large=FactCatalogue();large.envelope('e1','optimize_redistribution',payload)
    paths={f.path for f in large.facts.values()}
    assert len(large.facts)<=64
    assert {f'action_state.{k}' for k in advisory_state()}<=paths
    assert {'solver.status','safe_capacity','impact.transferred_units','impact.after.target_deficit'}<=paths


def test_exact_retained_two_failed_claims_rejected_without_provider_request():
    reproduction=old_failure()
    assert reproduction['status']=='PASS' and len(reproduction['cases'])==2
    assert reproduction['new_provider_requests']==0
    assert all(c['diagnostic']['authoritative_action_states']==[advisory_state()] for c in reproduction['cases'])


def test_missing_state_does_not_infer_execution_from_optimal():
    req,records,catalog=setup();records['e1']['payload'].pop('action_state')
    with pytest.raises(CopilotError):check_action_claim('OPTIMAL means the transfers were executed.',[],records)


def test_new_one_send_budget_preserves_29_history_and_blocks_replay(tmp_path):
    ledger=tmp_path/'ledger.json';journal=tmp_path/'new-journal.json'
    old={'day':'2026-09-28','used':29,'per_model':{MODEL:10,'other':19},'extra':'preserve'}
    ledger.write_text(json.dumps(old));budget=AdvisoryBudget(ledger,journal)
    budget.preflight();assert json.loads(ledger.read_text())==old and not journal.exists()
    with pytest.raises(CopilotError):budget.record_send('gemini-3.6-flash')
    budget.record_send(MODEL)
    expected=deepcopy(old);expected['used']=30;expected['per_model'][MODEL]=11
    assert json.loads(ledger.read_text())==expected
    assert json.loads(journal.read_text())['historical_ledger']==old
    with pytest.raises(CopilotError):budget.record_send(MODEL)
    ledger.write_text(json.dumps(old))
    with pytest.raises(CopilotError):AdvisoryBudget(ledger,journal)


def test_exact_new_live_failure_is_rejected_by_action_guard_independently_of_solver_guard():
    source=Path(__file__).resolve().parents[2]/'docs/evaluation/phase6-action-live.json'
    row=json.loads(source.read_text())['tests'][0]
    saved=FactDraftAnswer.model_validate_json(row['final_output_text'])
    text=saved.remaining_gaps[0].text
    assert 'optimal advisory transfers executed' in text
    assert row['authoritative_evidence']['e2']['payload']['action_state']==advisory_state()
    with pytest.raises(CopilotError) as e:
        check_action_claim(text,[],row['authoritative_evidence'],'remaining_gaps.0.text')
    assert e.value.code=='unsafe_claim'
    assert e.value.action_state_diagnostic['reason']=='unsupported_execution_or_authorization'
