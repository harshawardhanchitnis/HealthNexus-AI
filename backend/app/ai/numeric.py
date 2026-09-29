"""Numeric representation only: no rounding, arithmetic or unit conversion."""
from decimal import Decimal, InvalidOperation
import math
import re

NUMBER = re.compile(r'[-+]?(?:(?:\d+(?:,\d{3})*)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?')
PERCENT_FIELDS = frozenset(('medicine_availability','bed_utilisation','staff_availability','percent_deficit_resolved'))


def canonical(token):
    try:
        value = Decimal(str(token).replace(',',''))
        return value if value.is_finite() else None
    except InvalidOperation:
        return None


def field_unit(tool, path, payload):
    leaf=path.rsplit('.',1)[-1]
    if leaf in PERCENT_FIELDS: return '%'
    if leaf=='wape': return 'WAPE fraction'
    if any(p in ('probabilities','risk_before','risk_after','donor_risk_after','receiver_risk_after','max_stockout_risk') for p in path.split('.')): return 'fraction'
    if leaf in ('facilities_at_risk','new_donor_risks'): return 'facilities'
    parent=payload
    try:
        for part in path.split('.')[:-1]: parent=parent[int(part)] if isinstance(parent,list) else parent[part]
    except (KeyError,IndexError,TypeError,ValueError): parent={}
    if isinstance(parent,dict) and isinstance(parent.get('unit'),str): return parent['unit']
    if isinstance(payload.get('unit'),str): return payload['unit']
    if tool in ('get_warning_summary','get_warnings') and path.startswith('summary.'): return 'warnings'
    if leaf=='facilities' or path.startswith('summary.status_counts.'): return 'facilities'
    if leaf in ('total_beds','occupied_beds','available_beds','reserved_beds'): return 'beds'
    if leaf in ('staff_present','staff_scheduled'): return 'staff'
    if leaf=='patient_footfall': return 'visits'
    if leaf in ('safe_capacity','target_deficit','transferred_units','shortage_units_resolved'): return 'accounting items'
    if leaf in ('horizon','duration'): return 'days'
    return None


def numeric_leaves(value, path=''):
    if isinstance(value,bool): return
    if isinstance(value,(int,float)):
        if not isinstance(value,float) or math.isfinite(value): yield path,value
    elif isinstance(value,dict):
        for key,child in value.items(): yield from numeric_leaves(child,f'{path}.{key}' if path else key)
    elif isinstance(value,list):
        for index,child in enumerate(value): yield from numeric_leaves(child,f'{path}.{index}' if path else str(index))


def numeric_sources(value, path, tool, payload):
    """Exact numbers belonging to the cited field, retaining their source units."""
    for field,number in numeric_leaves(value,path):
        yield canonical(number),field_unit(tool,field,payload)
    if isinstance(value,str):
        for match in NUMBER.finditer(value): yield canonical(match.group()),field_unit(tool,path,payload)
