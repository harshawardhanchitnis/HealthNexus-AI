"""Compact model context; complete authoritative objects remain in the response."""
import json
from app.ai.numeric import numeric_leaves, field_unit


def compact(tool, payload):
    keys = {
        'run_emergency_scenario': ('context','scenario','scenario_id','model_versions','resource_impact','warnings_after'),
        'get_scenario_comparison': ('context','scenario_id','model_versions','resource_impact','warnings_before','warnings_after'),
        'get_redistribution_preview': ('context','request','model_version','policy_version','total_deficit','safe_capacity',
            'capacity_by_resource','deficit_by_resource','receiver_pairs','donor_pairs','feasible_lanes','donors','limitations'),
        'optimize_redistribution': ('context','run_id','scenario_id','model_version','policy_version','solver','safe_capacity',
            'impact','action_state','resource_units','resource_risks','transfers','transfers_total','transfers_truncated','unit_notice'),
        'get_optimization_result': ('context','run_id','scenario_id','model_version','policy_version','solver','safe_capacity',
            'impact','action_state','resource_units','resource_risks','transfers','transfers_total','transfers_truncated','unit_notice'),
        'get_data_provenance': ('context','data_type','purpose','seed','live_government_inventory','model_version','model_sha256','sources'),
        'get_model_performance': ('context','model_version','data_type','operational_profile','profile_version','windows',
            'selection_rule','uncertainty_method','source_vintage_note','targets'),
    }.get(tool)
    result={k:payload[k] for k in keys if k in payload} if keys else dict(payload)
    if 'scenario' in result:
        result['scenario']={k:v for k,v in result['scenario'].items() if k!='assumptions'}
    if tool=='get_model_performance':
        result['targets']={target:{**{k:v for k,v in row.items() if k!='models'},
            'models':{name:{'test':metrics['test']} for name,metrics in row['models'].items()}}
            for target,row in payload['targets'].items()}
    if 'transfers' in result:
        seen=set();rows=[]
        for transfer in result['transfers']:
            row={k:transfer[k] for k in ('donor_id','donor_name','receiver_id','receiver_name','resource_id','unit',
                'quantity','distance_km','donor_protected_reserve','donor_protected_minimum_after',
                'donor_risk_after','receiver_deficit_after','receiver_warning_after','receiver_risk_after')}
            if transfer['donor_id'] not in seen:row['rationale']=transfer['rationale']
            seen.add(transfer['donor_id']);rows.append(row)
        # Preserve every row's index/quantity. Drop repeated metadata, not authoritative values.
        result['transfers']=rows
    return result


def byte_size(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(',',':')).encode('utf-8'))


def model_record(eid, tool, payload, *, summary_only=False):
    result=compact(tool,payload)
    if summary_only and tool=='get_network_summary':
        # Geography is already validated; nationwide discovery catalogues are irrelevant to this summary.
        result={k:result[k] for k in ('context','summary','warnings','model_version','facilities','facilities_truncated') if k in result}
    provenance={k:v for k,v in {'origin':payload.get('context',{}).get('origin'),
        'model_version':payload.get('model_version')}.items() if v is not None}
    facts=[]
    for path,value in numeric_leaves(result):
        facts.append({'evidence_id':eid,'path':path,'value':value,'quote':str(value),
            'unit':field_unit(tool,path,payload),'provenance':provenance})
        if len(facts)>=32:break
    return {'evidence_id':eid,'tool':tool,'result':result,'numeric_facts':facts}
