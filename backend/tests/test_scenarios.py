from datetime import timedelta
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from test_forecasting import trained
from app.forecasting.prediction import ForecastService
from app.scenarios.engine import ScenarioEngine, select
from app.scenarios.models import ScenarioRequest, Parameters
from app.scenarios.effects import project
from app.warnings.engine import evaluate, listing
from app.core.risk_config import SEVERITY_RANK
from app.main import create_app


@pytest.fixture
def setup(trained):
    root, snapshot, _ = trained
    engine = ScenarioEngine(ForecastService(root))
    return engine, snapshot


def definition(snapshot, kind="DENGUE_SURGE", **kwargs):
    return ScenarioRequest(country_id=snapshot.country, scenario_type=kind,
        facility_ids=[snapshot.facilities[0].id], **kwargs)


def test_repeatable_and_non_destructive(setup):
    engine, snapshot = setup
    before = snapshot.model_dump_json()
    request = definition(snapshot)
    a = engine.run(snapshot, request)
    b = engine.run(snapshot, request)
    assert a.baseline == b.baseline
    assert a.scenario_result == b.scenario_result
    assert a.delta == b.delta
    assert a.scenario.baseline_snapshot_id == b.scenario.baseline_snapshot_id
    assert snapshot.model_dump_json() == before
    assert request.start_date is None


def test_scope_isolation(setup):
    engine, snapshot = setup
    a = engine.run(snapshot, definition(snapshot))
    assert {f.facility_id for f in a.scenario_result.facilities} == {snapshot.facilities[0].id}
    with pytest.raises(LookupError):
        engine.run(snapshot, ScenarioRequest(country_id="BR", scenario_type="DENGUE_SURGE", facility_ids=["IN-MH-PUNE-001"]))
    with pytest.raises(ValueError):
        engine.run(snapshot, ScenarioRequest(country_id="IN", scenario_type="DENGUE_SURGE"))
    with pytest.raises(LookupError):
        select(snapshot, state="MH")


def test_severity_and_syndrome_mapping(setup):
    engine, snapshot = setup
    results = [engine.run(snapshot, definition(snapshot, severity=s)) for s in ("moderate", "severe", "critical")]
    assert results[0].scenario_result.metrics.patient_demand < results[1].scenario_result.metrics.patient_demand < results[2].scenario_result.metrics.patient_demand
    a = results[1]
    assert a.delta["patient_demand"].percent == pytest.approx(50)
    assert a.delta["admissions_requested"].absolute > 0
    assert a.delta["unmet_admissions"].absolute >= 0
    for r in a.resource_impact:
        assert r.demand.absolute > 0 if r.resource_id in ("PCM", "IVF", "ORS") else r.demand.absolute == 0
    for b, s in zip(a.baseline.facilities[0].timeline, a.scenario_result.facilities[0].timeline):
        assert s.syndrome_counts["fever"] > b.syndrome_counts["fever"]
        assert s.syndrome_counts["maternal"] == b.syndrome_counts["maternal"]
        assert sum(s.syndrome_counts.values()) == pytest.approx(s.footfall)


def test_event_window_and_carryover(setup):
    engine, snapshot = setup
    a = engine.run(snapshot, definition(snapshot, duration=3, start_date=snapshot.as_of+timedelta(days=4)))
    b, s = a.baseline.facilities[0], a.scenario_result.facilities[0]
    for i in range(14):
        assert (s.timeline[i].footfall > b.timeline[i].footfall) == (3 <= i < 6)
    for r in s.resources:
        original = next(x for x in b.resources if x.resource_id == r.resource_id)
        assert r.stockout.trajectory[-1].closing_stock <= original.stockout.trajectory[-1].closing_stock


@pytest.mark.parametrize("kind", ["DENGUE_SURGE", "DELIVERY_DELAY", "STAFF_SHORTAGE", "FACILITY_DISRUPTION"])
def test_conservation_all_scenarios(setup, kind):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, kind, severity="critical"))
    for outcome in (result.baseline, result.scenario_result):
        for f in outcome.facilities:
            for d in f.timeline:
                assert d.occupied == pytest.approx(d.opening_occupied+d.admissions-d.discharges)
                assert d.occupied <= d.bed_capacity+d.bed_overflow+1e-8
                assert d.admissions <= d.admissions_requested
                assert d.unmet_admissions == pytest.approx(d.admissions_requested-d.admissions)
                assert d.available_staff <= d.scheduled_staff
                assert d.served_patients <= d.footfall
                assert d.unserved_patients == pytest.approx(d.footfall-d.served_patients)
            for resource in f.resources:
                opening = resource.stockout.current_stock
                for row in resource.stockout.trajectory:
                    fulfilled = row.demand-row.unmet_demand
                    assert row.closing_stock == pytest.approx(opening+row.expected_receipts-fulfilled)
                    assert 0 <= fulfilled <= row.demand+1e-8
                    opening = row.closing_stock
                probabilities = resource.stockout.probabilities
                assert 0 <= probabilities["3"] <= probabilities["7"] <= probabilities["14"] <= 1


