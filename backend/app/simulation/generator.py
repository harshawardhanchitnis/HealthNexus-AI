"""Country-local, reproducible operations with aggregate anchors and conserved flows."""
import csv
import math
import random
import re
from datetime import date, timedelta

from app.core.config import ROOT
from app.core.geography import COUNTRY_BY_ID
from app.models.network import Alert, Beds, DailyActivity, District, Facility, InventoryItem, Region, Snapshot, Staff, Status, StockDay
from app.models.provenance import Provenance
from app.simulation.calibration import calibration_for, public_provenance

RANK = {Status.HEALTHY: 0, Status.WATCH: 1, Status.AT_RISK: 2, Status.CRITICAL: 3}
# Operational resource assumptions per syndrome, never individual treatment advice.
MEDICINES = [
    ("PCM", "Paracetamol 500 mg", "tablets", {"fever": 3.5, "respiratory": 1.5, "general": 0.5}),
    ("IVF", "IV fluids", "bags", {"fever": 0.3, "diarrhoeal": 0.7, "maternal": 0.2}),
    ("ORS", "Oral rehydration salts", "sachets", {"diarrhoeal": 2.5, "fever": 0.1}),
    ("AMX", "Amoxicillin 500 mg", "capsules", {"respiratory": 1.6, "general": 0.3}),
    ("IFA", "Iron and folic acid", "tablets", {"maternal": 4.0, "general": 0.3}),
]


def inventory_status(days: float) -> Status:
    if days < 3:
        return Status.CRITICAL
    if days < 7:
        return Status.AT_RISK
    if days < 10:
        return Status.WATCH
    return Status.HEALTHY


def syndrome_mix(footfall: int, seasonal: float) -> dict[str, int]:
    weights = {"fever": 0.23 + 0.05 * seasonal, "respiratory": 0.22,
        "diarrhoeal": 0.13, "maternal": 0.12, "general": 0.30 - 0.05 * seasonal}
    counts = {key: math.floor(footfall * weight) for key, weight in weights.items()}
    counts["general"] += footfall - sum(counts.values())
    return counts


