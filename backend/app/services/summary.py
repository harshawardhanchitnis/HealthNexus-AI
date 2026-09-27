from app.models.network import Facility, Status


def summarize(facilities: list[Facility]) -> dict:
    total_beds = sum(f.beds.total for f in facilities)
    occupied = sum(f.beds.occupied for f in facilities)
    scheduled = sum(f.staff.scheduled for f in facilities)
    present = sum(f.staff.present for f in facilities)
    inventory = [item for f in facilities for item in f.inventory]
    covered = sum(item.days_of_cover >= 7 for item in inventory)
    return {
        "facilities": len(facilities),
        "status_counts": {s.value: sum(f.status == s for f in facilities) for s in Status},
        "patient_footfall": sum(f.footfall_today for f in facilities),
        "medicine_availability": round(100 * covered / len(inventory), 1) if inventory else 0,
        "total_beds": total_beds, "occupied_beds": occupied,
        "available_beds": sum(f.beds.available for f in facilities),
        "reserved_beds": sum(f.beds.reserved for f in facilities),
        "bed_utilisation": round(100 * occupied / total_beds, 1) if total_beds else 0,
        "staff_present": present, "staff_scheduled": scheduled,
        "staff_availability": round(100 * present / scheduled, 1) if scheduled else 0,
    }


def aggregate_history(facilities: list[Facility]) -> list[dict]:
    dates: dict[str, dict] = {}
    for facility in facilities:
        for activity in facility.history:
            key = activity.date.isoformat()
            bucket = dates.setdefault(key, {"date": key, "footfall": 0, "medicine_units": 0, "occupied_beds": 0})
            for field in ("footfall", "medicine_units", "occupied_beds"):
                bucket[field] += getattr(activity, field)
    return [dates[key] for key in sorted(dates)]

