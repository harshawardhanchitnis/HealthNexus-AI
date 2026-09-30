"""Read-only geographic/action metadata; no planning calculations."""

ACTION_STATE = {'plan_mode': 'advisory', 'physical_execution': False,
    'externally_authorized': False, 'hospital_contacted': False,
    'real_world_transfer_status': 'not_executed'}


def plan_geography(plan, snapshot):
    names = {d.id: d.name for d in snapshot.districts}
    districts = sorted({t.donor_district_id for t in plan.transfers if t.donor_district_id})
    return {'donor_scope': plan.preview.request.scope,
        'receiver_district_id': plan.preview.request.district_id,
        'receiver_district_name': names.get(plan.preview.request.district_id),
        'donor_districts': [{'id': d, 'name': names[d]} for d in districts],
        'donor_district_count': len(districts),
        'cross_district_lane_count': sum(t.cross_district for t in plan.transfers),
        'total_lane_count': len(plan.transfers), 'action_state': dict(ACTION_STATE),
        'distance_method': 'Haversine geographic proxy; not road distance or travel time',
        'quantity_basis': 'mixed-resource inventory-item accounting sums; physical units remain per lane'}
