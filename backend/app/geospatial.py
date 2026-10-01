"""Read-only geographic projections of existing operational engine objects."""
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from app.models.provenance import CountryCode
from app.profiles.config import ProfileID, NOTICES
from app.profiles.access import snapshot_for
from app.profiles.identity import fingerprint
from app.scenarios.engine import select
from app.services.summary import summarize
from app.optimization.geography import ACTION_STATE
from app.forecasting.prediction import ModelUnavailable
from app.map_coordinates import map_coordinates, VERSION
from app.optimization.distance import haversine
from app.core.runtime import compute_scope

Mode = Literal['network', 'forecast', 'emergency', 'redistribution']
STATUS = {'NORMAL': 'HEALTHY', 'INFO': 'HEALTHY', 'WARNING': 'AT_RISK'}


def collection(features):
    return {'type': 'FeatureCollection', 'features': features}


def read_map(snapshot, engine, planner, mode='network', state_id=None, district_id=None,
             scenario_id=None, run_id=None, donor_scope=None, resource=None, status=None, facility_type=None):
    facilities = select(snapshot, state_id, district_id)
    lookup = {f.id: f for f in snapshot.facilities}
    selected_ids = {f.id for f in facilities}
    projections, warnings, plan = {}, [], None
    scenario = None
    if scenario_id:
        scenario = engine.store.get(scenario_id, snapshot.country, snapshot.operational_profile)
        definition = scenario.scenario.definition
        original = select(snapshot, definition.state_id, definition.district_id, definition.facility_ids)
        if scenario.scenario.baseline_snapshot_id != fingerprint(snapshot, original) or scenario.scenario.origin != snapshot.as_of:
            raise ValueError('Scenario baseline/origin is stale')
        if not selected_ids.intersection(f.facility_id for f in scenario.scenario_result.facilities):
            raise ValueError('Scenario does not overlap selected geography')
        bundle = engine.forecasts.bundle(snapshot.country, snapshot.operational_profile)
        if any(f.provenance.model_sha256 != bundle.get('artifact_sha256') for f in scenario.scenario_result.facilities):
            raise ValueError('Scenario model identity is stale')
    if run_id:
        plan = planner.get(run_id, snapshot.country, snapshot.operational_profile)
        req = plan.preview.request
        if (req.state_id, req.district_id, req.scenario_id) != (state_id, district_id, scenario_id):
            raise ValueError('Optimization overlay does not match geography/scenario')
        if donor_scope and req.scope != donor_scope:
            raise ValueError('Optimization donor scope does not match')
        scope = select(snapshot, req.state_id if req.scope in ('state', 'cross_district') else None,
            req.district_id if req.scope == 'district' else None)
        if plan.preview.snapshot_id != fingerprint(snapshot, scope) or plan.preview.origin != snapshot.as_of:
            raise ValueError('Optimization baseline/origin is stale')
        bundle = engine.forecasts.bundle(snapshot.country, snapshot.operational_profile)
        if plan.preview.model_version != bundle['report']['model_version'] or any(
            f.provenance.model_sha256 != bundle.get('artifact_sha256') for f in plan.before):
            raise ValueError('Optimization model identity is stale')
    if mode == 'forecast':
        compute_scope(facilities)
        outcome, listing = engine.baseline(snapshot, facilities)
        projections = {f.facility_id: f for f in outcome.facilities}; warnings = listing.items
    elif mode == 'emergency':
        if not scenario: raise ValueError('Emergency map requires scenario_id')
        projections = {f.facility_id: f for f in scenario.scenario_result.facilities}
        warnings = scenario.warnings_created.items
    elif mode == 'redistribution':
        if not plan: raise ValueError('Redistribution map requires run_id')
        # Include out-of-district donors while retaining the selected receiver network.
        ids = selected_ids | {t.donor_id for t in plan.transfers} | {t.receiver_id for t in plan.transfers}
        facilities = [lookup[i] for i in sorted(ids)]
        projections = {f.facility_id: f for f in plan.after}; warnings = plan.after_warnings.items
    states = {s.id: s.name for s in snapshot.regions}; districts = {d.id: d.name for d in snapshot.districts}
    features = []
    for f in facilities:
        projection = projections.get(f.id)
        raw_status = projection.status if projection else f.status.value
        display_status = STATUS.get(raw_status, raw_status)
        if status and display_status != status or facility_type and f.type != facility_type: continue
        current = summarize([f])
        signals = [{'resource_id': r.resource_id, 'name': r.name, 'unit': r.unit,
            'stockout_risk_14': r.stockout.probabilities['14'], 'expected_unmet': r.unmet_total}
            for r in projection.resources] if projection else []
        features.append({'type': 'Feature', 'id': f.id, 'geometry': {'type': 'Point',
            'coordinates': map_coordinates(f)}, 'properties': {'facility_id': f.id,
            'name': f.name, 'facility_type': f.type, 'country_id': f.country_id,
            'state_id': f.state_id, 'state_name': states[f.state_id], 'district_id': f.district_id,
            'district_name': districts.get(f.district_id, f.district_name), 'status': display_status,
            'source_status': raw_status, 'medicine_availability': current['medicine_availability'],
            'bed_utilisation': current['bed_utilisation'], 'staff_availability': current['staff_availability'],
            'forecast_signals': signals, 'warnings': [w.model_dump(mode='json') for w in warnings if w.facility_id == f.id],
            'scenario_affected': bool(scenario and f.id in {p.facility_id for p in scenario.scenario_result.facilities}),
            'role': 'receiver' if plan and any(t.receiver_id == f.id for t in plan.transfers)
                    else 'donor' if plan and any(t.donor_id == f.id for t in plan.transfers) else 'facility',
            'simulated': True, 'illustrative_coordinates': True}})
    visible = {f['id'] for f in features}
    lines = []
    if mode == 'redistribution':
        for t in plan.transfers:
            if resource and resource != t.resource_id: continue
            if t.donor_id not in visible or t.receiver_id not in visible: continue
            d, r = lookup[t.donor_id], lookup[t.receiver_id]
            dc, rc = map_coordinates(d), map_coordinates(r)
            props = t.model_dump(mode='json')
            props.update(donor_district_name=districts.get(d.district_id), receiver_district_name=districts.get(r.district_id),
                donor_state_name=states[d.state_id], receiver_state_name=states[r.state_id], action_state=dict(ACTION_STATE),
                label='Recommended Transfer Lane', distance_method='Haversine geographic proxy',
                map_distance_km=haversine(dc[1], dc[0], rc[1], rc[0]),
                optimizer_distance_notice='Original illustrative optimizer input; preserved separately from map geometry')
            lines.append({'type': 'Feature', 'id': t.transfer_id, 'properties': props,
                'geometry': {'type': 'LineString', 'coordinates': [dc, rc]}})
    return {'metadata': {'mode': mode, 'origin': str(snapshot.as_of), 'country_id': snapshot.country,
        'profile': snapshot.operational_profile, 'profile_version': snapshot.profile_version,
        'state_id': state_id, 'district_id': district_id, 'scenario_id': scenario_id, 'run_id': run_id,
        'donor_scope': plan.preview.request.scope if plan else donor_scope,
        'data_notice': NOTICES[snapshot.operational_profile],
        'geometry_notice': 'Illustrative facility locations; fictional prototype facilities',
        'map_coordinate_version': VERSION, 'surveyed_coordinates': False,
        'data_type': 'calibrated simulated operations', 'live_government_inventory': False,
        'action_state': dict(ACTION_STATE)}, 'geography': {'states': [r.model_dump() for r in snapshot.regions],
        'districts': [d.model_dump() for d in snapshot.districts]},
        'facilities': collection(features), 'transfers': collection(lines),
        'summary': {'visible_facilities': len(features), 'visible_lanes': len(lines),
            'plan': {'geography': plan.geography, 'safe_capacity': plan.preview.safe_capacity,
                'target_before': plan.preview.total_deficit, 'planned_accounting_items': plan.impact.transferred_units,
                'unresolved': plan.impact.after.target_deficit, 'donor_violations': plan.impact.donor_safety_violations,
                'new_donor_risks': plan.impact.new_donor_risks} if mode == 'redistribution' else None}}


def geospatial_router(engine, planner):
    router = APIRouter(prefix='/api/geospatial', tags=['geospatial'])

    @router.get('')
    def view(request: Request, country_id: CountryCode = 'IN', profile: ProfileID = 'constrained',
             mode: Mode = 'network', state_id: str | None = None, district_id: str | None = None,
             scenario_id: str | None = None, run_id: str | None = None,
             donor_scope: Literal['district','cross_district','state','national'] | None = None,
             resource: Literal['PCM','IVF','ORS','AMX','IFA'] | None = None,
             status: Literal['HEALTHY','WATCH','AT_RISK','CRITICAL'] | None = None, facility_type: str | None = None):
        try:
            return read_map(snapshot_for(request, country_id, profile), engine, planner, mode, state_id,
                district_id, scenario_id, run_id, donor_scope, resource, status, facility_type)
        except LookupError as e: raise HTTPException(404, str(e))
        except ModelUnavailable as e: raise HTTPException(503, str(e))
        except ValueError as e: raise HTTPException(422, str(e))
    return router
