"""Verifier-only scope, accounting and fail-fast checks; no live provider traffic."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verify_live_workflow import WorkflowBudget,check_calls,text_acceptance,review_passed,native_trace,MODEL,MAX_SENDS
from app.ai.client import CopilotError
from app.ai.schemas import CopilotRequest


def budget(tmp_path):
    original={'day':'original-retained-day','used':25,'per_model':{MODEL:6,'legacy-unattributed':7},'retained':'metadata'}
    path=tmp_path/'ledger.json';path.write_text(json.dumps(original));journal=tmp_path/'journal.json'
    return WorkflowBudget(path,journal),path,journal,original


def test_eight_sends_are_global_and_cumulative_without_date_rollover(tmp_path):
    counter,path,journal,original=budget(tmp_path)
    counter.preflight();assert json.loads(path.read_text())==original
    for _ in range(MAX_SENDS):counter.record_send(MODEL)
    expected=deepcopy(original);expected['used']=33;expected['per_model'][MODEL]=14
    assert json.loads(path.read_text())==expected
    assert json.loads(journal.read_text())['historical_ledger']==original
    with pytest.raises(CopilotError,match='global maximum'):counter.preflight()
    with pytest.raises(CopilotError,match='global maximum'):counter.record_send(MODEL)
    with pytest.raises(CopilotError,match='replayed'):WorkflowBudget(path,journal)


def test_other_models_cannot_consume_authorized_budget(tmp_path):
    counter,path,journal,original=budget(tmp_path)
    with pytest.raises(CopilotError,match='Cross-model'):counter.record_send('gemini-3.6-flash')
    assert json.loads(path.read_text())==original and not journal.exists()


def request(**kwargs):
    return CopilotRequest(country_id='IN',profile='redistribution-ready',state_id='MH',district_id='MH-PUNE',
        message='Acceptance',allow_planning=kwargs.pop('allow_planning',True),**kwargs)


def native(name='run_emergency_scenario',**kwargs):
    return {'type':'function_call','id':'native-1','name':name,'arguments':{
        'country_id':'IN','profile':'redistribution-ready','state_id':'MH','district_id':'MH-PUNE',
        'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,**kwargs}}


def checks(call,req=None,known=None):
    return check_calls({'tools':[{'name':'run_emergency_scenario'},{'name':'get_scenario_comparison'}]},
        {'steps':[call]},req or request(),None,None,None,known or set(),set())


def test_native_valid_call_is_checked_without_operational_execution():
    result=checks(native())
    assert result[0]['declared'] and result[0]['pydantic_valid'] and result[0]['scope_permissions_identity_valid']
    assert result[0]['validated_arguments']['duration']==14


@pytest.mark.parametrize('change',[{'name':'fabricated_tool'},{'arguments':{}},{'id':None}])
def test_undeclared_or_malformed_native_call_is_rejected_before_execution(change):
    with pytest.raises(CopilotError):checks({**native(),**change})


@pytest.mark.parametrize('kwargs',[{'country_id':'BR'},{'profile':'constrained'},
    {'district_id':'MH-MUMBAI'},{'duration':99},{'quantity':123}])
def test_native_pydantic_scope_and_no_model_transfer_quantity(kwargs):
    with pytest.raises(CopilotError):checks(native(**kwargs))


def test_native_planning_requires_permission():
    with pytest.raises(CopilotError):checks(native(),request(allow_planning=False))


def test_unknown_scenario_identity_is_rejected_before_execution():
    call={'type':'function_call','id':'native-scenario','name':'get_scenario_comparison','arguments':{
        'country_id':'IN','profile':'redistribution-ready','scenario_id':str(uuid4())}}
    with pytest.raises(CopilotError):checks(call)


def answer(situation,risks=(),gaps=()):
    return SimpleNamespace(situation=SimpleNamespace(text=situation),key_risks=[SimpleNamespace(text=t) for t in risks],
        remaining_gaps=[SimpleNamespace(text=t) for t in gaps],recommended_actions=[])


@pytest.mark.parametrize('text',['All shortages resolved.','Risk eliminated.'])
def test_false_complete_resolution_is_an_acceptance_failure(text):
    with pytest.raises(CopilotError):text_acceptance(answer(text,gaps=['Shortages remain.']),'positive')


def test_positive_answer_must_identify_remaining_shortage():
    with pytest.raises(CopilotError):text_acceptance(answer('The advisory plan is optimal.'),'positive')


def test_followup_needs_donor_protection_and_remaining_shortages():
    assert text_acceptance(answer('Donors retain protected reserves.',gaps=['Shortages remain.']),'followup')['qualitative_acceptance']=='PASS'
    with pytest.raises(CopilotError):text_acceptance(answer('Donors were chosen.',gaps=['Shortages remain.']),'followup')


def test_constrained_answer_cannot_suggest_network_self_resolution():
    assert text_acceptance(answer('No safe surplus is available; the network cannot self-resolve shortages.'),'constrained')
    with pytest.raises(CopilotError):text_acceptance(answer('Redistribution resolves shortages.'),'constrained')


def test_provenance_requires_all_requested_distinctions():
    with pytest.raises(CopilotError) as error:text_acceptance(answer('This is simulated inventory, not live inventory.'),'provenance')
    assert 'wape_error_metric' in error.value.acceptance_diagnostic['missing_distinctions']
    text=('Official public aggregates inform calibrated simulated operations, not live government inventory. '
        'Forecasts are derived model outputs, not clinically validated; WAPE is an error metric. '
        'Scenario projections use externally specified assumptions; advisory recommendations involve no physical action.')
    assert text_acceptance(answer(text),'provenance')['qualitative_acceptance']=='PASS'


@pytest.mark.parametrize('verdict',['STOP: unsupported donor claim','','yes'])
def test_only_an_explicit_local_factual_pass_can_continue(verdict):
    assert not review_passed(verdict)
    assert review_passed('PASS')


def test_native_trace_excludes_opaque_provider_signatures_and_internal_metadata():
    call={**native(),'signature':'opaque-provider-state','internal_metadata':{'hidden':'unused'}}
    assert native_trace([call])==[{k:call[k] for k in ('type','name','id','arguments')}]
    assert 'signature' in call  # Logging does not mutate the provider response.
