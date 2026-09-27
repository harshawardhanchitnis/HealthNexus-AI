"""Stateless deterministic rules. Repeated reads cannot append duplicate warnings."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from app.core import risk_config as C
from app.warnings.models import Warning, WarningList, WarningSummary


def evaluate(facility, origin, scenario_id=None, scenario_type=None, baseline=None):
    f = facility
    result = {}
    old = {(w.warning_type.value, w.resource_id): w for w in baseline or [] if w.facility_id == f.facility_id}

    def add(kind, category, severity, current, threshold, predicted, event, factors, resource=None, probability=None):
        identity = f"{f.country_id}:{f.facility_id}:{kind}:{resource}:{scenario_id or 'baseline'}:{origin}"
        days = max(0, (event-origin).days) if event else C.HORIZON
        patients = sum(d.footfall for d in f.timeline)
        weights = C.PRIORITY_WEIGHTS
        priority = (C.SEVERITY_RANK[severity]*weights["severity"] + weights["urgency"]*(1-min(C.HORIZON, days)/C.HORIZON)
            + weights["probability"]*(probability or 0) + weights["patients"]*min(1, patients/C.PRIORITY_PATIENT_SCALE)
            + weights["hospital"]*("Hospital" in f.facility_type))
        previous = old.get((kind, resource))
        transition = "baseline"
        if scenario_id:
            transition = "new" if not previous else "worsened" if C.SEVERITY_RANK[severity] > C.SEVERITY_RANK[previous.severity.value] else "improved" if C.SEVERITY_RANK[severity] < C.SEVERITY_RANK[previous.severity.value] else "unchanged"
        warning = Warning(warning_id=hashlib.sha256(identity.encode()).hexdigest()[:24], warning_type=kind, category=category,
            severity=severity, country_id=f.country_id, state_id=f.state_id, district_id=f.district_id,
            facility_id=f.facility_id, facility_name=f.facility_name, resource_id=resource,
            generated_at=datetime.now(timezone.utc), forecast_origin=origin,
            current_value=current, threshold=threshold, predicted_value=predicted, estimated_event_date=event,
            model_based_probability=probability, baseline_or_scenario="scenario" if scenario_id else "baseline", scenario_id=scenario_id,
            explanation_factors=[dict(factor=k, value=v, description=d) for k, v, d in factors],
            provenance={"config_version": C.CONFIG_VERSION, "is_synthetic": True, "source": "Phase 3 saved forecasts + deterministic operational propagation",
                "baseline_model": f.source_models.get(resource or ("admissions" if category == "beds" else "footfall"), "unknown"),
                "uncertainty": "conditional_on_scenario" if scenario_id else "empirical_calibration_residuals"},
            model_version=f.provenance.model_version, priority_score=round(priority, 4),
            baseline_severity=previous.severity if previous else None, transition=transition)
        result[warning.warning_id] = warning

    for r in f.resources:
        s = r.stockout
        factors = [("days_of_cover", s.days_of_cover if s.days_of_cover is not None else "undefined", "Current inventory / mean 14-day requested demand; receipts excluded."),
            ("requested_demand", r.requested_total, f"Model-derived 14-day requested demand in {r.unit}."),
            ("stockout_risk_7d", s.probabilities["7"], "Fraction of paired residual paths reaching zero within seven days.")]
        if s.days_of_cover is not None and s.days_of_cover < C.LOW_COVER_DAYS:
            add("LOW_STOCK", "medicine", "CRITICAL" if s.days_of_cover < C.CRITICAL_DAYS else "WARNING", s.days_of_cover, C.LOW_COVER_DAYS, s.days_of_cover, origin, factors, r.resource_id)
        if s.safety_breach_date:
            add("SAFETY_STOCK_BREACH", "medicine", "WARNING" if (s.safety_breach_date-origin).days <= 7 else "WATCH", s.current_stock, s.safety_stock,
                min(p.closing_stock for p in s.trajectory), s.safety_breach_date, factors, r.resource_id)
        if s.stockout_date:
            add("PREDICTED_STOCKOUT", "medicine", "CRITICAL" if (s.stockout_date-origin).days <= C.CRITICAL_DAYS else "WARNING", s.current_stock, 0, 0, s.stockout_date, factors, r.resource_id, s.probabilities["14"])
        if s.probabilities["14"] >= C.RISK_WATCH:
            severity = "CRITICAL" if s.probabilities["3"] >= C.RISK_CRITICAL else "WARNING" if s.probabilities["7"] >= C.RISK_WARNING else "WATCH"
            risk_day = 3 if severity == "CRITICAL" else 7 if severity == "WARNING" else 14
            add("HIGH_STOCKOUT_RISK", "medicine", severity, None, C.RISK_WATCH, s.probabilities["14"], s.stockout_date,
                factors+[("risk_horizon_days", risk_day, "Severity uses 3-day 80%, 7-day 50%, then 14-day 20% thresholds.")], r.resource_id, s.probabilities["14"])
        changes = [c for c in f.receipt_changes if c.resource_id == r.resource_id]
        if changes:
            add("DELIVERY_DELAY", "medicine", "WARNING" if s.safety_breach_date else "INFO", 0, 0,
                max((c.projected_date-c.original_date).days for c in changes), min(c.original_date for c in changes),
                [("shifted_receipts", len(changes), "Only orders placed by origin with arrivals inside the selected event window are shifted.")], r.resource_id)
    days = f.timeline
    future_mean = sum(d.footfall for d in days)/len(days)
    growth = future_mean/max(1, f.baseline_recent_daily_mean)-1
    if growth >= C.SURGE_WATCH:
        severity = "CRITICAL" if growth >= C.SURGE_CRITICAL else "WARNING" if growth >= C.SURGE_WARNING else "WATCH"
        rolling = [p.value for p in f.history[-6:]]+[d.footfall for d in days]
        first_surge = next((d.date for i, d in enumerate(days) if sum(rolling[i:i+7])/7/max(1, f.baseline_recent_daily_mean)-1 >= C.SURGE_WATCH), None)
        add("PATIENT_SURGE", "demand", severity, 0., C.SURGE_WATCH, growth, first_surge,
            [("forecast_demand_growth", growth, "Projected 14-day mean versus observed trailing 7-day mean. Event date is the first rolling 7-day mean crossing 15% growth.")])
    history = [p.value for p in f.history]
    import numpy as np
    threshold = float(np.mean(history[:-1])+C.ABNORMAL_STD*np.std(history[:-1]))
    if history[-1] > threshold:
        add("ABNORMAL_FOOTFALL", "demand", "WATCH", history[-1], threshold, None, origin,
            [("historical_upper_threshold", threshold, "Latest observed day exceeds prior 27-day mean + 3 standard deviations; descriptive only.")])
    peak = max((d.occupancy_ratio or 0 for d in days), default=0)
    if peak >= C.OCCUPANCY_WATCH:
        day = next(d for d in days if (d.occupancy_ratio or 0) >= C.OCCUPANCY_WATCH)
        add("HIGH_BED_OCCUPANCY", "beds", "WARNING" if peak >= C.OCCUPANCY_WARNING else "WATCH", f.current_occupancy_ratio, C.OCCUPANCY_WATCH, peak, day.date,
            [("peak_occupancy_ratio", peak, "Occupied / usable beds after deterministic admissions and discharges.")])
    failures = [d for d in days if d.unmet_admissions > 1e-8 or d.bed_overflow > 1e-8]
    if failures:
        first = failures[0]
        add("PREDICTED_BED_CAPACITY_BREACH", "beds", "CRITICAL" if (first.date-origin).days <= C.CRITICAL_DAYS else "WARNING", days[0].opening_occupied, first.bed_capacity,
            first.opening_occupied-first.discharges+first.admissions_requested, first.date,
            [("unmet_admissions", sum(d.unmet_admissions for d in days), "Requested admissions above available beds; overflow of existing occupants is explicit."),
             ("peak_existing_overflow", max(d.bed_overflow for d in days), "Existing occupants above temporarily reduced capacity are retained, not silently removed.")])
    availability = min(d.available_staff/d.scheduled_staff for d in days)
    if availability < C.STAFF_WATCH:
        severity = "CRITICAL" if availability < C.STAFF_CRITICAL else "WARNING" if availability < C.STAFF_WARNING else "WATCH"
        first = next(d for d in days if d.available_staff/d.scheduled_staff < C.STAFF_WATCH)
        add("STAFF_SHORTAGE", "personnel", severity, f.current_staff_fraction, C.STAFF_WATCH, availability, first.date,
            [("available_fraction", availability, "Present staff / scheduled staff; schedules unchanged.")])
    overloaded = [d for d in days if d.workload_ratio is None or d.workload_ratio > C.WORKLOAD_WARNING]
    if overloaded:
        peak_work = max((d.workload_ratio or 0 for d in days), default=0)
        zero = any(d.service_capacity == 0 for d in days)
        add("HIGH_WORKLOAD", "personnel", "CRITICAL" if zero or peak_work >= C.WORKLOAD_CRITICAL else "WARNING", f.current_workload_ratio, C.WORKLOAD_WARNING,
            None if zero else peak_work, overloaded[0].date,
            [("unserved_patients", sum(d.unserved_patients for d in days), "Demand above available operational service capacity; no clinical treatment effect inferred.")])
    if scenario_type == "FACILITY_DISRUPTION":
        add("FACILITY_DISRUPTION", "emergency", "CRITICAL" if any(d.service_capacity == 0 for d in days) else "WARNING", None, None,
            min(d.bed_capacity for d in days), next(d.date for d in days if d.bed_capacity == min(x.bed_capacity for x in days)),
            [("minimum_service_capacity", min(d.service_capacity for d in days), "Specified loss of facility capability; no patient spillover or medicine transfers.")])
    critical_domains = {w.category for w in result.values() if w.severity.value == "CRITICAL"}
    if scenario_id and len(critical_domains) >= C.ESCALATION_DOMAINS:
        add("EMERGENCY_ESCALATION", "emergency", "CRITICAL", None, C.ESCALATION_DOMAINS, len(critical_domains), None,
            [("critical_domains", len(critical_domains), "At least two distinct operational domains have critical warnings.")])
    return sorted(result.values(), key=lambda w: (-w.priority_score, w.warning_id))


def summarize(items):
    def counts(rows):
        c = Counter(w.severity.value for w in rows)
        return {s: c[s] for s in C.SEVERITY_RANK}
    def group(key):
        groups = defaultdict(list)
        for w in items:
            value = getattr(w, key)
            if value is not None:
                groups[value].append(w)
        return {k: counts(v) for k, v in groups.items()}
    return WarningSummary(total=len(items), counts=counts(items), facilities_affected=len({w.facility_id for w in items}),
        medicines_at_risk=len({w.resource_id for w in items if w.category == "medicine" and w.warning_type.value != "DELIVERY_DELAY"}),
        bed_warnings=sum(w.category == "beds" for w in items), staff_warnings=sum(w.category == "personnel" for w in items),
        by_country=group("country_id"), by_region=group("state_id"), by_district=group("district_id"), by_facility=group("facility_id"))


def listing(items):
    unique = {w.warning_id: w for w in items}
    ordered = sorted(unique.values(), key=lambda w: (-w.priority_score, w.warning_id))
    return WarningList(items=ordered, summary=summarize(ordered))