def test_receipt_shift_and_risk_recalculation(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, "DELIVERY_DELAY", parameters=Parameters(medicine_id="IVF", delay_days=30)))
    b, s = result.baseline.facilities[0], result.scenario_result.facilities[0]
    assert s.receipt_changes
    for change in s.receipt_changes:
        assert change.resource_id == "IVF"
        assert (change.projected_date-change.original_date).days == 30
        assert change.ordered_at <= snapshot.as_of < change.original_date
    for a, z in zip(b.resources, s.resources):
        if z.resource_id == "IVF":
            assert z.stockout.trajectory != a.stockout.trajectory
            assert z.stockout.probabilities["14"] >= a.stockout.probabilities["14"]
            assert sum(p.expected_receipts for p in z.stockout.trajectory) == 0
        else:
            assert z.forecast == a.forecast
            assert z.stockout.trajectory == a.stockout.trajectory


def test_staff_shortage_and_recovery(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, "STAFF_SHORTAGE", duration=7, parameters=Parameters(unavailable_fraction=.4)))
    for i, (b, s) in enumerate(zip(result.baseline.facilities[0].timeline, result.scenario_result.facilities[0].timeline)):
        assert s.available_staff == pytest.approx(b.available_staff*(.6 if i < 7 else 1))
        assert s.scheduled_staff == b.scheduled_staff
        assert s.footfall == b.footfall
    assert result.delta["peak_workload_ratio"].absolute > 0


def test_disruption_zero_capacity_keeps_existing_patients(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, "FACILITY_DISRUPTION", parameters=Parameters(capacity_reduction=1)))
    f = result.scenario_result.facilities[0]
    assert all(d.bed_capacity == 0 and d.service_capacity == 0 for d in f.timeline)
    assert f.timeline[0].occupied == pytest.approx(f.timeline[0].bed_overflow)
    assert f.timeline[0].admissions == 0
    assert result.scenario_result.metrics.peak_workload_ratio is None
    assert result.scenario_result.metrics.peak_bed_occupancy_percent is None


@pytest.mark.parametrize("values", [{"duration": 0}, {"duration": 15}, {"severity": "random"}, {"country_id": "US"},
    {"parameters": {"unavailable_fraction": 1.1}}, {"parameters": {"delay_days": 2}}, {"scenario_type": "FIRE"}, {"extra": 3}])
def test_invalid_definition(values):
    with pytest.raises(ValidationError):
        ScenarioRequest(**{"scenario_type": "DENGUE_SURGE", **values})


@pytest.mark.parametrize("offset,duration", [(0, 14), (-1, 1), (2, 14), (15, 1)])
def test_invalid_time_window(setup, offset, duration):
    engine, snapshot = setup
    with pytest.raises(ValueError):
        engine.run(snapshot, definition(snapshot, start_date=snapshot.as_of+timedelta(days=offset), duration=duration))


def test_warning_dedup_priority_aggregation_and_metadata(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot))
    warnings = result.warnings_created.items
    assert warnings
    assert len({w.warning_id for w in warnings}) == len(warnings)
    assert listing(warnings+warnings).summary.total == len(warnings)
    assert [w.priority_score for w in warnings] == sorted([w.priority_score for w in warnings], reverse=True)
    assert sum(result.warnings_created.summary.counts.values()) == len(warnings)
    assert sum(result.warnings_created.summary.by_country["BR"].values()) == len(warnings)
    assert result.warnings_created.summary.facilities_affected == 1
    for w in warnings:
        assert w.scenario_id == result.scenario.scenario_id and w.country_id == "BR"
        assert w.model_version.startswith("forecast-v1-")
        assert w.explanation_factors and w.provenance["is_synthetic"]
        if w.transition == "worsened":
            assert SEVERITY_RANK[w.severity.value] > SEVERITY_RANK[w.baseline_severity.value]


def test_warning_threshold_crossings(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot))
    projection = result.baseline.facilities[0].model_copy(deep=True)
    s = projection.resources[0].stockout
    s.days_of_cover = 2
    s.stockout_date = snapshot.as_of+timedelta(days=2)
    s.probabilities = {"3": .8, "7": .9, "14": 1.}
    warnings = evaluate(projection, snapshot.as_of)
    assert next(w for w in warnings if w.warning_type == "LOW_STOCK").severity == "CRITICAL"
    assert next(w for w in warnings if w.warning_type == "PREDICTED_STOCKOUT").severity == "CRITICAL"
    assert next(w for w in warnings if w.warning_type == "HIGH_STOCKOUT_RISK").severity == "CRITICAL"


