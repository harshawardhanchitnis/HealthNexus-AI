from datetime import date, timedelta
import json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from threadpoolctl import threadpool_limits

from app.core.config import ROOT
from app.forecasting.data import digest, facility_hash
from app.forecasting.features import feature_block, MODEL_NAMES
from app.forecasting.evaluation import intervals
from app.forecasting.stockout import demand_paths, known_receipts, project_stock
from app.forecasting.schemas import ForecastResponse


class ModelUnavailable(ValueError):
    pass


def load_bundle(country: str, root: Path = ROOT):
    folder = root / "artifacts/models" / country
    try:
        integrity = json.loads((folder / "integrity.json").read_text())
        if integrity["sklearn_version"] != sklearn.__version__ or digest(folder / "bundle.joblib") != integrity["sha256"]:
            raise ModelUnavailable("Model version/integrity mismatch. Rebuild trusted local artifacts.")
        bundle = joblib.load(folder / "bundle.joblib")
    except FileNotFoundError:
        raise ModelUnavailable(f"Forecast models unavailable for {country}. Run scripts/forecast.py generate, build and train; API startup never trains.")
    if bundle["manifest"]["country_id"] != country:
        raise ModelUnavailable("Model country mismatch")
    return bundle


class ForecastService:
    def __init__(self, root: Path = ROOT):
        self.root, self.cache = root, {}

    def bundle(self, country):
        if country not in self.cache:
            self.cache[country] = load_bundle(country, self.root)
        return self.cache[country]

    def predict(self, snapshot, facility_id, target, resource_id, horizon=14):
        if horizon not in (1, 7, 14):
            raise ValueError("Horizon must be 1, 7 or 14")
        facility = next((f for f in snapshot.facilities if f.id == facility_id), None)
        if facility is None:
            raise LookupError("Facility not found in selected country")
        if target == "medicine" and not any(i.medicine_id == resource_id for i in facility.inventory):
            raise LookupError("Medicine not found at this facility")
        bundle = self.bundle(snapshot.country)
        manifest, report = bundle["manifest"], bundle["report"]
        if manifest["as_of"] != str(snapshot.as_of) or manifest["facility_hashes"].get(facility_id) != facility_hash(facility):
            raise ModelUnavailable("Forecast artifact is stale for this snapshot. Rebuild training tables/models from matching history and restart the backend.")
        context = next(c for c in manifest["series"][target] if c["facility_id"] == facility_id and c["resource_id"] == resource_id)
        as_of = date.fromisoformat(manifest["as_of"])
        start = as_of-timedelta(days=27)
        context = {**context, "trend_offset": manifest["days"]-28}
        values = np.asarray(context["last28"])
        x, scale, baseline = feature_block(values, 27, start, context)
        champion = report["targets"][target]["champion"]
        with threadpool_limits(limits=2):
            point = np.maximum(0, bundle["models"][target].predict(x))*scale if champion == MODEL_NAMES[-1] else baseline[:, MODEL_NAMES.index(champion)].astype(float)
        bands = intervals(point, scale, bundle["bands"][target][resource_id])
        paths = demand_paths(point, scale, bundle["residuals"][target][resource_id], f"{report['model_version']}:{facility_id}:{resource_id}")
        total = paths[:, :horizon].sum(axis=1)
        recent, expected = float(values[-7:].mean()), float(point[:horizon].mean())
        prior = float(values[-14:-7].mean())
        change = 100*(expected/recent-1) if recent else None
        explanations = [f"Observed requested demand averaged {recent:.2f} per day over the last 7 days versus {prior:.2f} in the preceding week.",
            f"Selected {champion} using chronological selection-window WAPE; test observations were excluded from fitting and selection.",
            "These are observed context and model-selection facts, not causal feature attributions."]
        stockout = None
        if target == "medicine":
            item = next(i for i in facility.inventory if i.medicine_id == resource_id)
            stockout = project_stock(item.current_stock, item.safety_stock, point, paths,
                known_receipts(item.scheduled_deliveries, as_of), as_of)
            explanations.append(f"Last 7 days: {sum(r.requested for r in item.ledger[-7:])} requested, {sum(r.consumed for r in item.ledger[-7:])} fulfilled; unmet demand is retained in the forecast target.")
        return ForecastResponse(country_id=snapshot.country, facility_id=facility_id, resource_id=resource_id,
            target=target, horizon=horizon, as_of=as_of, unit=context["unit"],
            history=[{"date": start+timedelta(days=i), "value": value} for i, value in enumerate(values)],
            forecast=[{"date": as_of+timedelta(days=i+1), "point": point[i], "lower80": bands["0.8"][0][i],
                "upper80": bands["0.8"][1][i], "lower95": bands["0.95"][0][i], "upper95": bands["0.95"][1][i]} for i in range(horizon)],
            summary={"latest_demand": values[-1], "recent_daily_mean": recent, "forecast_daily_mean": expected,
                "forecast_total": float(point[:horizon].sum()), "change_percent": change,
                "total_lower80": float(np.quantile(total, .1)), "total_upper80": float(np.quantile(total, .9)),
                "total_lower95": float(np.quantile(total, .025)), "total_upper95": float(np.quantile(total, .975))},
            provenance={"data_type": manifest["data_type"], "model_version": report["model_version"], "model": champion,
                "trained_through": manifest["windows"]["train"]["end"], "evaluated_at": report["evaluated_at"],
                "windows": manifest["windows"], "history_sha256": manifest["history_sha256"],
                "calibration_sources": manifest["calibration"]["inputs"], "source_vintage_note": manifest["source_vintage_note"],
                "uncertainty_method": report["uncertainty_method"]},
            test_metric=report["targets"][target]["models"][champion]["test"],
            coverage=report["targets"][target]["coverage"][resource_id], explanations=explanations, stockout=stockout)
