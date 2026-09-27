from datetime import date, timedelta
import gzip
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.forecasting.data import generate_history, build_tables, series_from
from app.forecasting.features import feature_block, origins_for, split_bounds, FEATURES, MODEL_NAMES
from app.forecasting.training import train_country, evaluate_saved
from app.forecasting.prediction import ForecastService, load_bundle, ModelUnavailable
from app.forecasting.evaluation import metrics, residual_bands, intervals
from app.forecasting.stockout import known_receipts, demand_paths, project_stock
from app.models.network import Snapshot, ScheduledReceipt, StockDay
from app.main import create_app

CONTEXT = {"type_index": 0, "catchment": 1000, "beds": 12, "scheduled_staff": 9, "latitude": 18}


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    root = tmp_path_factory.mktemp("forecast")
    generate_history("BR", 365, date(2026, 9, 27), 42, root)
    build_tables("BR", root)
    report = train_country("BR", root, iterations=12)
    snapshot = Snapshot.model_validate_json((root / "data/generated/nodes/BR/network.json").read_text(encoding="utf-8"))
    return root, snapshot, report


def test_long_history_and_ledger(trained):
    root, snapshot, _ = trained
    long = Snapshot.model_validate_json(gzip.decompress((root / "data/generated/history/BR.json.gz").read_bytes()))
    assert all(len(f.history) == 365 for f in long.facilities)
    assert all(len(f.history) == 28 for f in snapshot.facilities)
    for f in long.facilities:
        for item in f.inventory:
            assert any(r.requested > 0 for r in item.ledger)
            for prev, row in zip(item.ledger, item.ledger[1:]):
                assert row.opening == prev.closing
                assert row.closing == row.opening+row.received+row.transfers_received-row.consumed-row.transfers_sent
                assert row.requested == row.consumed+row.unmet_demand
        for row in f.history:
            assert row.available_staff <= row.scheduled_staff
            assert row.total_beds == f.beds.total
    assert any(r.unmet_demand for f in long.facilities for i in f.inventory for r in i.ledger)
    series = list(series_from(long, "medicine"))
    assert np.array_equal(series[0][1], [r.requested for r in long.facilities[0].inventory[0].ledger])


def test_generation_is_deterministic(trained, tmp_path):
    root, _, _ = trained
    generate_history("BR", 365, date(2026, 9, 27), 42, tmp_path)
    assert (root / "data/generated/history/BR.json.gz").read_bytes() == (tmp_path / "data/generated/history/BR.json.gz").read_bytes()


def test_future_and_same_target_never_enter_features():
    values = np.arange(1, 100, dtype=float)
    before = feature_block(values, 40, date(2025, 1, 1), CONTEXT)
    values[41:] = 999999
    after = feature_block(values, 40, date(2025, 1, 1), CONTEXT)
    for a, b in zip(before, after):
        np.testing.assert_array_equal(a, b)
    assert "target" not in FEATURES and before[0].shape == (14, len(FEATURES))
    assert before[0][0, FEATURES.index("lag1_ratio")] == pytest.approx(41 / np.arange(14, 42).mean())


def test_inference_time_origin_matches_training_features():
    values = np.arange(1, 541, dtype=float)
    training = feature_block(values, 539, date(2025, 4, 6), CONTEXT)[0]
    inference = feature_block(values[-28:], 27, date(2025, 4, 6)+timedelta(days=512), {**CONTEXT, "trend_offset": 512})[0]
    np.testing.assert_array_equal(training, inference)


def test_temporal_partitions_and_purged_horizons(trained):
    root, _, report = trained
    windows = report["windows"]
    assert windows["train"]["end"] < windows["selection"]["start"] <= windows["selection"]["end"] < windows["calibration"]["start"] < windows["test"]["start"]
    with np.load(root / "data/generated/training/BR/medicine.npz") as a:
        bounds = split_bounds(365)
        for i, (start, end) in enumerate(bounds):
            mask = a["split"] == i
            assert a["target_day"][mask].min() >= start
            assert a["target_day"][mask].max() < end
            assert np.all(a["origin"][mask] < a["target_day"][mask])
        assert set(a["X"][:, 0]) == set(range(1, 15))


def test_frozen_origin_baselines():
    _, _, baseline = feature_block(np.arange(1, 29), 27, date(2025, 1, 1), CONTEXT)
    np.testing.assert_array_equal(baseline[:, 0], np.full(14, 28))
    np.testing.assert_array_equal(baseline[:, 1], list(range(22, 29))*2)
    np.testing.assert_array_equal(baseline[:, 2], np.full(14, 25))


