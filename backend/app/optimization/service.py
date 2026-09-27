from datetime import datetime, timezone
import hashlib
from threading import RLock
from uuid import uuid4
import numpy as np
from app.forecasting.data import facility_hash
from app.forecasting.stockout import demand_paths
from app.scenarios.engine import select
from app.optimization.config import POLICY as P, LIMITATIONS
from app.optimization.schemas import Preview, PlanResult
from app.optimization.candidates import candidates, make_edges
from app.optimization.solver import solve, greedy
from app.optimization.impact import apply_plan
from app.warnings.engine import evaluate


def fingerprint(snapshot, facilities):
    return hashlib.sha256((str(snapshot.as_of)+snapshot.country+''.join(facility_hash(f) for f in sorted(facilities, key=lambda f: f.id))).encode()).hexdigest()


class OptimizationService:
    def __init__(self, scenarios):
        self.scenarios = scenarios
        self.results = {}
        self.lock = RLock()

    def prepare(self, snapshot, request):
        if snapshot.country != request.country_id:
            raise ValueError("Planning and snapshot country mismatch")
        selected = select(snapshot, request.state_id, request.district_id)
        receiver_ids = {f.id for f in selected}
        scope_facilities = select(snapshot, request.state_id if request.scope == "state" else None,
            request.district_id if request.scope == "district" else None)
        if any(f.country_id != request.country_id for f in scope_facilities):
            raise ValueError("International redistribution is prohibited")
        bundle = self.scenarios.forecasts.bundle(snapshot.country)
        scenario, scenario_snapshot = None, None
        overlay = {}
        if request.scenario_id:
            scenario = self.scenarios.store.get(request.scenario_id, request.country_id)
            definition = scenario.scenario.definition
            original = select(snapshot, definition.state_id, definition.district_id, definition.facility_ids)
            scenario_snapshot = fingerprint(snapshot, original)
            if scenario_snapshot != scenario.scenario.baseline_snapshot_id or scenario.scenario.origin != snapshot.as_of:
                raise ValueError("Scenario baseline identity no longer matches current snapshot")
            overlay = {f.facility_id: f for f in scenario.scenario_result.facilities}
            if any(f.provenance.model_version != bundle["report"]["model_version"] for f in overlay.values()):
                raise ValueError("Scenario model version no longer matches planning model")
            receiver_ids &= overlay.keys()
            if not receiver_ids:
                raise ValueError("Scenario has no affected facilities in selected receiver scope")
        baseline, _ = self.scenarios.baseline(snapshot, scope_facilities)
        projections = [overlay.get(f.facility_id, f).model_copy(deep=True) for f in baseline.facilities]
        projections.sort(key=lambda f: f.facility_id)
        paths, warnings = {}, []
        for f in projections:
            physical = next(x for x in scope_facilities if x.id == f.facility_id)
            forecasts, _ = self.scenarios.inputs(snapshot, physical)
            affected = f.facility_id in overlay
            seed = scenario.scenario.definition.seed if scenario and affected else 42
            for r in f.resources:
                base = forecasts[r.resource_id]
                point = np.array([p.point for p in base.forecast])
                context = next(c for c in bundle["manifest"]["series"]["medicine"] if c["facility_id"] == f.facility_id and c["resource_id"] == r.resource_id)
                scale = max(1., float(np.mean(context["last28"])))
                key = f"{base.provenance.model_version}:{f.facility_id}:{r.resource_id}"
                if seed != 42:
                    key += f":scenario-seed-{seed}"
                paths[(f.facility_id, r.resource_id)] = demand_paths(point, scale, bundle["residuals"]["medicine"][r.resource_id], key) + (np.array([p.point for p in r.forecast])-point)[None, :]
            warnings.extend(evaluate(f, snapshot.as_of, request.scenario_id if affected else None,
                scenario.scenario.definition.scenario_type.value if scenario and affected else None))
        donors, receivers = candidates(projections, paths, warnings, snapshot.as_of, receiver_ids, request.resources)
        # Keep only resource pools requested by a receiver; all safe capacities for
        # these resources remain visible even if the domestic scope has no edge.
        donors = [d for d in donors if d.resource_id in {r.resource_id for r in receivers}]
        edges = make_edges(donors, receivers, {f.id: f for f in scope_facilities}, request.country_id, request.scope)
        preview = Preview(request=request, snapshot_id=fingerprint(snapshot, scope_facilities), scenario_snapshot_id=scenario_snapshot,
            scenario_facility_ids=sorted(overlay), origin=snapshot.as_of, config_version=P.version, model_version=bundle["report"]["model_version"],
            receivers=receivers, donors=donors, edges=edges, total_deficit=sum(r.deficit for r in receivers),
            safe_capacity=sum(d.safe_surplus for d in donors),
            capacity_by_resource={c: sum(d.safe_surplus for d in donors if d.resource_id == c) for c in request.resources},
            deficit_by_resource={c: sum(r.deficit for r in receivers if r.resource_id == c) for c in request.resources}, limitations=LIMITATIONS)
        return preview, projections, paths, scenario.scenario.definition.scenario_type.value if scenario else None

    def preview(self, snapshot, request):
        return self.prepare(snapshot, request)[0]

    def run(self, snapshot, request):
        preview, projections, paths, scenario_type = self.prepare(snapshot, request)
        quantities, metadata = solve(preview.donors, preview.receivers, preview.edges, request.time_limit_seconds)
        run_id = str(uuid4())
        impact, transfers, after, before_warnings, after_warnings = apply_plan(projections, paths, preview, quantities, snapshot.as_of, run_id, metadata.status, scenario_type)
        greedy_impact, greedy_transfers, *_ = apply_plan(projections, paths, preview,
            greedy(preview.donors, preview.receivers, preview.edges), snapshot.as_of, run_id+"-greedy", "FEASIBLE", scenario_type)
        capacity_insufficient = any(preview.capacity_by_resource[c] < preview.deficit_by_resource[c] for c in request.resources)
        message = "All selected target deficits are covered by the proposed plan."
        if metadata.objective is None:
            message = "Solver returned no incumbent plan. No transfers are proposed; retry with a longer time limit."
        elif impact.after.target_deficit:
            message = "Network resources are insufficient to completely resolve this shortage." if capacity_insufficient else "Unresolved deficits remain in this time-limited feasible plan."
        detail_ids = {r.facility_id for r in preview.receivers} | {t.donor_id for t in transfers+greedy_transfers}
        result = PlanResult(run_id=run_id, created_at=datetime.now(timezone.utc), preview=preview,
            solver=metadata, transfers=transfers, impact=impact, greedy=greedy_impact, greedy_transfers=greedy_transfers,
            before=[f for f in projections if f.facility_id in detail_ids], after=[f for f in after if f.facility_id in detail_ids],
            before_warnings=before_warnings, after_warnings=after_warnings, message=message)
        with self.lock:
            if len(self.results) >= P.max_runs:
                raise ValueError("Stored planning limit reached; discard an existing plan")
            self.results[run_id] = result.model_copy(deep=True)
        return result

    def get(self, run_id, country):
        with self.lock:
            result = self.results.get(run_id)
            if not result or result.preview.request.country_id != country:
                raise LookupError("Plan not found in selected country")
            return result.model_copy(deep=True)

    def discard(self, run_id, country):
        with self.lock:
            self.get(run_id, country)
            del self.results[run_id]
