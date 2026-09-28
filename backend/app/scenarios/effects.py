"""Pure scenario adjustments around saved forecasts. No fitting or baseline mutation."""
from datetime import timedelta
import numpy as np
from app.core import risk_config as C
from app.simulation.generator import MEDICINES
from app.forecasting.stockout import demand_paths, known_receipts, project_stock
from app.scenarios.models import FacilityProjection, ScenarioType

PROFILES = {code: profile for code, _, _, profile in MEDICINES}


def parameters(request):
    level = request.severity
    supplied = request.parameters
    if request.scenario_type == ScenarioType.DENGUE_SURGE:
        return {"additional_fever_fraction": C.DENGUE[level], "extra_fever_admission_rate": C.FEVER_ADMISSION_RATE}
    if request.scenario_type == ScenarioType.DELIVERY_DELAY:
        return {"medicine_id": supplied.medicine_id or "IVF", "delay_days": supplied.delay_days or C.DELAY_DAYS[level]}
    if request.scenario_type == ScenarioType.STAFF_SHORTAGE:
        return {"unavailable_fraction": supplied.unavailable_fraction or C.STAFF_UNAVAILABLE[level]}
    return {"capacity_reduction": supplied.capacity_reduction or C.CAPACITY_REDUCTION[level]}


def adjusted(points, extra):
    # Conditional bands translate with the specified shock; no uncertainty about shock size.
    return [p.model_copy(update={k: getattr(p, k)+float(extra[i]) for k in ("point", "lower80", "upper80", "lower95", "upper95")}) for i, p in enumerate(points)]


def project(facility, forecasts, bundle, origin, request=None, seed=42):
    f = facility
    foot, admissions = forecasts["footfall"], forecasts["admissions"]
    active = np.zeros(C.HORIZON, dtype=bool)
    effect = parameters(request) if request else {}
    if request:
        start = (request.start_date-origin).days-1
        active[start:start+request.duration] = True
    baseline_foot = np.array([p.point for p in foot.forecast])
    past = f.history[-7:]
    total_past = sum(h.footfall for h in past)
    syndromes = set(PROFILES["PCM"]) | set(PROFILES["IVF"]) | set(PROFILES["IFA"])
    shares = {s: sum(h.syndrome_counts.get(s, 0) for h in past)/max(1, total_past) for s in syndromes}
    if sum(shares.values()) == 0:
        shares = {"fever": .25, "respiratory": .22, "diarrhoeal": .13, "maternal": .12, "general": .28}
    extra_fever = baseline_foot * float(effect.get("additional_fever_fraction", 0)) * active
    future_foot = baseline_foot+extra_fever
    future_admissions = np.array([p.point for p in admissions.forecast]) + extra_fever*C.FEVER_ADMISSION_RATE
    discharge_rate = sum(h.discharges for h in past)/max(1, sum(h.previous_occupied or 0 for h in past))
    discharge_rate = min(1., discharge_rate or C.DEFAULT_DISCHARGE_RATE)
    occupied = float(f.beds.occupied)
    normal_beds = f.beds.total-f.beds.reserved
    staff_normal = f.staff.present
    staff_capacity_per_person = foot.summary.recent_daily_mean*C.SERVICE_HEADROOM/max(1, staff_normal)
    timeline = []
    for i, p in enumerate(foot.forecast):
        reduction = float(effect.get("capacity_reduction", 0)) if active[i] else 0.
        unavailable = float(effect.get("unavailable_fraction", 0)) if active[i] else 0.
        available_staff = staff_normal*(1-unavailable)
        capacity = normal_beds*(1-reduction)
        service = available_staff*staff_capacity_per_person*(1-reduction)
        opening = occupied
        discharged = opening*discharge_rate
        admitted = min(float(future_admissions[i]), max(0., capacity-opening+discharged))
        occupied = opening+admitted-discharged
        mix = {s: float(baseline_foot[i]*share) for s, share in shares.items()}
        mix["fever"] += float(extra_fever[i])
        timeline.append(dict(date=p.date, footfall=float(future_foot[i]), syndrome_counts=mix,
            admissions_requested=float(future_admissions[i]), admissions=admitted, discharges=discharged,
            opening_occupied=opening, occupied=occupied, bed_capacity=capacity,
            occupancy_ratio=occupied/capacity if capacity else None, bed_overflow=max(0., occupied-capacity),
            unmet_admissions=float(future_admissions[i])-admitted,
            scheduled_staff=f.staff.scheduled, available_staff=available_staff, service_capacity=service,
            served_patients=min(float(future_foot[i]), service), unserved_patients=max(0., float(future_foot[i])-service),
            workload_ratio=float(future_foot[i])/service if service else None))
    resources, changes = [], []
    for item in f.inventory:
        code = item.medicine_id
        forecast = forecasts[code]
        extra = extra_fever*PROFILES[code].get("fever", 0.)
        point = np.array([p.point for p in forecast.forecast])
        context = next(c for c in bundle["manifest"]["series"]["medicine"] if c["facility_id"] == f.id and c["resource_id"] == code)
        scale = max(1., float(np.mean(context["last28"])))
        key = f"{forecast.provenance.model_version}:{f.id}:{code}"
        if seed != 42:
            key += f":scenario-seed-{seed}"
        paths = None if request is None and seed == 42 else demand_paths(point, scale, bundle["residuals"]["medicine"][code], key)
        orders = []
        for order in item.scheduled_deliveries:
            shifted = order.model_copy(deep=True)
            if request and request.scenario_type == ScenarioType.DELIVERY_DELAY and effect["medicine_id"] == code and order.ordered_at <= origin < order.expected_at and request.start_date <= order.expected_at < request.start_date+timedelta(days=request.duration):
                shifted.expected_at += timedelta(days=int(effect["delay_days"]))
                changes.append(dict(resource_id=code, ordered_at=order.ordered_at, original_date=order.expected_at,
                    projected_date=shifted.expected_at, quantity=order.quantity))
            orders.append(shifted)
        stock = forecast.stockout.model_dump(mode="json") if paths is None else project_stock(item.current_stock, item.safety_stock, point+extra, paths+extra[None, :], known_receipts(orders, origin), origin)
        if request:
            stock["method"] = "Conditional scenario estimate using 500 paired Phase 3 residual paths plus specified demand shock and shifted receipts. Shock and receipt assumptions treated as certain; not validated emergency probabilities."
        resources.append(dict(resource_id=code, name=item.name, unit=item.unit, forecast=adjusted(forecast.forecast, extra),
            stockout=stock, requested_total=float((point+extra).sum()), unmet_total=sum(p["unmet_demand"] for p in stock["trajectory"])))
    return FacilityProjection(facility_id=f.id, facility_name=f.name, facility_type=f.type, country_id=f.country_id,
        state_id=f.state_id, district_id=f.district_id, history=foot.history, footfall=adjusted(foot.forecast, extra_fever),
        timeline=timeline, resources=resources, receipt_changes=changes, provenance=foot.provenance,
        source_models={key: value.provenance.model for key, value in forecasts.items()},
        baseline_recent_daily_mean=foot.summary.recent_daily_mean, current_staff_fraction=f.staff.present/f.staff.scheduled,
        current_occupancy_ratio=f.beds.occupied/max(1, normal_beds),
        current_workload_ratio=f.footfall_today/(staff_normal*staff_capacity_per_person) if staff_normal else None)