def generate_snapshot(seed: int = 42, as_of: date | None = None, country_id: str = "IN") -> Snapshot:
    if country_id not in COUNTRY_BY_ID:
        raise ValueError("Unsupported country")
    rng = random.Random(f"{seed}:{country_id}")
    as_of = as_of or date.today()
    calibration = calibration_for(country_id)
    op_id, geo_id, derived_id = f"operations-{country_id}-v2", f"geography-{country_id}-v2", f"risk-{country_id}-v2"
    provenance = public_provenance()
    provenance[op_id] = Provenance(id=op_id, source_type="synthetic", source_name="Calibrated operational generator",
        accessed_at=as_of, geography=[country_id], is_synthetic=True, version=f"2/seed-{seed}",
        methodology="Public aggregate anchors + assumed contact rates, syndrome-resource profiles, admission/discharge and daily stock ledgers. No real facility records.",
        input_ids=[row["id"] for row in calibration["inputs"]])
    provenance[geo_id] = Provenance(id=geo_id, source_type="derived", source_name="Curated prototype geography",
        accessed_at=as_of, geography=[country_id], is_synthetic=False, version="2",
        methodology="Manually curated region names and internal IDs; approximate centroids; India districts illustrative. Not an official current subdivision registry.")
    provenance[derived_id] = Provenance(id=derived_id, source_type="derived", source_name="Resource threshold rules",
        accessed_at=as_of, geography=[country_id], is_synthetic=True, version="2",
        methodology="Stock-cover and attendance rules applied to synthetic observations.", input_ids=[op_id])
    path = ROOT / "data/metadata" / ("india-regions.csv" if country_id == "IN" else "brics-regions.csv")
    with path.open(encoding="utf-8") as source:
        rows = [r for r in csv.DictReader(source) if r.get("country_id", "IN") == country_id]
    regions, districts, facilities, alerts = [], [], [], []
    for row in rows:
        region = Region(**{k: v for k, v in row.items() if k not in ("districts", "country_id")}, country_id=country_id, provenance_id=geo_id)
        regions.append(region)
        for district_name in row.get("districts", "").split("|"):
            district_id = None
            if country_id == "IN":
                slug = re.sub(r"[^A-Z0-9]+", "-", district_name.upper()).strip("-")
                district_id = f"{region.id}-{slug}"
                districts.append(District(id=district_id, name=district_name, state_id=region.id, country_id=country_id, provenance_id=geo_id))
            kinds = ["PHC", "CHC", "District Hospital"] if country_id == "IN" else ["Primary Care Centre", "Community Hospital", "Regional Hospital"]
            for index, kind in enumerate(kinds):
                facility_id = f"IN-{district_id}-{index + 1:03d}" if country_id == "IN" else f"{region.id}-{index + 1:03d}"
                label = district_name or region.name
                total_beds = max(6, round([12, 30, 250][index] * calibration["bed_capacity_factor"]))
                reserved = max(1, round(total_beds * 0.05))
                population_factor = rng.uniform(0.9, 1.1)
                catchment = max(1, round(total_beds / calibration["beds_per_10000"] * 10000 * population_factor))
                baseline = catchment * [0.011, 0.009, 0.004][index]
                previous_occupied = round(total_beds * 0.5)
                history = []
                for day in range(28):
                    observed = as_of - timedelta(days=27 - day)
                    # Hemisphere-aware, explicitly assumed seasonality; no fabricated disease statistics.
                    peak = 245 if region.latitude >= 0 else 65
                    seasonal = math.cos(2 * math.pi * (observed.timetuple().tm_yday - peak) / 365)
                    weekly = [1.15, 1.03, 1.02, 1.0, 1.02, 0.90, 0.70][observed.weekday()]
                    footfall = max(1, round(baseline * weekly * (1 + 0.12 * seasonal) * (1 + 0.001 * day) * rng.uniform(0.96, 1.04)))
                    mix = syndrome_mix(footfall, seasonal)
                    admissions_requested = round(footfall * [0.045, 0.05, 0.06][index])
                    discharges = min(previous_occupied, round(previous_occupied / [2.5, 3, 5][index]))
                    admissions = min(admissions_requested, total_beds - reserved - previous_occupied + discharges)
                    occupied = previous_occupied + admissions - discharges
                    history.append(DailyActivity(date=observed, footfall=footfall, medicine_units=0,
                        occupied_beds=occupied, previous_occupied=previous_occupied, admissions=admissions,
                        discharges=discharges, unmet_admissions=admissions_requested-admissions,
                        syndrome_counts=mix, provenance_id=op_id))
                    previous_occupied = occupied
                inventory = []
                delivery_delay = len(facilities) % 9 == 1
                for code, name, unit, profile in MEDICINES:
                    opening = max(1, round(baseline * sum(syndrome_mix(1000, 0)[s] / 1000 * rate for s, rate in profile.items()) * 15))
                    ledger = []
                    for day, activity in enumerate(history):
                        requested = max(1, round(sum(activity.syndrome_counts[s] * rate for s, rate in profile.items())))
                        recent = [entry.requested for entry in ledger[-7:]]
                        expected = sum(recent) / len(recent) if recent else requested
                        delivery_due = day > 0 and day % 7 == 0
                        # 7-day reserve + weekly review period + 7-day logistics buffer.
                        received = max(0, round(21 * expected) - opening) if delivery_due and not (delivery_delay and day >= 14) else 0
                        consumed = min(requested, opening + received)
                        closing = opening + received - consumed
                        ledger.append(StockDay(date=activity.date, opening=opening, received=received,
                            requested=requested, consumed=consumed, unmet_demand=requested-consumed, closing=closing))
                        activity.medicine_units += consumed
                        opening = closing
                    latest = ledger[-1]
                    average = max(0.01, round(sum(x.consumed for x in ledger[-7:]) / 7, 2))
                    days = round(latest.closing / average, 1)
                    inventory.append(InventoryItem(medicine_id=code, name=name, unit=unit,
                        opening_stock=latest.opening, units_consumed=latest.consumed, units_received=latest.received,
                        current_stock=latest.closing, safety_stock=math.ceil(average * 7), average_daily_consumption=average,
                        days_of_cover=days, status=inventory_status(days), ledger=ledger, provenance_id=op_id))
                doctors = max(1, round(calibration["doctors_by_type"][index] * calibration["doctor_staffing_factor"] * population_factor))
                nurses = max(1, round(calibration["nurses_by_type"][index] * population_factor))
                support = [6, 12, 60][index]
                scheduled = doctors + nurses + support
                absence_rate = 0.27 if len(facilities) % 7 == 0 else 0.08
                present_doctors = doctors - sum(rng.random() < absence_rate for _ in range(doctors))
                present_nurses = nurses - sum(rng.random() < absence_rate for _ in range(nurses))
                present_support = support - sum(rng.random() < absence_rate for _ in range(support))
                present = present_doctors + present_nurses + present_support
                attendance = present / scheduled
                staff_status = Status.AT_RISK if attendance < 0.8 else Status.HEALTHY
                status = max([item.status for item in inventory] + [staff_status], key=lambda s: RANK[s])
                facility = Facility(id=facility_id, name=f"{label} · {kind} {index + 1:02d}", type=kind,
                    country_id=country_id, state_id=region.id, district_id=district_id, district_name=district_name,
                    latitude=region.latitude + rng.uniform(-0.04, 0.04), longitude=region.longitude + rng.uniform(-0.04, 0.04),
                    status=status, resilience_score=[96, 78, 55, 28][RANK[status]], footfall_today=history[-1].footfall,
                    beds=Beds(total=total_beds, occupied=previous_occupied, reserved=reserved,
                        available=total_beds-previous_occupied-reserved, provenance_id=op_id),
                    staff=Staff(scheduled=scheduled, present=present, doctors_present=present_doctors,
                        nurses_present=present_nurses, provenance_id=op_id), inventory=inventory, history=history,
                    provenance_id=op_id, calibration_ids=[r["id"] for r in calibration["inputs"]], catchment_population=catchment)
                facilities.append(facility)
                for item in inventory:
                    if item.status in (Status.AT_RISK, Status.CRITICAL):
                        alerts.append(Alert(id=f"{facility_id}-{item.medicine_id}", facility_id=facility_id,
                            facility_name=facility.name, district_id=district_id, state_id=region.id, country_id=country_id,
                            severity=item.status, resource=item.name, title=f"Low stock cover · {item.name}", provenance_id=derived_id,
                            explanation=f"{item.current_stock:,} {item.unit} / {item.average_daily_consumption:g} daily consumption = {item.days_of_cover} days of cover. Unserved demand today: {item.ledger[-1].unmet_demand}. Trailing consumption can understate demand during a shortage.",
                            recommended_action="Review unserved demand and coordinate domestic replenishment with the regional supply team."))
                if staff_status == Status.AT_RISK:
                    alerts.append(Alert(id=f"{facility_id}-STAFF", facility_id=facility_id, facility_name=facility.name,
                        district_id=district_id, state_id=region.id, country_id=country_id, severity=staff_status,
                        resource="Staff", title="Staff attendance below 80%", provenance_id=derived_id,
                        explanation=f"{present} of {scheduled} scheduled staff are present ({attendance:.0%}).",
                        recommended_action="Review the shift roster and coordinate additional domestic cover."))
    return Snapshot(as_of=as_of, seed=seed, country=country_id, regions=regions, districts=districts,
        facilities=facilities, alerts=sorted(alerts, key=lambda a: -RANK[a.severity]), provenance=provenance, calibration=calibration)
