"""Closed provider semantics, immutable evidence, and exact server rendering."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError
from app.ai import frames
from app.ai.action_state import advisory_state, check_action_claim
from app.ai.schemas import CopilotRequest, GroundedResponseFrame, FactDraftAnswer
from app.ai.facts import FactCatalogue
from app.ai.client import CopilotError
from test_profiles import profiles, trained
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

ORIGIN = '2026-09-27'


def fixture(message='Simulate a severe dengue surge and find the safest redistribution plan.', constrained=False):
    req = CopilotRequest(country_id='IN', profile='constrained' if constrained else 'redistribution-ready',
        state_id='MH', district_id='MH-PUNE', message=message, optimization_run_id='current-plan', scenario_id='current-scenario')
    context = {'country_id': req.country_id, 'profile': req.profile, 'origin': ORIGIN}
    payload = {'context': context, 'run_id': 'current-plan', 'scenario_id': 'current-scenario',
        'action_state': advisory_state(), 'solver': {'status': 'OPTIMAL'},
        'safe_capacity': 0 if constrained else 17745,
        'impact': {'before': {'target_deficit': 30230 if constrained else 41763},
            'after': {'target_deficit': 30230 if constrained else 26084, 'expected_unmet': 120.123456789},
            'transferred_units': 0 if constrained else 15679, 'transfer_count': 0 if constrained else 10,
            'donor_safety_violations': 0, 'new_donor_risks': 0},
        'transfers': [] if constrained else [{'donor_protected_reserve': 333,
            'donor_protected_minimum_after': 1137.2347601697224, 'donor_id': 'donor', 'donor_name': 'Donor',
            'receiver_id': 'receiver', 'receiver_name': 'Receiver', 'resource_id': 'IVF', 'unit': 'bags',
            'quantity': 20, 'distance_km': 2, 'donor_risk_after': 0, 'receiver_deficit_after': 10,
            'receiver_warning_after': None, 'receiver_risk_after': 0, 'rationale': 'retains reserve'}]}
    records = {'e1': {'tool': 'get_optimization_result', 'payload': payload,
        'request_scope': {'state_id': 'MH', 'district_id': 'MH-PUNE', 'facility_id': None}}}
    cat = FactCatalogue(); cat.envelope('e1', records['e1']['tool'], payload)
    return req, records, cat


def frame(cat, req, kinds=None):
    choices = {c['kind']: c['required_fact_ids'] for c in frames.options(cat, req)}
    if kinds is None:
        kinds = (['NO_SAFE_DONOR_CAPACITY', 'NO_RECOMMENDED_REDISTRIBUTION', 'REMAINING_SHORTAGE']
            if 'NO_SAFE_DONOR_CAPACITY' in choices else ['NETWORK_PRESSURE', 'ADVISORY_REDISTRIBUTION',
            'PARTIAL_RELIEF', 'DONOR_PROTECTION', 'ELIGIBLE_CAPACITY', 'REMAINING_SHORTAGE'])
    return GroundedResponseFrame.model_validate({'claims': [{'kind': k, 'evidence_refs': choices[k]} for k in kinds]})


def text(public):
    return ' '.join(c.text for c in [public.situation, *public.key_risks, *public.recommended_actions, *public.remaining_gaps])


@pytest.mark.parametrize('field', ['text', 'free_text', 'comment', 'reason', 'explanation', 'summary', 'note', 'resource_name', 'duration', 'qualifiers'])
def test_no_provider_free_text_escape_hatch(field):
    with pytest.raises(ValidationError):
        GroundedResponseFrame.model_validate({'claims': [{'kind': 'NETWORK_PRESSURE', 'evidence_refs': ['id'], field: 'Despite executing recommended transfers'}]})
    schema = json.dumps(GroundedResponseFrame.model_json_schema())
    assert '"text"' not in schema and '"reason"' not in schema


def test_unknown_kind_rejected():
    with pytest.raises(ValidationError):
        GroundedResponseFrame.model_validate({'claims': [{'kind': 'AUTHORIZED_TRANSFER', 'evidence_refs': ['id']}]})


def test_exact_server_numbers_and_decimal_no_llm_arithmetic():
    req, records, cat = fixture(); selected = frame(cat, req)
    public, evidence, audits = frames.resolve_frame(selected, cat, records, req, ORIGIN)
    answer = text(public)
    for number in ('41763', '17745', '15679', '10', '26084', '120.123456789', '1137.2347601697224', '333', '0'):
        assert number in answer
    assert 'accounting units' in answer and 'partial relief' in answer and 'advisory' in answer
    assert 'execut' not in answer and 'OPTIMAL' not in answer
    assert evidence and audits and all(not a['unknown_fact_ids'] for a in audits)
    assert all('text' not in c for c in selected.model_dump()['claims'])


def test_duplicate_kind_rejected_before_renderer(monkeypatch):
    req, records, cat = fixture(); selected = frame(cat, req)
    selected.claims.append(selected.claims[0])
    monkeypatch.setattr(frames, 'render', lambda *a: pytest.fail('render called before validation completed'))
    with pytest.raises(CopilotError, match='semantic frame'): frames.resolve_frame(selected, cat, records, req, ORIGIN)


@pytest.mark.parametrize('mutation', ['missing', 'unsupported', 'duplicate_id', 'unknown', 'namespace', 'stale', 'source_value', 'tool', 'profile', 'geography', 'origin', 'plan_id', 'scenario_id'])
def test_invalid_evidence_rejected_before_rendering(mutation, monkeypatch):
    req, records, cat = fixture(); selected = frame(cat, req); claim = selected.claims[1]
    if mutation == 'missing': claim.evidence_refs.pop()
    elif mutation == 'unsupported': claim.evidence_refs[1] = selected.claims[0].evidence_refs[0]
    elif mutation == 'duplicate_id': claim.evidence_refs[1] = claim.evidence_refs[0]
    elif mutation == 'unknown': claim.evidence_refs[0] = 'unknown-id'
    elif mutation == 'namespace': claim.evidence_refs[0] = claim.evidence_refs[0].replace(cat.scope, '123456789abcdef0')
    elif mutation == 'stale':
        other = FactCatalogue(); other.envelope('e1', records['e1']['tool'], records['e1']['payload'])
        claim.evidence_refs = frame(other, req).claims[1].evidence_refs
    elif mutation == 'source_value': records['e1']['payload']['impact']['transferred_units'] += 1
    elif mutation == 'tool': records['e1']['tool'] = 'get_warning_summary'
    elif mutation == 'geography': records['e1']['request_scope']['district_id'] = 'MH-OTHER'
    elif mutation in ('profile', 'origin'):
        value = 'constrained' if mutation == 'profile' else '2026-09-26'
        records['e1']['payload']['context'][mutation] = value
        cat.facts = {i: replace(f, context=deepcopy(records['e1']['payload']['context'])) for i, f in cat.facts.items()}
    else: records['e1']['payload']['run_id' if mutation == 'plan_id' else 'scenario_id'] = 'other-object'
    monkeypatch.setattr(frames, 'render', lambda *a: pytest.fail('invalid frame rendered'))
    with pytest.raises(CopilotError): frames.resolve_frame(selected, cat, records, req, ORIGIN)


def test_missing_required_kind_not_added_or_repaired():
    req, records, cat = fixture(); selected = frame(cat, req, ['NETWORK_PRESSURE'])
    before = selected.model_dump_json()
    with pytest.raises(CopilotError) as e: frames.resolve_frame(selected, cat, records, req, ORIGIN)
    assert 'missing_required_kinds' in e.value.frame_diagnostic['reason'] and selected.model_dump_json() == before


def test_resource_name_duration_units_server_resolved():
    req, records, cat = fixture()
    payload = {'context': records['e1']['payload']['context'], 'scenario': {'definition': {'duration': 14}},
        'resource_impact': [{'resource_id': 'PCM', 'name': 'Paracetamol', 'unit': 'tablets', 'unmet_demand': {'scenario': 12.3456789}}]}
    records['e2'] = {'tool': 'run_emergency_scenario', 'payload': payload, 'request_scope': records['e1']['request_scope']}
    cat.envelope('e2', records['e2']['tool'], payload)
    selected = frame(cat, req)
    selected.claims.extend(frame(cat, req, ['RESOURCE_PRESSURE', 'SCENARIO_DURATION']).claims)
    public, _, _ = frames.resolve_frame(selected, cat, records, req, ORIGIN)
    answer = text(public)
    assert 'Paracetamol (PCM)' in answer and '12.3456789 tablets' in answer and '14 days' in answer
    assert 'Paracetamol' not in selected.model_dump_json() and 'fourteen' not in selected.model_dump_json()


def test_constrained_exact_zero_and_unresolved_no_invented_donors():
    req, records, cat = fixture(constrained=True)
    public, _, _ = frames.resolve_frame(frame(cat, req), cat, records, req, ORIGIN)
    answer = text(public)
    assert '0 safe donor' in answer and '0 planned' in answer and '0 transfer lanes' in answer and '30230' in answer
    assert 'no redistribution' in answer
    with pytest.raises(CopilotError):
        bad = frame(cat, req); bad.claims[1].kind = 'ADVISORY_REDISTRIBUTION'
        frames.resolve_frame(bad, cat, records, req, ORIGIN)


@pytest.mark.parametrize('question,kind', [('Have these transfers been executed?', 'EXECUTION_STATUS'), ('What status did the solver return?', 'SOLVER_STATUS')])
def test_explicit_status_only_with_authoritative_evidence(question, kind):
    req, records, cat = fixture(question)
    public, _, _ = frames.resolve_frame(frame(cat, req, [kind]), cat, records, req, ORIGIN)
    answer = text(public)
    assert ('not been physically executed' in answer) if kind == 'EXECUTION_STATUS' else ('OPTIMAL' in answer and 'mathematical optimum' in answer)
    ordinary = req.model_copy(update={'message': 'Explain the recommended plan.'})
    with pytest.raises(CopilotError): frames.resolve_frame(frame(cat, req, [kind]), cat, records, ordinary, ORIGIN)


def test_feasible_status_never_strengthened_to_optimal():
    req, records, _ = fixture('What status did the solver return?')
    records['e1']['payload']['solver']['status'] = 'FEASIBLE'
    cat = FactCatalogue(); cat.envelope('e1', records['e1']['tool'], records['e1']['payload'])
    public, _, _ = frames.resolve_frame(frame(cat, req, ['SOLVER_STATUS']), cat, records, req, ORIGIN)
    assert 'FEASIBLE' in public.situation.text and 'OPTIMAL' not in public.situation.text


@pytest.mark.parametrize('phrase', ['executing safe transfers', 'Despite executing authorized transfers', 'optimal advisory transfers executed', 'Despite executing recommended transfers'])
def test_all_previous_execution_failures_still_rejected_in_legacy_path(phrase):
    req, records, cat = fixture()
    ids = [f.fact_id for f in cat.facts.values() if f.path == 'action_state.plan_mode']
    draft = FactDraftAnswer.model_validate({'situation': {'text': phrase, 'evidence_refs': ids}})
    with pytest.raises(CopilotError) as error: cat.validate(draft, records, req, ORIGIN)
    assert error.value.code in ('unsafe_claim', 'solver_terminology')
    with pytest.raises(ValidationError):
        GroundedResponseFrame.model_validate({'claims': [{'kind': 'ADVISORY_REDISTRIBUTION', 'evidence_refs': ids, 'text': phrase}]})


def test_old_uncited_resource_and_worded_duration_evidence_remains_preserved():
    root = Path(__file__).resolve().parents[2]
    raw = (root / 'docs/evaluation/phase6-completion-live.json').read_text()
    review = (root / 'docs/evaluation/phase6-completion-review.json').read_text()
    assert 'fourteen-day' in raw and 'paracetamol' in raw.lower()
    assert 'paracetamol' in review.lower() and 'duration' in review.lower()
    for old in ('paracetamol', 'fourteen-day'):
        with pytest.raises(ValidationError):
            GroundedResponseFrame.model_validate({'claims': [{'kind': 'NETWORK_PRESSURE', 'evidence_refs': ['id'], 'text': old}]})


def test_provenance_wape_error_not_accuracy_and_no_live_connection():
    req, records, _ = fixture('Is this live government inventory, and how should I interpret the forecast performance?')
    context = records['e1']['payload']['context']
    records = {'e1': {'tool': 'get_data_provenance', 'payload': {'context': context,
        'data_type': 'calibrated simulated operations', 'live_government_inventory': False,
        'interpretation': {p.split('.')[1]: v for p, v in frames.PROVENANCE_VALUES.items()}}},
        'e2': {'tool': 'get_model_performance', 'payload': {'context': context,
            'targets': {'medicine': {'champion': 'measured', 'models': {'measured': {'test': {'wape': 0.123456789}}}}}}}}
    cat = FactCatalogue()
    for eid, record in records.items():
        record['request_scope'] = {'state_id': req.state_id, 'district_id': req.district_id, 'facility_id': req.facility_id}
        cat.envelope(eid, record['tool'], record['payload'])
    selected = frame(cat, req, list(frames.PROVENANCE_RULES))
    public, _, _ = frames.resolve_frame(selected, cat, records, req, ORIGIN)
    answer = text(public)
    for phrase in ('public aggregate', 'simulated', 'not live government', 'model-based', 'Scenarios', 'advisory',
                   'WAPE is an error metric, not accuracy', '0.123456789', 'not clinically validated', 'hospitals are connected', 'experimental'):
        assert phrase in answer
    legacy = FactDraftAnswer.model_validate({'situation': {'text': 'WAPE proves accuracy.', 'evidence_refs': selected.claims[5].evidence_refs}})
    with pytest.raises(CopilotError): cat.validate(legacy, records, req, ORIGIN)
    # A provider cannot reinterpret the metric through an uncontrolled qualifier.
    with pytest.raises(ValidationError):
        GroundedResponseFrame.model_validate({'claims': [{'kind': 'WAPE_ERROR_METRIC', 'evidence_refs': selected.claims[5].evidence_refs, 'qualifiers': ['accuracy']}]})


def test_current_six_send_authorization_preserves_33_request_ledger(tmp_path):
    from verify_phase6_frames import CompletionBudget, MODEL
    original = {'day': 'original-day-retained', 'used': 33, 'per_model': {MODEL: 14, 'other': 19}, 'history': 'keep'}
    ledger = tmp_path / 'ledger.json'; ledger.write_text(json.dumps(original)); journal = tmp_path / 'journal.json'
    budget = CompletionBudget(ledger, journal)
    with pytest.raises(CopilotError): budget.record_send('gemini-3.6-flash', 'positive')
    assert not journal.exists() and json.loads(ledger.read_text()) == original
    for label in ('positive', 'positive', 'positive', 'followup', 'constrained', 'provenance'): budget.record_send(MODEL, label)
    expected = deepcopy(original); expected['used'] = 39; expected['per_model'][MODEL] = 20
    assert json.loads(ledger.read_text()) == expected
    assert json.loads(journal.read_text())['historical_ledger'] == original
    with pytest.raises(CopilotError): budget.record_send(MODEL, 'extra')
    budget.stop()
    with pytest.raises(CopilotError): budget.preflight()
    with pytest.raises(CopilotError): CompletionBudget(ledger, journal)
    ledger.write_text(json.dumps(original))
    with pytest.raises(CopilotError): CompletionBudget(ledger, journal)


def test_semantic_handoff_preserves_contract_no_foreign_interaction_id(profiles):
    from test_ai import service
    from test_ai_budget import scoped
    from test_ai_failover import unavailable
    from verify_gemini import DemoTransport
    made = []
    class Primary(DemoTransport):
        def create(self, **body):
            if 'response_format' in body: raise unavailable()
            return super().create(**body)
    def factory(cfg):
        transport = Primary(cfg) if not made else DemoTransport(cfg)
        made.append(transport)
        return transport
    svc, repo = service(profiles, factory)
    req = scoped(repo, message='Simulate a severe 14-day dengue surge and find the safest redistribution plan.', allow_planning=True)
    response = svc.run(repo, req)
    body = made[1].bodies[0]; handoff = json.loads(body['input'])
    assert 'previous_interaction_id' not in body and 'tools' not in body
    assert handoff['semantic_contract']['protocol'] == frames.VERSION
    assert handoff['context']['profile'] == req.profile
    assert response.metadata['prose_author'] == 'HealthNexus deterministic renderer'
    assert sum(t.tool == 'optimize_redistribution' for t in response.tools_used) == 1
    assert response.metadata['model_handoffs'] and svc.audit[-1]['provider_semantic_frame']


def test_positive_provider_schema_has_unique_required_named_slots():
    req, records, cat = fixture()
    body, schema = frames.synthesis(cat, req, '{}')
    slots = schema['properties']['claims']
    expected = {'NETWORK_PRESSURE', 'ADVISORY_REDISTRIBUTION', 'PARTIAL_RELIEF', 'REMAINING_SHORTAGE'}
    assert slots['type'] == 'object' and slots['additionalProperties'] is False
    assert set(slots['properties']) == set(slots['required']) == expected
    assert 'RESOURCE_PRESSURE' not in slots['properties'] and 'SCENARIO_DURATION' not in slots['properties']
    for slot in slots['properties'].values():
        assert slot['additionalProperties'] is False
        assert set(slot['properties']) == {'evidence_refs'}
        assert slot['properties']['evidence_refs']['items']['enum']
        assert 'anyOf' not in slot
    from frame_fixture import mock_frame
    wire = mock_frame({'input': body})
    parsed = frames.parse(json.dumps(wire))
    assert {c.kind: c.evidence_refs for c in parsed.claims} == {k: v['evidence_refs'] for k,v in wire['claims'].items()}
    assert frames.resolve_frame(parsed, cat, records, req, ORIGIN)[0].situation


@pytest.mark.parametrize('raw', ['{"claims":[]}', '{"claims":{"UNKNOWN":{"evidence_refs":["id"]}}}',
    '{"claims":{"NETWORK_PRESSURE":{"evidence_refs":["id"],"text":"Resources were moved."}}}',
    '{"claims":{"NETWORK_PRESSURE":{"evidence_refs":["id"],"quantity":12}}}'])
def test_provider_slots_reject_lists_unknown_or_uncontrolled_values(raw):
    with pytest.raises(ValidationError): frames.parse(raw)


def test_duplicate_json_slot_is_rejected_not_silently_normalized():
    raw = '{"claims":{"NETWORK_PRESSURE":{"evidence_refs":["first"]},"NETWORK_PRESSURE":{"evidence_refs":["second"]}}}'
    with pytest.raises(CopilotError) as error: frames.parse(raw)
    assert error.value.frame_diagnostic['reason'] == 'duplicate_slot_property'


def test_slots_missing_required_kind_rejected_before_render(monkeypatch):
    req, records, cat = fixture()
    ids = next(c['required_fact_ids'] for c in frames.options(cat, req) if c['kind'] == 'NETWORK_PRESSURE')
    selected = frames.parse(json.dumps({'claims': {'NETWORK_PRESSURE': {'evidence_refs': ids}}}))
    monkeypatch.setattr(frames, 'render', lambda *a: pytest.fail('incomplete slots rendered'))
    with pytest.raises(CopilotError): frames.resolve_frame(selected, cat, records, req, ORIGIN)


def test_new_slots_run_global_budget_preserves_historical_36_requests(tmp_path):
    from verify_phase6_slots import CompletionBudget, MODEL
    original = {'day': 'preserve-old-day', 'used': 36, 'per_model': {MODEL: 17, 'other': 19}}
    ledger = tmp_path / 'ledger.json'; ledger.write_text(json.dumps(original)); journal = tmp_path / 'journal.json'
    budget = CompletionBudget(ledger, journal)
    for label in ('positive','positive','positive','followup','constrained','provenance'): budget.record_send(MODEL,label)
    expected = deepcopy(original); expected['used'] = 42; expected['per_model'][MODEL] = 23
    assert json.loads(ledger.read_text()) == expected
    assert json.loads(journal.read_text())['historical_ledger'] == original
    with pytest.raises(CopilotError): budget.record_send(MODEL,'extra')
    budget.stop()
    with pytest.raises(CopilotError): CompletionBudget(ledger,journal)


def test_named_slot_order_retains_followup_public_remaining_gap():
    req, records, cat = fixture('Why were these donors selected, and what shortages remain?')
    body, _ = frames.synthesis(cat, req, '{}')
    from frame_fixture import mock_frame
    raw = mock_frame({'input': body})
    # JSON ordering is not a semantic decision; decoding uses fixed slots.
    raw['claims'] = dict(reversed(list(raw['claims'].items())))
    public, _, _ = frames.resolve_frame(frames.parse(json.dumps(raw)), cat, records, req, ORIGIN)
    assert 'reserves' in public.situation.text and public.remaining_gaps
    assert '26084' in public.remaining_gaps[0].text
