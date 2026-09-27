"""Chronological selection, disjoint residual calibration, untouched final testing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from app.core.config import ROOT
from app.data_ingestion.base import save_json
from app.forecasting.data import TARGETS, digest
from app.forecasting.features import MODEL_NAMES, HORIZON
from app.forecasting.evaluation import metrics, residual_bands


def train_country(country: str, root: Path = ROOT, iterations: int = 100):
    folder = root / "data/generated/training" / country
    manifest = json.loads((folder / "manifest.json").read_text())
    config = {"max_iter": iterations, "max_leaf_nodes": 15, "learning_rate": .08,
        "l2_regularization": 1, "loss": "absolute_error", "early_stopping": False,
        "random_state": manifest["seed"]}
    version = hashlib.sha256((digest(folder / "manifest.json") + json.dumps(config, sort_keys=True) + sklearn.__version__).encode()).hexdigest()[:16]
    report = {"country_id": country, "model_version": f"forecast-v1-{version}",
        "evaluated_at": datetime.now(timezone.utc).isoformat(), "windows": manifest["windows"],
        "data_type": manifest["data_type"], "history_sha256": manifest["history_sha256"],
        "feature_schema": manifest["feature_schema"], "config": config, "sklearn_version": sklearn.__version__,
        "selection_rule": "Lowest selection-window WAPE across all 14 daily horizons; test never selects champion.",
        "uncertainty_method": "Per-resource/horizon absolute normalized residual quantiles from a separate calibration period; marginal daily 80%/95% intervals, no exchangeability guarantee.",
        "source_vintage_note": manifest["source_vintage_note"], "targets": {}}
    bundle = {"manifest": manifest, "report": report, "models": {}, "residuals": {}, "bands": {}}
    with threadpool_limits(limits=2):
        for target in TARGETS:
            path = folder / f"{target}.npz"
            if digest(path) != manifest["tables"][target]["sha256"]:
                raise ValueError("Training table hash mismatch")
            with np.load(path, allow_pickle=False) as a:
                X, y, scale = a["X"], a["y"], a["scale"]
                train, select, cal, test = (a["split"] == i for i in range(4))
                if not (a["target_day"][train].max() < a["target_day"][select].min() and
                    a["target_day"][select].max() < a["target_day"][cal].min() and a["target_day"][cal].max() < a["target_day"][test].min()):
                    raise ValueError("Temporal partition overlap")
                model = HistGradientBoostingRegressor(**config).fit(X[train], y[train]/scale[train])
                predicted = np.column_stack([a["baselines"], np.maximum(0, model.predict(X))*scale])
                comparison = {name: {"selection": metrics(y[select], predicted[select, i]),
                    "test": metrics(y[test], predicted[test, i]),
                    "test_by_horizon": {str(h): metrics(y[test & (X[:, 0] == h)], predicted[test & (X[:, 0] == h), i]) for h in (1, 7, 14)}}
                    for i, name in enumerate(MODEL_NAMES)}
                champion = min(MODEL_NAMES, key=lambda name: comparison[name]["selection"]["wape"] if comparison[name]["selection"]["wape"] is not None else float("inf"))
                idx = MODEL_NAMES.index(champion)
                resources = {c["resource_id"] for c in manifest["series"][target]}
                residuals, bands, coverage = {}, {}, {}
                for resource in sorted(resources):
                    ids = [i for i, c in enumerate(manifest["series"][target]) if c["resource_id"] == resource]
                    cmask, tmask = cal & np.isin(a["series"], ids), test & np.isin(a["series"], ids)
                    paths = ((y[cmask]-predicted[cmask, idx])/scale[cmask]).reshape(-1, HORIZON)
                    residuals[resource], bands[resource] = paths, residual_bands(paths)
                    coverage[resource] = {}
                    for level, widths in bands[resource].items():
                        halfwidth = widths[X[tmask, 0].astype(int)-1] * scale[tmask]
                        low, high = np.maximum(0, predicted[tmask, idx]-halfwidth), predicted[tmask, idx]+halfwidth
                        coverage[resource][level] = {"coverage": float(np.mean((y[tmask]>=low) & (y[tmask]<=high))),
                            "mean_width": float(np.mean(high-low)), "samples": int(tmask.sum()), "calibration_paths": len(paths)}
                report["targets"][target] = {"champion": champion, "models": comparison, "coverage": coverage,
                    "train_rows": int(train.sum()), "selection_rows": int(select.sum()),
                    "calibration_rows": int(cal.sum()), "test_rows": int(test.sum())}
                bundle["models"][target], bundle["residuals"][target], bundle["bands"][target] = model, residuals, bands
                print(f"{country}/{target}: {champion}; test WAPE={comparison[champion]['test']['wape']:.6f}", flush=True)
    out = root / "artifacts/models" / country
    out.mkdir(parents=True, exist_ok=True)
    # Trusted local artifacts only: joblib is not safe for untrusted uploads.
    joblib.dump(bundle, out / "bundle.tmp", compress=3)
    (out / "bundle.tmp").replace(out / "bundle.joblib")
    save_json(out / "metrics.json", report)
    save_json(out / "integrity.json", {"sha256": digest(out / "bundle.joblib"), "sklearn_version": sklearn.__version__})
    return report


def evaluate_saved(country: str, root: Path = ROOT):
    from app.forecasting.prediction import load_bundle
    bundle = load_bundle(country, root)
    folder = root / "data/generated/training" / country
    result = {}
    with threadpool_limits(limits=2):
        for target in TARGETS:
            path = folder / f"{target}.npz"
            if digest(path) != bundle["manifest"]["tables"][target]["sha256"]:
                raise ValueError("Evaluation table changed since training")
            with np.load(path, allow_pickle=False) as a:
                mask = a["split"] == 3
                ml = np.maximum(0, bundle["models"][target].predict(a["X"][mask])) * a["scale"][mask]
                pred = np.column_stack([a["baselines"][mask], ml])
                result[target] = {name: metrics(a["y"][mask], pred[:, i]) for i, name in enumerate(MODEL_NAMES)}
                for name in MODEL_NAMES:
                    expected = bundle["report"]["targets"][target]["models"][name]["test"]
                    if not np.isclose(result[target][name]["mae"], expected["mae"], rtol=1e-7):
                        raise ValueError("Loaded model does not reproduce evaluation")
    return result
