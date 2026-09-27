from collections import defaultdict
import numpy as np
from app.forecasting.stockout import project_stock
from app.forecasting.schemas import StockRisk
from app.optimization.schemas import Impact, Metrics, Transfer
from app.optimization.config import POLICY as P
from app.warnings.engine import evaluate, listing
from app.core.risk_config import SEVERITY_RANK


def apply_plan(projections, paths, preview, quantities, origin, run_id, status, scenario_type=None):
    """Copy projections, conserve origin stocks, reuse paired demand/receipt paths."""
    donors, receivers, edges = preview.donors, preview.receivers, preview.edges
    if len(quantities) != len(edges) or any(type(q) is not int or q < 0 for q in quantities):
        raise ValueError("Transfers must be nonnegative integers aligned with edges")
    outgoing, incoming, net = defaultdict(int), defaultdict(int), defaultdict(int)
    for e, q in zip(edges, quantities):
        outgoing[e.donor] += q
        incoming[e.receiver] += q
        d, r = donors[e.donor], receivers[e.receiver]
        if d.country_id != r.country_id or d.resource_id != r.resource_id:
            raise ValueError("Invalid transfer association")
        net[(d.facility_id, d.resource_id)] -= q
        net[(r.facility_id, r.resource_id)] += q
    if any(outgoing[i] > d.safe_surplus for i, d in enumerate(donors)) or any(incoming[i] > r.deficit for i, r in enumerate(receivers)):
        raise ValueError("Plan exceeds donor or receiver capacity")
    after = [f.model_copy(deep=True) for f in projections]
    before_lookup = {(f.facility_id, r.resource_id): r for f in projections for r in f.resources}
    after_lookup = {}
    conservation = {c: {"before": 0, "after": 0} for c in preview.request.resources}
    before_warnings, after_warnings = [], []
    for original, f in zip(projections, after):
        affected = original.facility_id in preview.scenario_facility_ids
        sid = preview.request.scenario_id if affected else None
        kind = scenario_type if affected else None
        old_w = evaluate(original, origin, sid, kind)
        before_warnings.extend(old_w)
        for r in f.resources:
            key = (f.facility_id, r.resource_id)
            s = r.stockout
            current = s.current_stock + net[key]
            if r.resource_id in conservation:
                conservation[r.resource_id]["before"] += s.current_stock
                conservation[r.resource_id]["after"] += current
            if net[key]:
                point = np.array([p.point for p in r.forecast])
                receipts = np.array([p.expected_receipts for p in s.trajectory])
                r.stockout = StockRisk.model_validate(project_stock(current, s.safety_stock, point, paths[key], receipts, origin))
                r.stockout.method = "500 paired demand paths, unchanged receipts; planning transfers applied at origin before day 1. Conditional simulated estimate, not a transport guarantee."
                r.unmet_total = sum(p.unmet_demand for p in r.stockout.trajectory)
            after_lookup[key] = r
        updated = evaluate(f, origin, sid, kind, old_w)
        for w in updated:
            w.provenance["optimizer_run_id"] = run_id
        f.status = max((w.severity.value for w in updated), key=lambda v: SEVERITY_RANK[v], default="NORMAL")
        f.priority_score = max((w.priority_score for w in updated), default=0.)
        after_warnings.extend(updated)
    if any(c["before"] != c["after"] for c in conservation.values()):
        raise ValueError("Resource conservation failed")
    receiver_keys = {(r.facility_id, r.resource_id) for r in receivers}
    def relevant(w):
        return w.category == "medicine" and (w.facility_id, w.resource_id) in receiver_keys
    def metric(lookup, warnings, deficit):
        rows = [lookup[k] for k in receiver_keys]
        return Metrics(target_deficit=deficit, expected_unmet=sum(r.unmet_total for r in rows),
            critical_resource_warnings=sum(relevant(w) and w.severity.value == "CRITICAL" for w in warnings),
            facilities_at_risk=len({f for f, m in receiver_keys if lookup[(f, m)].stockout.probabilities["14"] >= .2 or lookup[(f, m)].stockout.safety_breach_date}),
            max_stockout_risk=max((r.stockout.probabilities["14"] for r in rows), default=0.))
    unresolved = {f"{r.facility_id}:{r.resource_id}": r.deficit-incoming[i] for i, r in enumerate(receivers)}
    violations, new_risks = 0, 0
    for i, d in enumerate(donors):
        if not outgoing[i]:
            continue
        a = after_lookup[(d.facility_id, d.resource_id)]
        violations += int(d.protected_minimum_stock-outgoing[i] < d.protected_reserve-1e-8 or a.stockout.current_stock < 0)
        new_risks += int(any(a.stockout.probabilities[h] > d.risk[h]+1e-8 for h in ("3", "7", "14")) or a.unmet_total > d.expected_unmet+1e-8 or a.stockout.safety_breach_date is not None)
    if violations or new_risks:
        raise ValueError("Donor protection failed post-transfer verification")
    total = sum(r.deficit for r in receivers)
    resolved = total-sum(unresolved.values())
    impact = Impact(before=metric(before_lookup, before_warnings, total), after=metric(after_lookup, after_warnings, total-resolved),
        shortage_units_resolved=resolved, percent_deficit_resolved=100*resolved/total if total else 0,
        critical_deficits_resolved=sum(r.critical and incoming[i] == r.deficit for i, r in enumerate(receivers)),
        critical_deficits_total=sum(r.critical for r in receivers),
        facilities_protected=len({r.facility_id for r in receivers if all(unresolved[f"{rr.facility_id}:{rr.resource_id}"] == 0 for rr in receivers if rr.facility_id == r.facility_id)}),
        donor_facilities_used=len({d.facility_id for i, d in enumerate(donors) if outgoing[i]}),
        transfer_count=sum(q > 0 for q in quantities), transferred_units=sum(quantities),
        distance_km=sum(e.distance_km for e, q in zip(edges, quantities) if q),
        distance_weighted_units=sum(e.distance_km*q for e, q in zip(edges, quantities)),
        donor_safety_violations=violations, new_donor_risks=new_risks, unresolved=unresolved, conservation=conservation)
    transfers = []
    for i, (e, q) in enumerate(zip(edges, quantities)):
        if not q:
            continue
        d, r = donors[e.donor], receivers[e.receiver]
        a, ra = after_lookup[(d.facility_id, d.resource_id)], after_lookup[(r.facility_id, r.resource_id)]
        severity = max((w.severity.value for w in after_warnings if w.facility_id == r.facility_id and w.resource_id == r.resource_id), key=lambda v: SEVERITY_RANK[v], default="NORMAL")
        transfers.append(Transfer(transfer_id=f"{run_id}-{i}", optimizer_run_id=run_id,
            donor_id=d.facility_id, donor_name=d.facility_name, receiver_id=r.facility_id, receiver_name=r.facility_name,
            resource_id=r.resource_id, unit=r.unit, quantity=q, distance_km=e.distance_km,
            donor_stock_before=d.current_stock, donor_stock_after=a.stockout.current_stock,
            donor_protected_reserve=d.protected_reserve, donor_projected_stock_after=min(p.closing_stock for p in a.stockout.trajectory),
            donor_protected_minimum_after=d.protected_minimum_stock-outgoing[e.donor],
            donor_risk_before=d.risk, donor_risk_after=a.stockout.probabilities,
            receiver_deficit_before=r.deficit, receiver_deficit_after=unresolved[f"{r.facility_id}:{r.resource_id}"],
            receiver_warning_before=r.severity, receiver_warning_after=severity,
            receiver_risk_before=r.risk, receiver_risk_after=ra.stockout.probabilities,
            rationale={"safe_surplus_before": d.safe_surplus, "receiver_expected_unmet_before": r.expected_unmet,
                "receiver_priority": r.priority, "target_units_supplied_by_this_transfer": q,
                "geographic_penalty_per_unit": e.geographic_penalty,
                "reserve_note": "Reported after values include every transfer in this plan; reserve checked across all paired paths."},
            optimization_status=status, objective_contribution={"critical_units_resolved": q if r.critical else 0,
                "weighted_units_resolved": q*r.shortage_weight, "transport_cost": q*e.unit_cost+P.transfer_count_penalty},
            scenario_id=preview.request.scenario_id, provenance={"snapshot_id": preview.snapshot_id,
                "scenario_snapshot_id": preview.scenario_snapshot_id or "baseline", "config_version": P.version,
                "model_version": preview.model_version, "data_status": "simulated"}))
    return impact, transfers, after, listing(before_warnings), listing(after_warnings)
