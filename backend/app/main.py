import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.models.network import Snapshot, Status
from app.services.repository import NetworkRepository, create_repository
from app.services.summary import aggregate_history, summarize


def create_app(repository: NetworkRepository | None = None) -> FastAPI:
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repository = repository or create_repository(settings)
        yield

    app = FastAPI(title="HealthNexus AI · India", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
        allow_credentials=False, allow_methods=["GET"], allow_headers=["Content-Type"])

    def dataset(request: Request) -> Snapshot:
        try:
            return request.app.state.repository.snapshot()
        except Exception:
            logging.exception("Unable to read healthcare network")
            raise HTTPException(status_code=503, detail="Network data is unavailable. Check backend storage configuration.")

    def filtered(data: Snapshot, state_id: str | None, district_id: str | None):
        if state_id and not any(r.id == state_id for r in data.regions):
            raise HTTPException(404, "State or union territory not found")
        if district_id and not any(d.id == district_id and (not state_id or d.state_id == state_id) for d in data.districts):
            raise HTTPException(404, "District not found in selected scope")
        return [f for f in data.facilities if (not state_id or f.state_id == state_id) and (not district_id or f.district_id == district_id)]

    @app.get("/api/health")
    def health(request: Request, data: Snapshot = Depends(dataset)):
        return {"status": "ok", "service": "HealthNexus AI", "country": "IN",
            "storage": request.app.state.repository.mode, "synthetic": True, "as_of": data.as_of}

    @app.get("/api/regions")
    def regions(data: Snapshot = Depends(dataset)):
        return {"country": "IN", "regions": data.regions, "districts": data.districts}

    @app.get("/api/overview")
    def overview(state_id: str | None = None, district_id: str | None = None, data: Snapshot = Depends(dataset)):
        facilities = filtered(data, state_id, district_id)
        ids = {f.id for f in facilities}
        alerts = [a for a in data.alerts if a.facility_id in ids]
        return {"as_of": data.as_of, "synthetic": True, "scope": {"state_id": state_id, "district_id": district_id},
            "summary": {**summarize(facilities), "active_alerts": len(alerts)},
            "history": aggregate_history(facilities), "alerts": alerts[:6],
            "regions": [{**r.model_dump(), **summarize([f for f in facilities if f.state_id == r.id])}
                for r in data.regions if not state_id or r.id == state_id],
            "coverage": {"states": sum(r.kind == "state" for r in data.regions),
                "union_territories": sum(r.kind == "union_territory" for r in data.regions),
                "sample_districts": len(data.districts),
                "notice": "Synthetic sample facilities across all states and union territories. District coverage is illustrative, not a complete national facility registry."}}

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
        return {"facility": result, "alerts": [a for a in data.alerts if a.facility_id == facility_id], "as_of": data.as_of}

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

    return app


app = create_app()