def test_metrics_and_zero_denominator():
    result = metrics([0, 2], [1, 4])
    assert result["mae"] == 1.5 and result["rmse"] == pytest.approx(np.sqrt(2.5))
    assert result["wape"] == 1.5
    assert metrics([0], [1])["wape"] is None


def test_trained_artifact_reloads_and_reproduces_test(trained):
    root, _, report = trained
    scores = evaluate_saved("BR", root)
    bundle = load_bundle("BR", root)
    for target, result in report["targets"].items():
        winner = min(MODEL_NAMES, key=lambda name: result["models"][name]["selection"]["wape"])
        assert result["champion"] == winner
        assert bundle["models"][target].n_iter_ == 12
        for model in MODEL_NAMES:
            assert scores[target][model]["mae"] == pytest.approx(result["models"][model]["test"]["mae"])


def test_intervals_and_empirical_coverage(trained):
    root, snapshot, report = trained
    result = ForecastService(root).predict(snapshot, snapshot.facilities[0].id, "medicine", "IVF", 14)
    for row in result.forecast:
        assert 0 <= row.lower95 <= row.lower80 <= row.point <= row.upper80 <= row.upper95
    assert all(0 <= c["coverage"] <= 1 for target in report["targets"].values() for r in target["coverage"].values() for c in r.values())
    bands = residual_bands(np.ones((30, 14)))
    assert np.all(bands["0.8"] == 1)


def test_no_future_orders_or_realized_deliveries():
    origin = date(2026, 1, 1)
    orders = [ScheduledReceipt(ordered_at=origin, expected_at=origin+timedelta(days=3), quantity=40, lead_time_days=3),
        ScheduledReceipt(ordered_at=origin+timedelta(days=1), expected_at=origin+timedelta(days=4), quantity=9999, lead_time_days=3)]
    receipts = known_receipts(orders, origin)
    assert receipts.sum() == 40 and receipts[2] == 40 and receipts[3] == 0


def test_stock_trajectory_dates_and_probability():
    point = np.full(14, 10.0)
    paths = np.tile(point, (500, 1))
    result = project_stock(25, 15, point, paths, np.zeros(14), date(2026, 1, 1))
    assert result["safety_breach_date"] == "2026-01-02"
    assert result["stockout_date"] == "2026-01-04"
    assert result["probabilities"] == {"3": 1.0, "7": 1.0, "14": 1.0}
    assert result["trajectory"][2]["unmet_demand"] == 5
    assert result["days_of_cover"] == 2.5
    safe = project_stock(1000, 15, point, paths, np.zeros(14), date(2026, 1, 1))
    assert safe["stockout_date"] is None and safe["probabilities"]["14"] == 0


def test_monte_carlo_reproducibility_and_temporal_dependence():
    residuals = np.tile(np.linspace(-1, 1, 20)[:, None], (1, 14))
    a = demand_paths(np.full(14, 5), 1, residuals, "same")
    np.testing.assert_array_equal(a, demand_paths(np.full(14, 5), 1, residuals, "same"))
    np.testing.assert_array_equal(a[:, 0], a[:, -1])


def test_zero_demand_and_zero_stock():
    r = project_stock(0, 0, np.zeros(14), np.zeros((500, 14)), np.zeros(14), date(2026, 1, 1))
    assert r["stockout_date"] == "2026-01-01" and r["days_of_cover"] is None


def test_probability_is_fraction_of_paths_and_remembers_depletion():
    paths = np.vstack([np.ones((250, 14)), np.full((250, 14), 10)])
    receipts = np.zeros(14)
    receipts[1] = 1000
    r = project_stock(5, 2, np.full(14, 5), paths, receipts, date(2026, 1, 1))
    assert r["probabilities"] == {"3": .5, "7": .5, "14": .5}
    assert r["trajectory"][1]["closing_stock"] > 0


def test_each_evaluation_window_scores_its_final_day():
    rows = list(origins_for(540, 0))
    for split, (_, end) in enumerate(split_bounds(540)):
        if split:
            assert max(o+14 for s, o in rows if s == split) == end-1


def test_fitting_is_reproducible(trained):
    from sklearn.base import clone
    from threadpoolctl import threadpool_limits
    root, _, _ = trained
    old = load_bundle("BR", root)["models"]["footfall"]
    with np.load(root / "data/generated/training/BR/footfall.npz") as a, threadpool_limits(limits=2):
        mask = a["split"] == 0
        again = clone(old).fit(a["X"][mask], a["y"][mask]/a["scale"][mask])
        np.testing.assert_allclose(old.predict(a["X"][:50]), again.predict(a["X"][:50]), rtol=1e-12)


