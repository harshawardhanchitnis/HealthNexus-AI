"""Reproduce district and strict cross-district plans with zero provider calls."""
import argparse
from collections import defaultdict
from math import ceil, isclose
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.repository import LocalRepository
from app.scenarios.engine import ScenarioEngine
from app.scenarios.models import ScenarioRequest
from app.optimization.service import OptimizationService
from app.optimization.schemas import RedistributionRequest
from app.optimization.config import POLICY
from app.optimization.distance import haversine


def measured(plan):
    return {'target_before': plan.preview.total_deficit, 'safe_capacity': plan.preview.safe_capacity,
        'planned_accounting_items': plan.impact.transferred_units, 'lanes': len(plan.transfers),
        'unresolved': plan.impact.after.target_deficit,
        'donor_violations': plan.impact.donor_safety_violations, 'new_donor_risks': plan.impact.new_donor_risks,
        'solver_status': plan.solver.status, 'geography': plan.geography,
        'before': plan.impact.before.model_dump(), 'after': plan.impact.after.model_dump()}


def validate(plan, snapshot, service):
    request = plan.preview.request
    preview, projections, paths, _ = service.prepare(snapshot, request)
    facility = {f.id: f for f in snapshot.facilities}
    candidates = {(d.facility_id, d.resource_id): d for d in preview.donors}
    projected = {(f.facility_id, r.resource_id): r for f in projections for r in f.resources}
    outgoing = defaultdict(int)
    for t in plan.transfers:
        d, r = facility[t.donor_id], facility[t.receiver_id]
        assert d.country_id == r.country_id == request.country_id
        if request.scope == 'cross_district':
            assert d.state_id == r.state_id == request.state_id
            assert d.district_id != r.district_id == request.district_id
            assert t.cross_district and t.donor_district_id == d.district_id
        assert t.receiver_district_id == r.district_id and t.donor_state_id == d.state_id
        assert all(next(i for i in f.inventory if i.medicine_id == t.resource_id).unit == t.unit for f in (d, r))
        assert isclose(t.distance_km, haversine(d.latitude, d.longitude, r.latitude, r.longitude), abs_tol=1e-9)
        assert t.quantity > 0 and t.donor_stock_after >= 0 and t.plan_mode == 'advisory'
        assert t.donor_protected_minimum_after >= t.donor_protected_reserve
        assert all(t.donor_risk_after[h] <= t.donor_risk_before[h] for h in ('3', '7', '14'))
        outgoing[(d.id, t.resource_id)] += t.quantity
    for key, amount in outgoing.items():
        d, r = candidates[key], projected[key]
        point = np.array([v.point for v in r.forecast])
        receipts = np.array([v.expected_receipts for v in r.stockout.trajectory])
        assert paths[key].shape == (500, 14)
        current = d.current_stock - amount
        assert current >= max(d.protected_reserve, ceil(point.mean() * POLICY.minimum_current_cover_days))
        assert np.min(current + np.cumsum(receipts - point)) >= d.protected_reserve
        assert np.min(current + np.cumsum(receipts[None, :] - paths[key], axis=1)) >= d.protected_reserve
        assert amount <= d.safe_surplus
    assert plan.impact.donor_safety_violations == plan.impact.new_donor_risks == 0
    assert all(v['before'] == v['after'] for v in plan.impact.conservation.values())
    assert sum(t.quantity for t in plan.transfers) == plan.impact.transferred_units
    state = plan.geography['action_state']
    assert state['plan_mode'] == 'advisory' and all(state[k] is False for k in ('physical_execution', 'externally_authorized', 'hospital_contacted'))
    return 'PASS'


def verify():
    repo = LocalRepository(); engine = ScenarioEngine(); planner = OptimizationService(engine)
    report = {'baseline': '723c6a8', 'live_gemini_requests': 0, 'profiles': {}}
    for profile in ('redistribution-ready', 'constrained'):
        snapshot = repo.profile_snapshot('IN', profile); before = snapshot.model_dump_json()
        scenario = engine.run(snapshot, ScenarioRequest(country_id='IN', profile=profile, state_id='MH',
            district_id='MH-PUNE', scenario_type='DENGUE_SURGE', severity='severe', duration=14, seed=42))
        district = planner.run(snapshot, RedistributionRequest(country_id='IN', profile=profile, state_id='MH',
            district_id='MH-PUNE', scenario_id=scenario.scenario.scenario_id, scope='district'))
        validate(district, snapshot, planner)
        expected = (41763,17745,15679,10,26084) if profile == 'redistribution-ready' else (30230,0,0,0,30230)
        assert (district.preview.total_deficit, district.preview.safe_capacity, district.impact.transferred_units,
            len(district.transfers), district.impact.after.target_deficit) == expected
        cross = planner.run(snapshot, district.preview.request.model_copy(update={'scope': 'cross_district'}))
        validate(cross, snapshot, planner)
        if profile == 'redistribution-ready':
            assert cross.geography['cross_district_lane_count'] > 0 and cross.preview.safe_capacity > 0 and cross.impact.transferred_units > 0
        assert snapshot.model_dump_json() == before
        report['profiles'][profile] = {'district': measured(district), 'cross_district': measured(cross),
            'lanes': [t.model_dump(mode='json') for t in cross.transfers], 'paired_demand_path_safety': 'PASS',
            'baseline_immutable': True, 'scenario_id': scenario.scenario.scenario_id, 'run_id': cross.run_id}
    report['status'] = 'PASS'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=ROOT/'docs/evaluation/phase9-cross-district.json')
    args = parser.parse_args(); report = verify(); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'live_gemini_requests': 0,
        'cross_district': report['profiles']['redistribution-ready']['cross_district']}, indent=2))
