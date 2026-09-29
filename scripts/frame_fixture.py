"""Shared deterministic test transport fixture; never called by a live transport."""
import json


def mock_frame(body):
    data = body['input']
    if isinstance(data, str):
        data = json.loads(data)
    else:
        data = json.loads(data[0]['result'][0]['text'])
    choices = data['semantic_contract']['allowed_claims']
    available = {c['kind']: c['required_fact_ids'] for c in choices}
    if 'PUBLIC_AGGREGATE_INPUT' in available:
        order = ['PUBLIC_AGGREGATE_INPUT', 'SIMULATED_FACILITY_OPERATIONS', 'MODEL_BASED_FORECAST',
            'SCENARIO_PROJECTION', 'ADVISORY_OPTIMIZATION', 'WAPE_ERROR_METRIC',
            'NOT_CLINICALLY_VALIDATED', 'NO_LIVE_GOVERNMENT_CONNECTION', 'EXPERIMENTAL_FEDERATION']
    elif 'EXECUTION_STATUS' in available: order = ['EXECUTION_STATUS']
    elif 'SOLVER_STATUS' in available: order = ['SOLVER_STATUS']
    elif 'NO_SAFE_DONOR_CAPACITY' in available:
        order = ['NO_SAFE_DONOR_CAPACITY', 'NO_RECOMMENDED_REDISTRIBUTION', 'REMAINING_SHORTAGE']
    elif 'why' in data.get('question', '').lower():
        order = ['DONOR_PROTECTION', 'ELIGIBLE_CAPACITY', 'REMAINING_SHORTAGE']
    else:
        order = ['NETWORK_PRESSURE', 'ADVISORY_REDISTRIBUTION', 'PARTIAL_RELIEF',
                 'DONOR_PROTECTION', 'ELIGIBLE_CAPACITY', 'REMAINING_SHORTAGE']
    return {'claims': {k: {'evidence_refs': available[k]} for k in order if k in available}}
