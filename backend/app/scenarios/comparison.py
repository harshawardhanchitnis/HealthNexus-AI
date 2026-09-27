from app.core.risk_config import SEVERITY_RANK
from app.scenarios.models import Outcome, Metrics, MetricDelta, ResourceImpact


def outcome(facilities, warnings):
    for f in facilities:
        local = [w for w in warnings if w.facility_id == f.facility_id]
        f.status = max((w.severity.value for w in local), key=SEVERITY_RANK.get) if local else "NORMAL"
        f.priority_score = max((w.priority_score for w in local), default=0)
    facilities.sort(key=lambda f: (-f.priority_score, f.facility_id))
    days = [d for f in facilities for d in f.timeline]
    # Peak across facilities, not a national average that conceals local failure.
    occupancy = [d.occupancy_ratio for d in days]
    workload = [d.workload_ratio for d in days]
    return Outcome(facilities=facilities, metrics=Metrics(patient_demand=sum(d.footfall for d in days),
        admissions_requested=sum(d.admissions_requested for d in days), unmet_admissions=sum(d.unmet_admissions for d in days),
        unserved_patients=sum(d.unserved_patients for d in days),
        peak_bed_occupancy_percent=None if None in occupancy else 100*max(occupancy, default=0),
        peak_workload_ratio=None if None in workload else max(workload, default=0),
        max_stockout_probability=max((r.stockout.probabilities["14"] for f in facilities for r in f.resources), default=0),
        critical_facilities=sum(f.status == "CRITICAL" for f in facilities)))


def delta(a, b, unit="count"):
    return MetricDelta(baseline=a, scenario=b, absolute=None if a is None or b is None else b-a,
        percent=100*(b/a-1) if a and b is not None else None, unit=unit)


def compare(baseline, scenario):
    before, after = baseline.metrics.model_dump(), scenario.metrics.model_dump()
    deltas = {k: delta(a, after[k], "percentage points" if k == "peak_bed_occupancy_percent" else "probability fraction" if k == "max_stockout_probability" else "ratio" if k == "peak_workload_ratio" else "count") for k, a in before.items()}
    impact = []
    for code in sorted({r.resource_id for f in baseline.facilities for r in f.resources}):
        a = [r for f in baseline.facilities for r in f.resources if r.resource_id == code]
        b = [r for f in scenario.facilities for r in f.resources if r.resource_id == code]
        impact.append(ResourceImpact(resource_id=code, name=a[0].name, unit=a[0].unit,
            demand=delta(sum(r.requested_total for r in a), sum(r.requested_total for r in b), a[0].unit),
            unmet_demand=delta(sum(r.unmet_total for r in a), sum(r.unmet_total for r in b), a[0].unit),
            max_stockout_risk=delta(100*max(r.stockout.probabilities["14"] for r in a), 100*max(r.stockout.probabilities["14"] for r in b), "percentage points")))
    return deltas, impact
