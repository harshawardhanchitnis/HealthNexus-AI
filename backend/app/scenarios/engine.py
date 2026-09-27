from datetime import datetime, timedelta, timezone
import hashlib
from threading import RLock
from uuid import uuid4
from app.core import risk_config as C
from app.forecasting.prediction import ForecastService
from app.forecasting.data import facility_hash
from app.scenarios.effects import project, parameters
from app.scenarios.comparison import outcome, compare
from app.scenarios.models import ScenarioRequest, ScenarioMetadata
from app.scenarios.schemas import ScenarioResult
from app.scenarios.state import ScenarioStore
from app.warnings.engine import evaluate, listing

ASSUMPTIONS = [
    "Operational resilience digital twin using simulated facility records; not an epidemiological or clinically validated model.",
    "Baseline forecasts come from saved Phase 3 country-local champions; no model is retrained for scenarios.",
    "Dengue adds externally specified fever visits. Existing non-fever demand is unchanged. Extra medicines use existing syndrome/resource coefficients, not treatment guidance.",
    "Extra fever admissions use an assumed 0.10 rate. Bed discharge rate is frozen from recent observed flows. Existing occupants above disrupted capacity remain explicit overflow.",
    "Service capacity is recent mean visits × 1.25 headroom, scaled by attendance and facility availability. No role-specific or clinical effects are inferred.",
    "Medicine requests remain demand-side needs even when service capacity is exceeded. Unserved visits are daily pressure, not a patient queue.",
    "Daily projection spans 14 days; shocks apply only inside the selected event window. Inventory/bed effects can persist after it ends.",
    "Known receipts only; selected future arrivals shift in delivery-delay scenarios. No future orders, transfers or patient spillover.",
    "500 paired residual paths reuse Phase 3 calibration errors. Scenario bands and probabilities condition on fixed assumptions; shock uncertainty and real outbreak accuracy are unvalidated.",
    "Process-local scenarios survive navigation, not server restarts; maximum 20 stored runs. Baseline data is never overwritten.",
]


def select(snapshot, state=None, district=None, facility_ids=None):
    if state and not any(r.id == state for r in snapshot.regions):
        raise LookupError("Region not found in selected country")
    if district and not any(d.id == district and (not state or d.state_id == state) for d in snapshot.districts):
        raise LookupError("District not found in selected region")
    facilities = [f for f in snapshot.facilities if (not state or f.state_id == state) and (not district or f.district_id == district)]
    if facility_ids:
        if set(facility_ids)-{f.id for f in facilities}:
            raise LookupError("Selected facilities do not belong to the requested geography")
        facilities = [f for f in facilities if f.id in facility_ids]
    if not facilities:
        raise LookupError("No facilities in selected scope")
    return facilities


class ScenarioEngine:
    def __init__(self, forecasts=None):
        self.forecasts = forecasts or ForecastService()
        self.store = ScenarioStore()
        self.cache = {}
        self.baseline_cache = {}
        self.lock = RLock()

    def inputs(self, snapshot, facility):
        bundle = self.forecasts.bundle(snapshot.country)
        key = (snapshot.country, str(snapshot.as_of), facility.id, facility_hash(facility), bundle["report"]["model_version"])
        with self.lock:
            if key not in self.cache:
                predictions = {target: self.forecasts.predict(snapshot, facility.id, target, target) for target in ("footfall", "admissions")}
                predictions.update({i.medicine_id: self.forecasts.predict(snapshot, facility.id, "medicine", i.medicine_id) for i in facility.inventory})
                if len(self.cache) >= 300:
                    self.cache.clear()
                self.cache[key] = predictions
            return self.cache[key], bundle

    def baseline(self, snapshot, facilities):
        projections, warnings = [], []
        for f in facilities:
            forecasts, bundle = self.inputs(snapshot, f)
            key = (snapshot.country, str(snapshot.as_of), f.id, facility_hash(f), bundle["report"]["model_version"])
            with self.lock:
                if key not in self.baseline_cache:
                    if len(self.baseline_cache) >= 300:
                        self.baseline_cache.clear()
                    projected = project(f, forecasts, bundle, snapshot.as_of)
                    self.baseline_cache[key] = (projected, evaluate(projected, snapshot.as_of))
                cached, alerts = self.baseline_cache[key]
                projection = cached.model_copy(deep=True)
            projections.append(projection)
            warnings.extend(w.model_copy(deep=True) for w in alerts)
        return outcome(projections, warnings), listing(warnings)

    def run(self, snapshot, definition: ScenarioRequest):
        if definition.country_id != snapshot.country:
            raise ValueError("Scenario and baseline country mismatch")
        request = definition.model_copy(deep=True)
        request.start_date = request.start_date or snapshot.as_of+timedelta(days=1)
        if request.start_date <= snapshot.as_of or (request.start_date-snapshot.as_of).days+request.duration-1 > C.HORIZON:
            raise ValueError("Event must start after the forecast origin and fit entirely within its 14-day horizon")
        facilities = [f.model_copy(deep=True) for f in select(snapshot, request.state_id, request.district_id, request.facility_ids)]
        scenario_id = str(uuid4())
        base, changed, warnings, base_warnings = [], [], [], []
        for f in facilities:
            forecasts, bundle = self.inputs(snapshot, f)
            b = project(f, forecasts, bundle, snapshot.as_of, seed=request.seed)
            w = evaluate(b, snapshot.as_of)
            s = project(f, forecasts, bundle, snapshot.as_of, request, request.seed)
            base.append(b)
            changed.append(s)
            base_warnings.extend(w)
            warnings.extend(evaluate(s, snapshot.as_of, scenario_id, request.scenario_type.value, w))
        before, after = outcome(base, base_warnings), outcome(changed, warnings)
        deltas, impacts = compare(before, after)
        fingerprint = hashlib.sha256((str(snapshot.as_of)+snapshot.country+''.join(facility_hash(f) for f in sorted(facilities, key=lambda x: x.id))).encode()).hexdigest()
        result = ScenarioResult(scenario=ScenarioMetadata(scenario_id=scenario_id, definition=request,
            created_at=datetime.now(timezone.utc), baseline_snapshot_id=fingerprint, origin=snapshot.as_of,
            config_version=C.CONFIG_VERSION, effective_parameters=parameters(request), assumptions=ASSUMPTIONS),
            baseline=before, scenario_result=after, delta=deltas, resource_impact=impacts,
            baseline_warnings=listing(base_warnings), warnings_created=listing(warnings))
        self.store.put(result)
        return result.model_copy(deep=True)
