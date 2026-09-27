"""Transparent aggregate anchors. These mappings are demo assumptions, not fitted models."""
from app.data_ingestion.catalog import datasets, latest_observations


def calibration_for(country_id: str) -> dict:
    local = latest_observations(country_id)
    india = latest_observations("IN")
    inputs = {row.id: row for row in [*local.values(), *india.values()]}
    used, fallbacks = [], []

    def value(rows, key, fallback):
        row = rows.get(key)
        if row is None or row.value <= 0:
            fallbacks.append(f"{key}: missing/nonpositive anchor; assumed default {fallback:g}.")
            return fallback
        used.append(row.id)
        return row.value

    india_beds = value(india, "WHS6_102", 16.0)
    india_doctors = value(india, "HWF_0001", 10.0)
    beds = value(local, "WHS6_102", india_beds)
    doctors = value(local, "HWF_0001", india_doctors)
    phcs = value(india, "phc_count", 1)
    chcs = value(india, "chc_count", 1)
    phc_doctors = value(india, "phc_doctors", 1.3 * phcs) / phcs
    chc_doctors = value(india, "chc_doctors", 4.1 * chcs) / chcs
    phc_nurses = value(india, "phc_nurses", 1.5 * phcs) / phcs
    chc_nurses = value(india, "chc_nurses", 8 * chcs) / chcs
    hospitals = value(india, "sdh_count", 1340) + value(india, "dh_count", 714)
    hospital_doctors = value(india, "sdh_dh_doctors", 22 * hospitals) / hospitals
    return {
        "version": "aggregate-anchors-v2", "country_id": country_id,
        "is_synthetic": True, "public_sources_available": bool(used),
        "beds_per_10000": beds, "doctors_per_10000": doctors,
        "bed_capacity_factor": max(0.65, min(2.0, (beds / india_beds) ** 0.5)),
        "doctor_staffing_factor": 1.0 if country_id == "IN" else max(0.7, min(2.3, (doctors / india_doctors) ** 0.5)),
        "doctors_by_type": [phc_doctors, chc_doctors, hospital_doctors],
        "nurses_by_type": [phc_nurses, chc_nurses, 38.0],
        "inputs": [inputs[key].model_dump(mode="json") for key in sorted(set(used))],
        "assumptions": [
            "India workforce-per-facility ratios are national HDI totals divided by matching facility totals; DH doctors use the pooled SDH+DH ratio.",
            "Foreign nodes reuse illustrative care-centre templates; square-root WHO density ratios scale capacity and doctor staffing with explicit bounds.",
            "Catchment population = synthetic bed capacity / country bed density * 10,000. It is inferred, not a population estimate for a real facility.",
            "Daily visit rates, syndrome mixes, length of stay, medicine profiles, attendance and deliveries remain unvalidated simulation assumptions.",
            "Use latest available country observations, not a common year. South Africa bed data may be substantially older; see input years.",
        ],
        "fallbacks": fallbacks,
    }


def public_provenance():
    return {data.provenance.id: data.provenance for data in datasets()}