def test_transfer_ledger_conservation():
    StockDay(date=date.today(), opening=10, received=5, transfers_received=3, transfers_sent=2, requested=7, consumed=7, unmet_demand=0, closing=9)
    with pytest.raises(ValueError):
        StockDay(date=date.today(), opening=0, received=0, requested=1, consumed=1, unmet_demand=0, closing=0)


@pytest.fixture(scope="module")
def forecast_client(trained):
    root, snapshot, _ = trained
    class Repository:
        mode = "test"
        def snapshot(self):
            return snapshot.model_copy(update={"country": "IN"})
        def country_snapshot(self, country):
            return snapshot if country == "BR" else snapshot.model_copy(update={"country": country, "facilities": []})
    with TestClient(create_app(Repository(), ForecastService(root))) as client:
        yield client


@pytest.mark.parametrize("horizon", [1, 7, 14])
@pytest.mark.parametrize("resource", ["footfall", "beds", "medicines/PCM"])
def test_forecast_routes(forecast_client, horizon, resource):
    response = forecast_client.get(f"/api/forecasts/facilities/BR-SP-001/{resource}?country_id=BR&horizon={horizon}")
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["forecast"]) == horizon and len(result["history"]) == 28
    assert result["forecast"][0]["date"] > result["as_of"]
    assert result["provenance"]["is_synthetic"] is True


@pytest.mark.parametrize("horizon", [0, 2, 30, "bad"])
def test_invalid_horizon(forecast_client, horizon):
    assert forecast_client.get(f"/api/forecasts/facilities/BR-SP-001/footfall?country_id=BR&horizon={horizon}").status_code == 422


def test_country_facility_medicine_isolation(forecast_client):
    assert forecast_client.get("/api/forecasts/facilities/BR-SP-001/footfall?country_id=RU").status_code == 404
    assert forecast_client.get("/api/forecasts/facilities/missing/footfall?country_id=BR").status_code == 404
    assert forecast_client.get("/api/forecasts/facilities/BR-SP-001/medicines/missing?country_id=BR").status_code == 404
    assert forecast_client.get("/api/forecasts/facilities/BR-SP-001/footfall?country_id=XX").status_code == 422
    a = forecast_client.get("/api/forecasts/facilities/BR-SP-001/footfall?country_id=BR").json()
    b = forecast_client.get("/api/forecasts/facilities/BR-SP-002/footfall?country_id=BR").json()
    assert a["facility_id"] != b["facility_id"] and a["forecast"] != b["forecast"]


def test_metrics_and_stockout_routes(forecast_client):
    metrics_response = forecast_client.get("/api/models/forecasting/metrics?country_id=BR")
    assert metrics_response.status_code == 200
    response = forecast_client.get("/api/forecasts/facilities/BR-SP-001/stockout-risks?country_id=BR")
    assert response.status_code == 200 and len(response.json()["items"]) == 5
    assert forecast_client.get("/api/models/forecasting/metrics?country_id=RU").status_code == 503


def test_missing_model_api_does_not_train(trained, tmp_path):
    _, snapshot, _ = trained
    class Repository:
        mode = "test"
        def country_snapshot(self, country):
            return snapshot
    with TestClient(create_app(Repository(), ForecastService(tmp_path))) as client:
        response = client.get("/api/forecasts/facilities/BR-SP-001/footfall?country_id=BR")
        assert response.status_code == 503 and "never trains" in response.json()["detail"]
    assert not (tmp_path / "artifacts").exists()


def test_missing_models_and_stale_snapshot(trained, tmp_path):
    root, snapshot, _ = trained
    with pytest.raises(ModelUnavailable, match="unavailable"):
        ForecastService(tmp_path).predict(snapshot, snapshot.facilities[0].id, "footfall", "footfall")
    changed = snapshot.model_copy(deep=True)
    changed.facilities[0].footfall_today += 1
    with pytest.raises(ModelUnavailable, match="stale"):
        ForecastService(root).predict(changed, changed.facilities[0].id, "footfall", "footfall")


def test_artifact_tampering_rejected(trained, tmp_path):
    import shutil
    root, _, _ = trained
    shutil.copytree(root / "artifacts", tmp_path / "artifacts")
    with (tmp_path / "artifacts/models/BR/bundle.joblib").open("ab") as f:
        f.write(b"tamper")
    with pytest.raises(ModelUnavailable, match="integrity"):
        load_bundle("BR", tmp_path)
