"""Closed semantic protocol: validate every selection before rendering any text.

No fallback to prose, missing-reference repair, or business calculations. All
numbers, resource labels and durations are copied from immutable local facts.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math
from app.ai.schemas import GroundedResponseFrame, GroundedResponseSlots, FactDraftAnswer
from app.ai.client import CopilotError
from app.ai.citations import resolve
from app.ai.numeric import field_unit
from app.ai.action_state import PLAN_TOOLS
from app.ai.synthesis import provider_view, status_topics, validate_narrative
from app.ai.tool_registry import json_schema

VERSION = 'grounded-semantic-slots-v2'
MODE = 'action_state.plan_mode'
BEFORE = 'impact.before.target_deficit'
AFTER = 'impact.after.target_deficit'
PLAN_RULES = {
    'NETWORK_PRESSURE': (BEFORE,),
    'ADVISORY_REDISTRIBUTION': (MODE, 'impact.transferred_units', 'impact.transfer_count'),
    'PARTIAL_RELIEF': (MODE, BEFORE, AFTER),
    'REMAINING_SHORTAGE': (MODE, AFTER, 'impact.after.expected_unmet'),
    'DONOR_PROTECTION': (MODE, 'transfers.0.donor_protected_reserve',
                         'transfers.0.donor_protected_minimum_after', 'impact.donor_safety_violations'),
    'ELIGIBLE_CAPACITY': (MODE, 'safe_capacity'),
    'NO_SAFE_DONOR_CAPACITY': ('safe_capacity',),
    'NO_RECOMMENDED_REDISTRIBUTION': (MODE, 'impact.transferred_units', 'impact.transfer_count'),
    'EXECUTION_STATUS': (MODE, 'action_state.physical_execution',
                         'action_state.externally_authorized', 'action_state.hospital_contacted'),
    'SOLVER_STATUS': ('solver.status',),
}
PROVENANCE_RULES = {
    'PUBLIC_AGGREGATE_INPUT': ('interpretation.public_inputs',),
    'SIMULATED_FACILITY_OPERATIONS': ('interpretation.facility_operations', 'data_type'),
    'MODEL_BASED_FORECAST': ('interpretation.forecast',),
    'SCENARIO_PROJECTION': ('interpretation.scenario',),
    'ADVISORY_OPTIMIZATION': ('interpretation.optimization',),
    'WAPE_ERROR_METRIC': ('interpretation.wape',),
    'NOT_CLINICALLY_VALIDATED': ('interpretation.forecast',),
    'NO_LIVE_GOVERNMENT_CONNECTION': ('live_government_inventory', 'interpretation.connections'),
    'EXPERIMENTAL_FEDERATION': ('interpretation.federation',),
}
# These are the typed tool adapter's documented semantics, not provider wording.
PROVENANCE_VALUES = {
    'interpretation.public_inputs': 'official public aggregate source inputs',
    'interpretation.facility_operations': 'fictional calibrated simulated facility operations',
    'interpretation.forecast': 'derived model-based output; not clinically validated',
    'interpretation.scenario': 'externally specified simulated stress-test projection',
    'interpretation.optimization': 'advisory optimization recommendation',
    'interpretation.wape': 'forecast error metric, not accuracy',
    'interpretation.connections': 'no government systems or hospitals connected',
    'interpretation.federation': 'experimental federated-learning metrics',
}


def enabled(selected_intent):
    return selected_intent in ('emergency-planning', 'follow-up-plan', 'plan-review', 'provenance')


@dataclass(frozen=True)
class Selection:
    kind: str
    fact_ids: tuple


def reject(reason):
    error = CopilotError('semantic_frame_invalid', 'Gemini selected an invalid semantic frame.', 422)
    error.frame_diagnostic = {'reason': reason}
    raise error


def options(catalogue, request):
    """Server describes eligible exact evidence combinations, never fills a frame."""
    topics = status_topics(request)
    result = []
    for eid, envelope in catalogue.envelopes.items():
        tool = envelope['tool']
        facts = {f.path: f for f in catalogue.facts.values() if f.evidence_id == eid}
        rules = PLAN_RULES if tool in PLAN_TOOLS else PROVENANCE_RULES if tool == 'get_data_provenance' else {}
        for kind, paths in rules.items():
            if kind == 'EXECUTION_STATUS' and not topics['action']: continue
            if kind == 'SOLVER_STATUS' and not topics['solver']: continue
            if not all(p in facts for p in paths): continue
            ids = [facts[p].fact_id for p in paths]
            if kind == 'WAPE_ERROR_METRIC':
                metrics = [f for f in catalogue.facts.values() if f.tool == 'get_model_performance'
                           and f.path.endswith('.test.wape')]
                # The catalogue prioritizes the measured medicine champion.
                if not metrics: continue
                ids.append(metrics[0].fact_id)
            if predicate(kind, [catalogue.facts[i] for i in ids], fail=False):
                result.append({'kind': kind, 'required_fact_ids': ids})
        if tool == 'run_emergency_scenario':
            if 'scenario.definition.duration' in facts:
                result.append({'kind': 'SCENARIO_DURATION', 'required_fact_ids': [facts['scenario.definition.duration'].fact_id]})
            for path in facts:
                if path.startswith('resource_impact.') and path.endswith('.resource_id'):
                    root = path.rsplit('.', 1)[0]
                    paths = [path, root + '.name', root + '.unit', root + '.unmet_demand.scenario']
                    if all(p in facts for p in paths):
                        result.append({'kind': 'RESOURCE_PRESSURE', 'required_fact_ids': [facts[p].fact_id for p in paths]})
    return result


def predicate(kind, facts, fail=True):
    v = {f.path: f.value for f in facts}
    numeric = [f.value for f in facts if f.path in {BEFORE, AFTER, 'safe_capacity',
        'impact.transferred_units', 'impact.transfer_count', 'impact.after.expected_unmet',
        'impact.donor_safety_violations', 'transfers.0.donor_protected_reserve',
        'transfers.0.donor_protected_minimum_after', 'scenario.definition.duration'}
        or f.path.endswith(('.test.wape', '.unmet_demand.scenario'))]
    ok = all(type(n) in (int, float) and math.isfinite(n) and n >= 0 for n in numeric)
    if MODE in v: ok &= v[MODE] == 'advisory'
    if kind == 'NETWORK_PRESSURE': ok &= v.get(BEFORE, 0) > 0
    elif kind == 'ADVISORY_REDISTRIBUTION': ok &= v.get('impact.transferred_units', 0) > 0 and v.get('impact.transfer_count', 0) > 0
    elif kind == 'PARTIAL_RELIEF': ok &= 0 < v.get(AFTER, 0) < v.get(BEFORE, 0)
    elif kind == 'REMAINING_SHORTAGE': ok &= v.get(AFTER, 0) > 0
    elif kind == 'DONOR_PROTECTION':
        ok &= v.get('impact.donor_safety_violations') == 0 and v.get('transfers.0.donor_protected_minimum_after', -1) >= v.get('transfers.0.donor_protected_reserve', 0)
    elif kind == 'ELIGIBLE_CAPACITY': ok &= v.get('safe_capacity', 0) > 0
    elif kind == 'NO_SAFE_DONOR_CAPACITY': ok &= v.get('safe_capacity') == 0
    elif kind == 'NO_RECOMMENDED_REDISTRIBUTION': ok &= v.get('impact.transferred_units') == v.get('impact.transfer_count') == 0
    elif kind == 'EXECUTION_STATUS': ok &= all(v.get(p) is False for p in PLAN_RULES[kind][1:])
    elif kind == 'SOLVER_STATUS': ok &= v.get('solver.status') in ('OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'UNKNOWN', 'MODEL_INVALID')
    elif kind == 'SCENARIO_DURATION': ok &= v.get('scenario.definition.duration', 0) > 0
    elif kind == 'RESOURCE_PRESSURE':
        ok &= all(isinstance(f.value, str) and f.value for f in facts if f.path.endswith(('.resource_id', '.unit')))
    if kind in PROVENANCE_RULES:
        ok &= all(v.get(p) == PROVENANCE_VALUES[p] for p in PROVENANCE_RULES[kind] if p.startswith('interpretation.'))
        if 'live_government_inventory' in v: ok &= v['live_government_inventory'] is False
        if 'data_type' in v: ok &= v['data_type'] == 'calibrated simulated operations'
    if not ok and fail: reject('claim_predicate_failed:' + kind)
    return bool(ok)


def validate(frame, catalogue, records, request, origin):
    """Complete validation pass; renderer has not been called at this point."""
    accepted = []; seen = set(); choices = options(catalogue, request)
    for claim in frame.claims:
        if claim.kind in seen: reject('duplicate_kind')
        seen.add(claim.kind)
        ids = claim.evidence_refs
        if len(set(ids)) != len(ids): reject('duplicate_fact_id')
        if any(fid not in catalogue.facts or not fid.startswith(catalogue.facts[fid].evidence_id + '_' + catalogue.scope + '_') for fid in ids): reject('unknown_or_stale_fact_id')
        facts = [catalogue.facts[fid] for fid in ids]
        for fact in facts:
            record = records.get(fact.evidence_id, {})
            try:
                payload = record['payload']; context = payload['context']
                if record['tool'] != fact.tool or context != fact.context or resolve(payload, fact.path) != fact.value: reject('fact_source_changed')
                if field_unit(fact.tool, fact.path, payload) != fact.unit: reject('fact_unit_changed')
                identity = {k: payload[k] for k in ('run_id', 'scenario_id', 'snapshot_id',
                    'model_version', 'model_sha256', 'policy_version') if k in payload}
                if identity != catalogue.envelopes[fact.evidence_id]['source_identity']: reject('source_identity_changed')
                if context['country_id'] != request.country_id or context['profile'] != request.profile or context.get('origin') != str(origin): reject('context_or_origin_mismatch')
                expected_scope = {key: getattr(request, key, None) for key in ('state_id', 'district_id', 'facility_id')}
                if record.get('request_scope') != expected_scope: reject('geography_mismatch')
                if fact.tool in PLAN_TOOLS:
                    if request.optimization_run_id and payload.get('run_id') != request.optimization_run_id: reject('plan_identity_mismatch')
                    if request.scenario_id and payload.get('scenario_id') != request.scenario_id: reject('scenario_identity_mismatch')
            except (KeyError, TypeError, IndexError, ValueError): reject('fact_source_changed')
        if not any(c['kind'] == claim.kind and set(c['required_fact_ids']) == set(ids) for c in choices): reject('incompatible_or_missing_evidence:' + claim.kind)
        predicate(claim.kind, facts)
        accepted.append(Selection(claim.kind, tuple(ids)))
    # These bounded operational questions require all their semantic distinctions.
    # Missing kinds are rejected; never inserted by the server.
    required = required_kinds(choices, request)
    if not required <= seen: reject('missing_required_kinds:' + ','.join(sorted(required - seen)))
    return tuple(accepted)


def required_kinds(choices, request):
    available = {c['kind'] for c in choices}
    topics = status_topics(request)
    if topics['action'] and 'EXECUTION_STATUS' in available: required = {'EXECUTION_STATUS'}
    elif topics['solver'] and 'SOLVER_STATUS' in available: required = {'SOLVER_STATUS'}
    elif 'PUBLIC_AGGREGATE_INPUT' in available: required = set(PROVENANCE_RULES) & available
    elif 'NO_SAFE_DONOR_CAPACITY' in available:
        required = {'NO_SAFE_DONOR_CAPACITY', 'NO_RECOMMENDED_REDISTRIBUTION', 'REMAINING_SHORTAGE'} & available
    elif 'why' in request.message.lower() and 'DONOR_PROTECTION' in available:
        required = {'DONOR_PROTECTION', 'ELIGIBLE_CAPACITY', 'REMAINING_SHORTAGE'} & available
    elif 'ADVISORY_REDISTRIBUTION' in available:
        required = {'NETWORK_PRESSURE', 'ADVISORY_REDISTRIBUTION', 'PARTIAL_RELIEF', 'REMAINING_SHORTAGE'} & available
    else: required = set()
    return required


def sentence(selection, catalogue):
    facts = [catalogue.facts[i] for i in selection.fact_ids]
    v = {f.path: f.value for f in facts}; k = selection.kind
    # str copies exact scalars, without rounding or unit conversion.
    if k == 'NETWORK_PRESSURE': return f"Current projections indicate resource pressure: {v[BEFORE]} inventory-item accounting units are needed to meet the selected network's target."
    if k == 'ADVISORY_REDISTRIBUTION': return f"HealthNexus recommends an advisory redistribution plan of {v['impact.transferred_units']} inventory-item accounting units across {v['impact.transfer_count']} transfer lanes."
    if k == 'PARTIAL_RELIEF': return f"The proposed advisory plan provides partial relief: target deficit would fall from {v[BEFORE]} to {v[AFTER]} inventory-item accounting units."
    if k == 'REMAINING_SHORTAGE': return f"Substantial shortages remain under the advisory plan: {v[AFTER]} target inventory-item accounting units remain unresolved, with expected unmet demand of {v['impact.after.expected_unmet']} accounting units."
    if k == 'DONOR_PROTECTION':
        units = {f.path: f.unit or 'inventory items' for f in facts}
        return f"Recommended donor selections retain configured reserves. The cited donor retains a projected minimum of {v['transfers.0.donor_protected_minimum_after']} {units['transfers.0.donor_protected_minimum_after']} against a protected reserve of {v['transfers.0.donor_protected_reserve']} {units['transfers.0.donor_protected_reserve']}; the plan has {v['impact.donor_safety_violations']} donor protection violations."
    if k == 'ELIGIBLE_CAPACITY': return f"Eligible safe donor capacity for this advisory plan is {v['safe_capacity']} inventory-item accounting units under the configured protection policy."
    if k == 'NO_SAFE_DONOR_CAPACITY': return f"Configured reserve constraints leave {v['safe_capacity']} safe donor inventory-item accounting units in this network."
    if k == 'NO_RECOMMENDED_REDISTRIBUTION': return f"HealthNexus recommends no redistribution: the advisory plan contains {v['impact.transferred_units']} planned inventory-item accounting units and {v['impact.transfer_count']} transfer lanes."
    if k == 'EXECUTION_STATUS': return 'These transfers are advisory recommendations and have not been physically executed. They have no external authorization, and no hospitals have been contacted.'
    if k == 'SOLVER_STATUS':
        status = v['solver.status']
        meanings = {'OPTIMAL': 'it found the mathematical optimum under the configured constraints',
            'FEASIBLE': 'it found a feasible mathematical solution without certifying an optimum',
            'INFEASIBLE': 'the mathematical constraints admit no feasible solution',
            'UNKNOWN': 'it did not establish a mathematical solution status', 'MODEL_INVALID': 'the mathematical model was invalid'}
        return f"The solver returned {status}, meaning {meanings[status]}."
    if k == 'SCENARIO_DURATION': return f"The simulated scenario covers {v['scenario.definition.duration']} days."
    if k == 'RESOURCE_PRESSURE':
        resource = next(f.value for f in facts if f.path.endswith('.resource_id'))
        name = next(f.value for f in facts if f.path.endswith('.name'))
        unit = next(f.value for f in facts if f.path.endswith('.unit'))
        amount = next(f.value for f in facts if f.path.endswith('.unmet_demand.scenario'))
        return f"Resource {name} ({resource}) has projected unmet demand of {amount} {unit} in the simulated scenario."
    fixed = {
        'PUBLIC_AGGREGATE_INPUT': 'Official public aggregate source inputs inform HealthNexus calibration.',
        'SIMULATED_FACILITY_OPERATIONS': 'Facility operations and inventory are fictional calibrated simulated data.',
        'MODEL_BASED_FORECAST': 'Forecasts are derived model-based outputs using simulated operational histories.',
        'SCENARIO_PROJECTION': 'Scenarios are simulated stress-test projections, specified externally.',
        'ADVISORY_OPTIMIZATION': 'Optimization outputs are advisory recommendations for resource planning.',
        'NOT_CLINICALLY_VALIDATED': 'These forecasts are not clinically validated.',
        'NO_LIVE_GOVERNMENT_CONNECTION': 'Inventory is not live government inventory; no real government systems or hospitals are connected.',
        'EXPERIMENTAL_FEDERATION': 'Federated-learning metrics remain experimental.',
    }
    if k == 'WAPE_ERROR_METRIC':
        wape = next(f.value for f in facts if f.path.endswith('.test.wape'))
        return f"The cited forecast test WAPE is {wape}. WAPE is an error metric, not accuracy; lower error is better."
    return fixed[k]


def render(selections, catalogue):
    buckets = {'key_risks': [], 'recommended_actions': [], 'remaining_gaps': []}
    actions = {'ADVISORY_REDISTRIBUTION', 'DONOR_PROTECTION', 'ELIGIBLE_CAPACITY', 'NO_RECOMMENDED_REDISTRIBUTION', 'ADVISORY_OPTIMIZATION'}
    gaps = {'REMAINING_SHORTAGE', 'NOT_CLINICALLY_VALIDATED', 'NO_LIVE_GOVERNMENT_CONNECTION', 'EXPERIMENTAL_FEDERATION'}
    first = None
    for selected in selections:
        claim = {'text': sentence(selected, catalogue), 'evidence_refs': list(selected.fact_ids)}
        if first is None: first = claim; continue
        bucket = 'recommended_actions' if selected.kind in actions else 'remaining_gaps' if selected.kind in gaps else 'key_risks'
        buckets[bucket].append(claim)
    try: return FactDraftAnswer.model_validate({'situation': first, **buckets})
    except ValueError: reject('public_claim_capacity_exceeded')


def resolve_frame(frame, catalogue, records, request, origin):
    selected = validate(frame, catalogue, records, request, origin)
    draft = render(selected, catalogue)
    public, evidence, audits = catalogue.validate(draft, records, request, origin)
    validate_narrative(public, request, records)
    return public, evidence, audits


def synthesis(catalogue, request, data):
    views, _ = provider_view(catalogue, request)
    choices = options(catalogue, request)
    if not choices: reject('no_eligible_semantics')
    required = required_kinds(choices, request)
    # Ordinary acceptance flows expose their compact required operational points.
    # Per-resource/duration detail is a separate explicit question, not an extra
    # competing list item in the positive workflow.
    extra = set()
    question = request.message.lower()
    if any(p in question for p in ('which resource', 'resource detail', 'resource name')): extra.add('RESOURCE_PRESSURE')
    if any(p in question for p in ('how many days', 'scenario duration', 'duration of')): extra.add('SCENARIO_DURATION')
    choices = [c for c in choices if c['kind'] in required | extra] if required else choices
    schema = json_schema(GroundedResponseSlots)
    slots = schema['properties']['claims']; all_props = slots['properties']; props = {}
    for kind in dict.fromkeys(c['kind'] for c in choices):
        prop = next(p for p in all_props[kind]['anyOf'] if p.get('type') != 'null')
        combinations = [c['required_fact_ids'] for c in choices if c['kind'] == kind]
        refs = prop['properties']['evidence_refs']
        refs['items'] = {'type': 'string', 'enum': list(dict.fromkeys(i for ids in combinations for i in ids))}
        refs['minItems'] = min(map(len, combinations)); refs['maxItems'] = max(map(len, combinations))
        props[kind] = prop
    slots['properties'] = props; slots['required'] = [k for k in props if k in required]
    contract = {'protocol': VERSION, 'allowed_claims': choices,
                'instruction': 'Fill the named claim slots with ALL exact required_fact_ids for each. There is no kind list. A slot appears once. No prose, values, null required slots or extra fields. Do not replace or repair evidence.'}
    if isinstance(data, list):
        transformed = deepcopy(data)
        for item in transformed:
            original = json.loads(item['result'][0]['text'])
            row = next(v for v in views if v['evidence_id'] == original['evidence_id'])
            item['result'][0]['text'] = json.dumps({**row, 'current_evidence_catalogue': views, 'semantic_contract': contract}, ensure_ascii=False)
        return transformed, schema
    original = json.loads(data)
    handles = {k: original[k] for k in ('active_scenario_id', 'active_optimization_id') if k in original}
    return json.dumps({**handles, 'question': request.message, 'context': request.model_dump(exclude={'message', 'request_id', 'conversation_id'}),
        'server_prefetched_evidence': views, 'semantic_contract': contract}, ensure_ascii=False), schema


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: reject('duplicate_slot_property')
            result[key] = value
        return result
    return GroundedResponseSlots.model_validate(json.loads(raw, object_pairs_hook=unique)).as_frame()


INSTRUCTION = '\nFINAL SEMANTIC SLOTS: Return only the named claims object from the schema; each semantic slot contains evidence_refs only. Fill every required slot with its exact current fact IDs. No claim list and no kind/text/value fields. Select the relevant authoritative evidence; the server writes all prose and exact numbers. Native calculations are already complete. Never output explanations, reasons, resource names, quantities or durations. This contract overrides the legacy prose synthesis contract.\n'
