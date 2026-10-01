from datetime import date, timedelta
import json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from threadpoolctl import ThreadpoolController
from threading import RLock

from app.core.config import ROOT
from app.core.artifact_io import artifact_reader
from app.core.runtime import low_memory, operational_country
from app.core.cache import BoundedCache
from app.forecasting.data import digest, facility_hash
from app.forecasting.features import feature_block, MODEL_NAMES
from app.forecasting.evaluation import intervals
from app.forecasting.stockout import demand_paths, known_receipts, project_stock
from app.forecasting.schemas import ForecastResponse


class ModelUnavailable(ValueError):
    pass


def load_bundle(country: str, root: Path = ROOT):
    operational_country(country)
    folder = root / "artifacts/models" / country
    try:
        integrity = json.loads((folder / "integrity.json").read_text())
        if integrity["sklearn_version"] != sklearn.__version__ or digest(folder / "bundle.joblib") != integrity["sha256"]:
            raise ModelUnavailable("Model version/integrity mismatch. Rebuild trusted local artifacts.")
        with artifact_reader(folder / "bundle.joblib") as stream:
            bundle = joblib.load(stream)
    except FileNotFoundError:
        raise ModelUnavailable(f"Forecast models unavailable for {country}. Run scripts/forecast.py generate, build and train; API startup never trains.")
    if bundle["manifest"]["country_id"] != country:
        raise ModelUnavailable("Model country mismatch")
    bundle["artifact_sha256"] = integrity["sha256"]
    return bundle


