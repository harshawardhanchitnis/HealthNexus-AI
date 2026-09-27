"""Deterministic synthetic network. No real facility locations or health records."""
import csv
import math
import random
import re
from datetime import date, timedelta

from app.core.config import ROOT
from app.models.network import (
    Alert, Beds, DailyActivity, District, Facility, InventoryItem,
    Region, Snapshot, Staff, Status,
)

MEDICINES = [
    ("PCM", "Paracetamol 500 mg", "tablets", 1.7),
    ("IVF", "IV fluids", "bags", 0.24),
    ("ORS", "Oral rehydration salts", "sachets", 0.42),
    ("AMX", "Amoxicillin 500 mg", "capsules", 0.65),
    ("IFA", "Iron and folic acid", "tablets", 0.85),
]
RANK = {Status.HEALTHY: 0, Status.WATCH: 1, Status.AT_RISK: 2, Status.CRITICAL: 3}


def inventory_status(days: float) -> Status:
    if days < 3:
        return Status.CRITICAL
    if days < 7:
        return Status.AT_RISK
    if days < 10:
        return Status.WATCH
    return Status.HEALTHY


def generate_snapshot(seed: int = 42, as_of: date | None = None) -> Snapshot:
    rng = random.Random(seed)
    as_of = as_of or date.today()
    regions, districts, facilities, alerts = [], [], [], []
    with (ROOT / "data/metadata/india-regions.csv").open(encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        region = Region(**{k: v for k, v in row.items() if k != "districts"})
        regions.append(region)
        for district_name in row["districts"].split("|"):
            slug = re.sub(r"[^A-Z0-9]+", "-", district_name.upper()).strip("-")
            district = District(id=f"{region.id}-{slug}", name=district_name, state_id=region.id)
            districts.append(district)
            for index, (kind, total_beds, baseline, scheduled) in enumerate([
                ("PHC", 12, 85, 14), ("CHC", 30, 170, 32),
                ("District Hospital", 250, 580, 130),
            ], start=1):
                facility_id = f"IN-{district.id}-{index:03d}"
                population_factor = rng.uniform(0.75, 1.25)
                history = []
                for day in range(28):
                    observed = as_of - timedelta(days=27 - day)
                    weekly = [1.15, 1.03, 1.02, 1.0, 1.02, 0.90, 0.70][observed.weekday()]
                    seasonal = 1 + 0.16 * math.cos(2 * math.pi * (observed.timetuple().tm_yday - 245) / 365)
                    trend = 1 + 0.002 * day
                    footfall = round(baseline * population_factor * weekly * seasonal * trend * rng.uniform(0.94, 1.06))
                    occupied = min(total_beds - 1, round(total_beds * (0.42 + 0.19 * footfall / baseline)))
                    history.append(DailyActivity(date=observed, footfall=footfall,
                        medicine_units=round(footfall * sum(m[3] for m in MEDICINES)), occupied_beds=occupied))
                inventory = []
                cover_factor = rng.choices([2.2, 5.5, 8.5, 17.0], weights=[5, 12, 15, 68])[0]
                for code, name, unit, consumption_rate in MEDICINES:
                    consumed = round(history[-1].footfall * consumption_rate)
                    average = round(sum(h.footfall for h in history[-7:]) / 7 * consumption_rate, 2)
                    current = max(1, round(average * cover_factor * rng.uniform(0.85, 1.2)))
                    received = round(consumed * 0.6) if cover_factor > 10 else 0
                    cover = round(current / average, 1)
                    inventory.append(InventoryItem(medicine_id=code, name=name, unit=unit,
                        opening_stock=current + consumed - received, units_consumed=consumed,
                        units_received=received, current_stock=current, safety_stock=math.ceil(average * 7),
                        average_daily_consumption=average, days_of_cover=cover, status=inventory_status(cover)))
                present = round(scheduled * rng.uniform(0.73, 1))
                attendance = present / scheduled
                staff_status = Status.AT_RISK if attendance < 0.8 else Status.HEALTHY
                status = max([item.status for item in inventory] + [staff_status], key=lambda s: RANK[s])
                occupied = history[-1].occupied_beds
                reserved = max(1, round(total_beds * 0.05))
                occupied = min(occupied, total_beds - reserved)
                history[-1].occupied_beds = occupied
                facility = Facility(id=facility_id, name=f"{district_name} · {kind} {index:02d}",
                    type=kind, state_id=region.id, district_id=district.id, district_name=district_name,
                    latitude=region.latitude + rng.uniform(-0.08, 0.08),
                    longitude=region.longitude + rng.uniform(-0.08, 0.08),
                    status=status, resilience_score=[96, 78, 55, 28][RANK[status]],
                    footfall_today=history[-1].footfall,
                    beds=Beds(total=total_beds, occupied=occupied, reserved=reserved,
                        available=total_beds - occupied - reserved),
                    staff=Staff(scheduled=scheduled, present=present,
                        doctors_present=max(1, present // 5), nurses_present=max(1, present // 2)),
                    inventory=inventory, history=history)
                facilities.append(facility)
                for item in inventory:
                    if item.status in (Status.AT_RISK, Status.CRITICAL):
                        alerts.append(Alert(id=f"{facility_id}-{item.medicine_id}", facility_id=facility_id,
                            facility_name=facility.name, district_id=district.id, state_id=region.id,
                            severity=item.status, resource=item.name, title=f"Low stock cover · {item.name}",
                            explanation=f"{item.current_stock:,} {item.unit} / {item.average_daily_consumption:g} daily consumption = {item.days_of_cover} days of cover. Below the seven-day reserve.",
                            recommended_action="Review available stock and coordinate replenishment with the district supply team."))
                if staff_status == Status.AT_RISK:
                    alerts.append(Alert(id=f"{facility_id}-STAFF", facility_id=facility_id,
                        facility_name=facility.name, district_id=district.id, state_id=region.id,
                        severity=staff_status, resource="Staff", title="Staff attendance below 80%",
                        explanation=f"{present} of {scheduled} scheduled staff are present ({attendance:.0%}).",
                        recommended_action="Review the shift roster and coordinate additional cover."))
    return Snapshot(as_of=as_of, seed=seed, regions=regions, districts=districts,
        facilities=facilities, alerts=sorted(alerts, key=lambda a: -RANK[a.severity]))