def test_baseline_matches_phase3_stock_paths(setup):
    engine, snapshot = setup
    f = snapshot.facilities[0]
    inputs, bundle = engine.inputs(snapshot, f)
    projection = project(f, inputs, bundle, snapshot.as_of)
    for r in projection.resources:
        assert r.stockout == inputs[r.resource_id].stockout


def test_delayed_event_cannot_warn_of_surge_before_shock(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, severity="critical", duration=7, start_date=snapshot.as_of+timedelta(days=8)))
    warnings = [w for w in result.warnings_created.items if w.warning_type == "PATIENT_SURGE"]
    assert warnings and all(w.estimated_event_date >= snapshot.as_of+timedelta(days=8) for w in warnings)


def test_baseline_cache_returns_independent_values_and_stable_warnings(setup):
    engine, snapshot = setup
    facilities = snapshot.facilities[:1]
    a, warnings = engine.baseline(snapshot, facilities)
    original = a.model_copy(deep=True)
    a.facilities[0].timeline[0].footfall = 999999
    b, again = engine.baseline(snapshot, facilities)
    assert original == b and warnings == again


def test_receipts_before_origin_and_unknown_future_orders_are_ignored(setup):
    from app.models.network import ScheduledReceipt
    engine, snapshot = setup
    f = snapshot.facilities[0].model_copy(deep=True)
    forecasts, bundle = engine.inputs(snapshot, snapshot.facilities[0])
    original = project(f, forecasts, bundle, snapshot.as_of)
    f.inventory[0].scheduled_deliveries.extend([
        ScheduledReceipt(ordered_at=snapshot.as_of-timedelta(days=4), expected_at=snapshot.as_of-timedelta(days=1), quantity=100000, lead_time_days=3),
        ScheduledReceipt(ordered_at=snapshot.as_of+timedelta(days=1), expected_at=snapshot.as_of+timedelta(days=3), quantity=100000, lead_time_days=2)])
    future = project(f, forecasts, bundle, snapshot.as_of)
    assert original.resources[0].stockout == future.resources[0].stockout


def test_discard_is_country_scoped_and_store_is_copy_safe(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot))
    sid = result.scenario.scenario_id
    result.scenario_result.facilities[0].timeline[0].footfall = 999999
    assert engine.store.get(sid, "BR").scenario_result.facilities[0].timeline[0].footfall != 999999
    with pytest.raises(LookupError):
        engine.store.discard(sid, "IN")
    engine.store.discard(sid, "BR")
    with pytest.raises(LookupError):
        engine.store.get(sid, "BR")


def test_admission_warning_identifies_selected_target_model(setup):
    engine, snapshot = setup
    result = engine.run(snapshot, definition(snapshot, "FACILITY_DISRUPTION", severity="critical"))
    f = result.scenario_result.facilities[0]
    for w in result.warnings_created.items:
        if w.category == "beds":
            assert w.provenance["baseline_model"] == f.source_models["admissions"]


def test_api_lifecycle_filters_and_reset(trained):
    root, snapshot, _ = trained
    class Repo:
        mode = "test"
        def snapshot(self):
            return snapshot
        def country_snapshot(self, country):
            return snapshot
    with TestClient(create_app(Repo(), ForecastService(root))) as client:
        assert client.get("/api/scenarios/presets").status_code == 200
        body = definition(snapshot).model_dump(mode="json")
        response = client.post("/api/scenarios", json=body)
        assert response.status_code == 201, response.text
        result = response.json()
        sid = result["scenario"]["scenario_id"]
        base = f"/api/scenarios/{sid}"
        query = {"country_id": "BR", "scenario_id": sid}
        assert client.get(base, params={"country_id": "BR"}).json() == result
        assert client.get(base+"/comparison", params={"country_id": "BR"}).json() == result
        assert client.get(base, params={"country_id": "IN"}).status_code == 404
        warnings = client.get("/api/warnings", params=query)
        assert warnings.status_code == 200
        assert warnings.json() == result["warnings_created"]
        assert client.get("/api/warnings/summary", params=query).json() == result["warnings_created"]["summary"]
        wid = warnings.json()["items"][0]["warning_id"]
        assert client.get(f"/api/warnings/{wid}", params=query).status_code == 200
        filtered = client.get("/api/warnings", params={**query, "severity": "CRITICAL"}).json()
        assert all(w["severity"] == "CRITICAL" for w in filtered["items"])
        assert client.get("/api/warnings", params={**query, "severity": "random"}).status_code == 422
        assert client.delete(base, params={"country_id": "IN"}).status_code == 404
        assert client.delete(base, params={"country_id": "BR"}).status_code == 204
        assert client.get(base, params={"country_id": "BR"}).status_code == 404
        assert client.get("/api/warnings", params=query).status_code == 404
        normal = client.get("/api/warnings", params={"country_id": "BR", "facility_id": snapshot.facilities[0].id}).json()
        assert all(w["baseline_or_scenario"] == "baseline" for w in normal["items"])