class ForecastService:
    def __init__(self, root: Path = ROOT):
        self.low_memory = low_memory()
        self.root, self.cache = root, BoundedCache(1 if self.low_memory else 5)
        self.identities, self.bindings = {}, {}
        self.points = BoundedCache(128 if self.low_memory else 10000)
        self.lock, self.controller = RLock(), None

    def bundle(self, country, profile='constrained'):
        operational_country(country)
        from app.profiles.config import folder
        from app.profiles.binding import bind_profile
        model_dir = self.root / 'artifacts/models' / country
        try:
            identity = tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in
                             (model_dir/'bundle.joblib', model_dir/'integrity.json'))
        except FileNotFoundError:
            return load_bundle(country, self.root)  # consistent actionable error
        with self.lock:
            if self.identities.get(country) != identity:
                self.cache[country] = load_bundle(country, self.root)
                self.identities[country] = identity
                self.bindings = {k:v for k,v in self.bindings.items() if k[0] != country}
                for key in list(self.points):
                    if key[0] == country:
                        del self.points[key]
                for old in list(self.identities):
                    if old not in self.cache:
                        del self.identities[old]
                        self.bindings = {k:v for k,v in self.bindings.items() if k[0] != old}
                        for key in list(self.points):
                            if key[0] == old:
                                del self.points[key]
                # Discover native libraries once, after loading the model libraries.
                self.controller = ThreadpoolController()
            base = self.cache[country]
            path = folder(profile, country, self.root)/'compatibility.json'
            if profile == 'constrained' and not path.exists():
                return base
            return bind_profile(base, country, profile, self.root, self.bindings, identity)

    def point_key(self, snapshot, facility, bundle, target, resource):
        return (snapshot.country,snapshot.operational_profile,snapshot.profile_version,str(snapshot.as_of),
                bundle['artifact_sha256'],facility.id,facility_hash(facility),target,resource)

    def prepare_predictions(self, snapshot, facilities):
        """Batch independent rows through the same champion, without refitting."""
        bundle=self.bundle(snapshot.country,snapshot.operational_profile)
        manifest,report=bundle['manifest'],bundle['report']
        if manifest['as_of'] != str(snapshot.as_of):
            raise ModelUnavailable('Forecast origin mismatch')
        for f in facilities:
            if manifest['facility_hashes'].get(f.id) != facility_hash(f):
                raise ModelUnavailable('Forecast artifact is stale for this snapshot')
        with self.lock:
            for target in ('footfall','admissions','medicine'):
                contexts={(c['facility_id'],c['resource_id']):c for c in manifest['series'][target]}
                rows=[]
                for f in facilities:
                    for resource in ([i.medicine_id for i in f.inventory] if target=='medicine' else [target]):
                        key=self.point_key(snapshot,f,bundle,target,resource)
                        if key in self.points:
                            continue
                        context={**contexts[(f.id,resource)],'trend_offset':manifest['days']-28}
                        x,scale,baseline=feature_block(np.asarray(context['last28']),27,snapshot.as_of-timedelta(days=27),context)
                        rows.append((key,x,scale,baseline))
                if not rows:
                    continue
                champion=report['targets'][target]['champion']
                if champion==MODEL_NAMES[-1]:
                    with self.controller.limit(limits=1 if self.low_memory else 2):
                        predicted=np.maximum(0,bundle['models'][target].predict(np.concatenate([r[1] for r in rows])))
                    points=[predicted[i*14:(i+1)*14]*r[2] for i,r in enumerate(rows)]
                else:
                    points=[r[3][:,MODEL_NAMES.index(champion)].astype(float) for r in rows]
                for row,point in zip(rows,points):
                    point.setflags(write=False)
                    self.points[row[0]]=point

    def predict(self, snapshot, facility_id, target, resource_id, horizon=14, *, _bundle=None):
        operational_country(snapshot.country)
        from app.profiles.config import VERSION
        if snapshot.profile_version != VERSION:
            raise ModelUnavailable("Unsupported inventory profile version")
        if horizon not in (1, 7, 14):
            raise ValueError("Horizon must be 1, 7 or 14")
        facility = next((f for f in snapshot.facilities if f.id == facility_id), None)
        if facility is None:
            raise LookupError("Facility not found in selected country")
        if target == "medicine" and not any(i.medicine_id == resource_id for i in facility.inventory):
            raise LookupError("Medicine not found at this facility")
        bundle = _bundle or self.bundle(snapshot.country, snapshot.operational_profile)
        manifest, report = bundle["manifest"], bundle["report"]
        if manifest["as_of"] != str(snapshot.as_of) or manifest["facility_hashes"].get(facility_id) != facility_hash(facility):
            raise ModelUnavailable("Forecast artifact is stale for this snapshot. Rebuild training tables/models from matching history and restart the backend.")
        context = next(c for c in manifest["series"][target] if c["facility_id"] == facility_id and c["resource_id"] == resource_id)
        as_of = date.fromisoformat(manifest["as_of"])
        start = as_of-timedelta(days=27)
        context = {**context, "trend_offset": manifest["days"]-28}
        values = np.asarray(context["last28"])
        with self.lock:
            prepared = self.points.get(self.point_key(snapshot,facility,bundle,target,resource_id))
        if prepared is None:
            x, scale, baseline = feature_block(values, 27, start, context)
        else:
            scale = max(1.,float(values.mean()))
        champion = report["targets"][target]["champion"]
        if prepared is not None:
            point = prepared
        elif champion == MODEL_NAMES[-1]:
            with self.lock, self.controller.limit(limits=1 if self.low_memory else 2):
                point = np.maximum(0, bundle["models"][target].predict(x))*scale
        else:
            point = baseline[:, MODEL_NAMES.index(champion)].astype(float)
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
            provenance={"model_sha256": bundle.get('artifact_sha256'), "operational_profile": snapshot.operational_profile, "profile_version": snapshot.profile_version,
                "operational_history_sha256": manifest.get('operational_history_sha256', manifest['history_sha256']),
                "data_type": manifest["data_type"], "model_version": report["model_version"], "model": champion,
                "trained_through": manifest["windows"]["train"]["end"], "evaluated_at": report["evaluated_at"],
                "windows": manifest["windows"], "history_sha256": manifest["history_sha256"],
                "calibration_sources": manifest["calibration"]["inputs"], "source_vintage_note": manifest["source_vintage_note"],
                "uncertainty_method": report["uncertainty_method"]},
            test_metric=report["targets"][target]["models"][champion]["test"],
            coverage=report["targets"][target]["coverage"][resource_id], explanations=explanations, stockout=stockout)
