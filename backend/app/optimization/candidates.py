from math import ceil, floor
import numpy as np
from app.core.risk_config import SEVERITY_RANK
from app.optimization.config import POLICY as P
from app.optimization.distance import haversine
from app.optimization.schemas import Candidate, Edge


def protection(current, safety, point, paths, receipts):
    """Raw balances (no clipping hides unmet demand); origin plus every future day."""
    reserve = ceil(safety * P.reserve_multiplier) + P.reserve_buffer_units
    raw = current + np.cumsum(receipts-point)
    sampled = current + np.cumsum(receipts[None, :]-paths, axis=1)
    minimum = min(float(current), float(raw.min()), float(sampled.min()))
    current_floor = max(reserve, ceil(float(point.mean())*P.minimum_current_cover_days))
    surplus = max(0, floor(min(minimum-reserve, current-current_floor)))
    # A single arrival at origin covers maximum point-forecast cumulative shortfall,
    # including reserve and current-cover target, rather than summing daily deficits.
    deficit = max(0, ceil(max(reserve-float(raw.min()), current_floor-current)))
    return reserve, minimum, surplus, deficit


def candidates(projections, paths, warnings, origin, receiver_ids, resources):
    donors, receivers = [], []
    for f in sorted(projections, key=lambda f: f.facility_id):
        for r in sorted(f.resources, key=lambda r: r.resource_id):
            if r.resource_id not in resources:
                continue
            s = r.stockout
            point = np.array([p.point for p in r.forecast])
            receipts = np.array([p.expected_receipts for p in s.trajectory])
            reserve, minimum, surplus, deficit = protection(s.current_stock, s.safety_stock, point, paths[(f.facility_id, r.resource_id)], receipts)
            alerts = [w for w in warnings if w.facility_id == f.facility_id and w.resource_id == r.resource_id]
            severity = max((w.severity.value for w in alerts), key=lambda s: SEVERITY_RANK[s], default="INFO")
            priority = max((w.priority_score for w in alerts), default=0.)
            days = max(0, min(14, (s.stockout_date-origin).days)) if s.stockout_date else 14
            weight = P.shortage_base_weight + P.severity_weight*SEVERITY_RANK[severity] + P.urgency_weight*(14-days) + round(P.probability_weight*s.probabilities["14"]) + round(P.priority_weight*priority)
            c = Candidate(facility_id=f.facility_id, facility_name=f.facility_name, country_id=f.country_id,
                state_id=f.state_id, district_id=f.district_id, resource_id=r.resource_id, unit=r.unit,
                current_stock=s.current_stock, protected_reserve=reserve, safe_surplus=surplus,
                protected_minimum_stock=minimum, reserve_after_max_donation=minimum-surplus,
                deficit=deficit, expected_unmet=r.unmet_total, depletion_date=s.stockout_date,
                safety_breach_date=s.safety_breach_date, risk=s.probabilities, severity=severity, priority=priority,
                critical=severity == "CRITICAL" or r.unmet_total > 1e-8, shortage_weight=weight)
            if surplus:
                donors.append(c)
            if deficit and f.facility_id in receiver_ids:
                receivers.append(c)
    return donors, receivers


def make_edges(donors, receivers, facilities, country, scope):
    edges = []
    for di, d in enumerate(donors):
        for ri, r in enumerate(receivers):
            if d.country_id != country or r.country_id != country or d.country_id != r.country_id:
                raise ValueError("International redistribution is prohibited")
            if d.resource_id != r.resource_id or d.unit != r.unit or d.facility_id == r.facility_id:
                continue
            same_state = d.state_id == r.state_id
            same_district = same_state and d.district_id is not None and d.district_id == r.district_id
            if scope == "state" and not same_state or scope == "district" and not same_district:
                continue
            if scope == "cross_district" and (not same_state or not d.district_id or not r.district_id or same_district):
                continue
            df, rf = facilities[d.facility_id], facilities[r.facility_id]
            distance = haversine(df.latitude, df.longitude, rf.latitude, rf.longitude)
            geo = 0 if same_district else P.cross_district_penalty if same_state else P.cross_state_penalty
            cost = round(distance)*P.distance_weight + geo + round(P.donor_risk_weight*d.risk["14"])
            edges.append(Edge(donor=di, receiver=ri, distance_km=distance, geographic_penalty=geo, unit_cost=cost))
    for di, d in enumerate(donors):
        d.nearest_receiver_distance_km = min((e.distance_km for e in edges if e.donor == di), default=None)
    return edges
