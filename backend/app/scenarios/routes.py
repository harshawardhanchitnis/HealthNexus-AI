from app.profiles.access import snapshot_for, selected_profile
from app.profiles.config import ProfileID
from app.core.runtime import low_memory
import logging
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
from app.models.provenance import CountryCode
from app.forecasting.prediction import ModelUnavailable
from app.scenarios.engine import ScenarioEngine, select
from app.scenarios.effects import parameters
from app.scenarios.models import ScenarioRequest, ScenarioType, ScenarioMetadata
from app.scenarios.schemas import ScenarioResult, PresetResponse
from app.warnings.models import Severity, WarningType, WarningList, WarningSummary, Warning
from app.warnings.engine import listing


def resilience_router(engine: ScenarioEngine):
    router = APIRouter()

    snapshot = snapshot_for

    def safe(action):
        try:
            return action()
        except LookupError as exc:
            raise HTTPException(404, str(exc))
        except ModelUnavailable as exc:
            raise HTTPException(503, str(exc))
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        except Exception:
            logging.exception("Resilience projection unavailable")
            raise HTTPException(503, "Projection unavailable. Check trusted saved models and operational snapshot.")

    @router.get("/api/scenarios/presets", response_model=PresetResponse)
    def presets():
        return {"horizon": 14, "duration_range": [1, 14], "types": [{"scenario_type": t.value,
            "presets": {s: parameters(ScenarioRequest(scenario_type=t, severity=s)) for s in ("moderate", "severe", "critical")}} for t in ScenarioType]}

    @router.post("/api/scenarios", response_model=ScenarioResult, status_code=201)
    def create(body: ScenarioRequest, request: Request):
        return safe(lambda: engine.run(snapshot(request, body.country_id, body.profile), body))

    @router.get("/api/scenarios", response_model=list[ScenarioMetadata])
    def scenarios(country_id: CountryCode = "IN", profile: ProfileID = "constrained"):
        with engine.store.lock:
            return [r.scenario for r in engine.store.results.values() if r.scenario.definition.country_id == country_id and r.scenario.definition.profile == profile]

    @router.get("/api/scenarios/{scenario_id}", response_model=ScenarioResult)
    @router.get("/api/scenarios/{scenario_id}/comparison", response_model=ScenarioResult)
    def get(scenario_id: str, country_id: CountryCode = "IN", profile: ProfileID = "constrained"):
        return safe(lambda: engine.store.get(scenario_id, country_id, profile))

    @router.delete("/api/scenarios/{scenario_id}", status_code=204)
    def discard(scenario_id: str, country_id: CountryCode = "IN", profile: ProfileID = "constrained"):
        safe(lambda: engine.store.discard(scenario_id, country_id, profile))
        return Response(status_code=204)

    def warnings(request, country, state, district, facility, severity, kind, category, scenario):
        data = snapshot(request, country)
        ids = {f.id for f in select(data, state, district, [facility] if facility else None)}
        if scenario:
            all_warnings = engine.store.get(scenario, country, selected_profile(request)).warnings_created.items
        else:
            facilities = [f for f in data.facilities if f.id in ids]
            if low_memory():
                # This endpoint returns warnings, not the discarded national
                # projection. Bound that temporary projection to twelve facilities.
                all_warnings = []
                for start in range(0,len(facilities),12):
                    _, batch = engine.baseline(data,facilities[start:start+12])
                    all_warnings.extend(batch.items)
            else:
                _, all_list = engine.baseline(data,facilities)
                all_warnings = all_list.items
        return listing([w for w in all_warnings if w.facility_id in ids and (not severity or w.severity == severity)
            and (not kind or w.warning_type == kind) and (not category or w.category == category)])

    Category = Literal["medicine", "demand", "beds", "personnel", "emergency"]

    @router.get("/api/warnings", response_model=WarningList)
    def get_warnings(request: Request, country_id: CountryCode = "IN", profile: ProfileID = "constrained", state_id: str | None = None,
        district_id: str | None = None, facility_id: str | None = None, severity: Severity | None = None,
        warning_type: WarningType | None = None, category: Category | None = None, scenario_id: str | None = None):
        return safe(lambda: warnings(request, country_id, state_id, district_id, facility_id, severity, warning_type, category, scenario_id))

    @router.get("/api/warnings/summary", response_model=WarningSummary)
    def summary(request: Request, country_id: CountryCode = "IN", profile: ProfileID = "constrained", state_id: str | None = None,
        district_id: str | None = None, facility_id: str | None = None, scenario_id: str | None = None,
        severity: Severity | None = None, warning_type: WarningType | None = None, category: Category | None = None):
        return safe(lambda: warnings(request, country_id, state_id, district_id, facility_id, severity, warning_type, category, scenario_id).summary)

    @router.get("/api/warnings/{warning_id}", response_model=Warning)
    def detail(warning_id: str, request: Request, country_id: CountryCode = "IN", profile: ProfileID = "constrained", scenario_id: str | None = None, facility_id: str | None = None):
        def find():
            result = warnings(request, country_id, None, None, facility_id, None, None, None, scenario_id)
            match = next((w for w in result.items if w.warning_id == warning_id), None)
            if match is None:
                raise LookupError("Warning not found in selected country/scenario")
            return match
        return safe(find)

    return router
