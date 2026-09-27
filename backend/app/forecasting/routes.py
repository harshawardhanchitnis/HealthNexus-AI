import logging
from fastapi import APIRouter, HTTPException, Request, Query
from app.models.provenance import CountryCode
from app.forecasting.prediction import ForecastService, ModelUnavailable
from app.forecasting.schemas import ForecastResponse, StockRisksResponse, PerformanceReport


def forecast_router(service: ForecastService | None = None):
    router = APIRouter()
    forecasts = service or ForecastService()

    def run(request, country, facility, target, resource, horizon):
        if horizon not in (1, 7, 14):
            raise HTTPException(422, "Horizon must be 1, 7 or 14")
        try:
            repo = request.app.state.repository
            snapshot = repo.snapshot() if country == "IN" else repo.country_snapshot(country)
            return forecasts.predict(snapshot, facility, target, resource, horizon)
        except LookupError as exc:
            raise HTTPException(404, str(exc))
        except ModelUnavailable as exc:
            raise HTTPException(503, str(exc))
        except Exception:
            logging.exception("Forecast unavailable")
            raise HTTPException(503, "Forecast data is unavailable. Check the snapshot and trusted local model artifacts.")

    @router.get("/api/forecasts/facilities/{facility_id}/footfall", response_model=ForecastResponse)
    def footfall(request: Request, facility_id: str, country_id: CountryCode = "IN", horizon: int = Query(14, ge=1, le=14)):
        return run(request, country_id, facility_id, "footfall", "footfall", horizon)

    @router.get("/api/forecasts/facilities/{facility_id}/medicines/{medicine_id}", response_model=ForecastResponse)
    def medicine(request: Request, facility_id: str, medicine_id: str, country_id: CountryCode = "IN", horizon: int = Query(14, ge=1, le=14)):
        return run(request, country_id, facility_id, "medicine", medicine_id, horizon)

    @router.get("/api/forecasts/facilities/{facility_id}/beds", response_model=ForecastResponse)
    def beds(request: Request, facility_id: str, country_id: CountryCode = "IN", horizon: int = Query(14, ge=1, le=14)):
        return run(request, country_id, facility_id, "admissions", "admissions", horizon)

    @router.get("/api/forecasts/facilities/{facility_id}/stockout-risks", response_model=StockRisksResponse)
    def stockout(request: Request, facility_id: str, country_id: CountryCode = "IN"):
        first = run(request, country_id, facility_id, "medicine", "PCM", 14)
        items = [first] + [run(request, country_id, facility_id, "medicine", code, 14) for code in ("IVF", "ORS", "AMX", "IFA")]
        return {"country_id": country_id, "facility_id": facility_id, "as_of": first.as_of, "items": items}

    @router.get("/api/models/forecasting/metrics", response_model=PerformanceReport)
    def model_metrics(country_id: CountryCode = "IN"):
        try:
            return forecasts.bundle(country_id)["report"]
        except ModelUnavailable as exc:
            raise HTTPException(503, str(exc))
        except Exception:
            logging.exception("Model report unavailable")
            raise HTTPException(503, "Model report is unavailable. Rebuild trusted local artifacts.")
    return router
