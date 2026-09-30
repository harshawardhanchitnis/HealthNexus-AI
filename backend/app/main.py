from app.profiles.access import snapshot_for, selected_profile
from app.profiles.config import NOTICES, VERSION, ProfileID
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.core.geography import COUNTRIES, COUNTRY_BY_ID
from app.data_ingestion.catalog import datasets
from app.models.provenance import CountryCode
from app.models.network import Snapshot, Status
from app.services.repository import NetworkRepository, create_repository
from app.services.summary import aggregate_history, summarize
from app.simulation.calibration import calibration_for
from app.forecasting.routes import forecast_router
from app.forecasting.prediction import ForecastService
from app.scenarios.engine import ScenarioEngine
from app.scenarios.routes import resilience_router
from app.optimization.service import OptimizationService
from app.optimization.routes import optimization_router


def create_app(repository: NetworkRepository | None = None, forecast_service=None, federation_service=None) -> FastAPI:
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repository = repository or create_repository(settings)
        yield
        app.state.federation.close()

    app = FastAPI(title="HealthNexus AI", version="0.8.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
        allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])

    @app.middleware("http")
    async def profile_notice(request, call_next):
        try:
            request.state.operational_profile = selected_profile(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail":exc.detail})
        response = await call_next(request)
        response.headers["X-Operational-Profile"] = request.state.operational_profile
        response.headers["X-Profile-Version"] = VERSION
        return response

    @app.get("/api/operational-profiles")
    def profiles():
        return {"items":[{"id":p,"version":VERSION,"notice":notice,"data_type":"calibrated simulated operations"} for p,notice in NOTICES.items()]}

    def dataset(request: Request, country_id: CountryCode = "IN", profile: ProfileID = "constrained") -> Snapshot:
        try:
            return snapshot_for(request, country_id)
        except Exception:
            logging.exception("Unable to read healthcare network")
            raise HTTPException(status_code=503, detail="Network data is unavailable. Check backend storage configuration.")

    def filtered(data: Snapshot, state_id: str | None, district_id: str | None):
        if state_id and not any(r.id == state_id for r in data.regions):
            raise HTTPException(404, "Region not found in selected country")
        if district_id and not any(d.id == district_id and (not state_id or d.state_id == state_id) for d in data.districts):
            raise HTTPException(404, "District not found in selected scope")
        return [f for f in data.facilities if (not state_id or f.state_id == state_id) and (not district_id or f.district_id == district_id)]

    @app.get("/api/health")
    def health(request: Request, data: Snapshot = Depends(dataset)):
        return {"status": "ok", "service": "HealthNexus AI", "country": data.country,
            "storage": request.app.state.repository.mode, "synthetic": True, "as_of": data.as_of}

    @app.get("/api/countries")
    def countries():
        return {"items": COUNTRIES, "federation_status": "experimental_fedavg",
            "scope_note": "Five configured hackathon nodes; not an exhaustive list of current BRICS members.",
            "redistribution": "domestic_only"}

    @app.get("/api/data-sources")
    def data_sources(country_id: CountryCode | None = None, profile: ProfileID = "constrained"):
        try:
            sources = datasets()
        except (ValueError, OSError):
            logging.exception("Public data cache is invalid")
            raise HTTPException(503, "Public data cache failed validation. Re-import the attributed snapshots.")
        records = [row for source in sources for row in source.records if not country_id or row.country_id == country_id]
        return {"operational_profile": profile, "profile_version": VERSION, "operational_notice": NOTICES[profile], "datasets": [{"provenance": source.provenance, "status": "Integrated — calibration and public reference",
                    "cached": True, "record_count": len(source.records), "adapter_version": source.adapter_version,
                    "fields": sorted({row.indicator for row in source.records}),
                    "reference_years": sorted({row.year for row in source.records}), "skipped_records": source.skipped_records}
                for source in sources],
            "records": records, "expected_adapters": ["india_hdi", "who_gho"],
            "notice": "Public observations are historical aggregates. Facility operations are simulated; calibration does not make them live or official.",
            "layers": ["official_public", "public_international", "derived", "synthetic", "simulation"],
            "simulation_status": "operational_resilience_scenarios",
            "calibration": calibration_for(country_id or "IN")}

    @app.get("/api/regions")
    def regions(data: Snapshot = Depends(dataset)):
        return {"country": data.country, "regions": data.regions, "districts": data.districts}

    @app.get("/api/overview")
    def overview(state_id: str | None = None, district_id: str | None = None, data: Snapshot = Depends(dataset)):
        facilities = filtered(data, state_id, district_id)
        ids = {f.id for f in facilities}
        alerts = [a for a in data.alerts if a.facility_id in ids]
        return {"operational_profile": data.operational_profile, "profile_version": data.profile_version, "as_of": data.as_of, "synthetic": True, "country": COUNTRY_BY_ID[data.country],
            "schema_version": data.schema_version, "calibration": data.calibration,
            "scope": {"country_id": data.country, "state_id": state_id, "district_id": district_id},
            "summary": {**summarize(facilities), "active_alerts": len(alerts)},
            "history": aggregate_history(facilities), "alerts": alerts[:6],
            "regions": [{**r.model_dump(), **summarize([f for f in facilities if f.state_id == r.id])}
                for r in data.regions if not state_id or r.id == state_id],
            "coverage": {"regions": len(data.regions), "complete_regions": data.country == "IN",
                "states": sum(r.kind == "state" for r in data.regions),
                "union_territories": sum(r.kind == "union_territory" for r in data.regions),
                "sample_districts": len(data.districts),
                "notice": "All Indian states/UTs; illustrative districts and facilities." if data.country == "IN" else "Representative regional nodes and fictional facilities; not complete national coverage."}}

    @app.get("/api/facilities")
    def facilities(state_id: str | None = None, district_id: str | None = None,
        status: Status | None = None, search: str = Query("", max_length=120),
        offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=250), data: Snapshot = Depends(dataset)):
        items = filtered(data, state_id, district_id)
        items = [f for f in items if (not status or f.status == status) and
            (search.casefold() in f.name.casefold() or search.casefold() in f.id.casefold())]
        return {"total": len(items), "offset": offset, "limit": limit,
            "items": [f.model_dump(exclude={"history", "inventory"}) for f in items[offset:offset+limit]]}

    @app.get("/api/facilities/{facility_id}")
    def facility(facility_id: str, data: Snapshot = Depends(dataset)):
        result = next((f for f in data.facilities if f.id == facility_id), None)
        if result is None:
            raise HTTPException(404, "Facility not found")
        return {"facility": result, "alerts": [a for a in data.alerts if a.facility_id == facility_id],
            "operational_profile": data.operational_profile, "profile_version": data.profile_version, "as_of": data.as_of, "country": COUNTRY_BY_ID[data.country], "provenance": data.provenance,
            "calibration": data.calibration}

    @app.get("/api/inventory")
    def inventory(state_id: str | None = None, district_id: str | None = None,
        data: Snapshot = Depends(dataset)):
        facilities = filtered(data, state_id, district_id)
        codes = sorted({item.medicine_id for f in facilities for item in f.inventory})
        result = []
        for code in codes:
            items = [item for f in facilities for item in f.inventory if item.medicine_id == code]
            result.append({"medicine_id": code, "name": items[0].name, "unit": items[0].unit,
                "current_stock": sum(i.current_stock for i in items),
                "daily_consumption": round(sum(i.average_daily_consumption for i in items), 1),
                "facilities_below_reserve": sum(i.days_of_cover < 7 for i in items), "facilities": len(items)})
        return {"items": result, "synthetic": True}

    @app.get("/api/alerts")
    def alerts(state_id: str | None = None, district_id: str | None = None,
        severity: Status | None = None, data: Snapshot = Depends(dataset)):
        ids = {f.id for f in filtered(data, state_id, district_id)}
        items = [a for a in data.alerts if a.facility_id in ids and (not severity or a.severity == severity)]
        return {"items": items, "total": len(items)}

    forecasts = forecast_service or ForecastService()
    app.include_router(forecast_router(forecasts))
    scenarios = ScenarioEngine(forecasts)
    app.include_router(resilience_router(scenarios))
    planner = OptimizationService(scenarios)
    app.include_router(optimization_router(planner))
    from app.geospatial import geospatial_router
    app.include_router(geospatial_router(scenarios, planner))
    from app.ai.orchestrator import CopilotService
    from app.ai.routes import copilot_router
    app.state.copilot = CopilotService(scenarios, planner)
    app.include_router(copilot_router(app.state.copilot))
    from app.federation.service import FederationService
    from app.federation.routes import federation_router
    app.state.federation = federation_service or FederationService()
    app.include_router(federation_router(app.state.federation))
    @app.get('/health')
    def liveness():
        return {'status':'ok', 'service':'HealthNexus AI'}

    from threading import Lock
    from time import monotonic
    readiness_cache, readiness_lock = {}, Lock()
    @app.get('/readiness')
    def readiness():
        from app.core.config import ROOT
        from app.core.readiness import capabilities
        with readiness_lock:
            if monotonic()-readiness_cache.get('checked_at',-1000)>30:
                readiness_cache.update(result=capabilities(ROOT,app.state.copilot,app.state.federation),checked_at=monotonic())
            result = readiness_cache['result']
        return JSONResponse(status_code=200 if result['status']=='ready' else 503,content=result)
    return app


app = create_app()
