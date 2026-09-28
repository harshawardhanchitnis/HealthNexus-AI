from app.profiles.access import snapshot_for, selected_profile
from app.profiles.config import ProfileID
import logging
from fastapi import APIRouter, HTTPException, Request, Response
from app.models.provenance import CountryCode
from app.forecasting.prediction import ModelUnavailable
from app.optimization.config import POLICY, LIMITATIONS, Policy
from app.optimization.schemas import RedistributionRequest, Preview, PlanResult


def optimization_router(service):
    router = APIRouter(prefix="/api/optimization", tags=["redistribution"])

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
            logging.exception("Redistribution failed")
            raise HTTPException(503, "Redistribution unavailable; check saved models and operational snapshot")

    snapshot = snapshot_for

    @router.get("/config", response_model=Policy)
    def config():
        return POLICY

    @router.post("/preview", response_model=Preview)
    def preview(body: RedistributionRequest, request: Request):
        return safe(lambda: service.preview(snapshot(request, body.country_id, body.profile), body))

    @router.post("/redistribution", response_model=PlanResult, status_code=201)
    def run(body: RedistributionRequest, request: Request):
        return safe(lambda: service.run(snapshot(request, body.country_id, body.profile), body))

    @router.get("/runs/{run_id}", response_model=PlanResult)
    def get(run_id: str, country_id: CountryCode = "IN", profile: ProfileID = "constrained"):
        return safe(lambda: service.get(run_id, country_id, profile))

    @router.delete("/runs/{run_id}", status_code=204)
    def discard(run_id: str, country_id: CountryCode = "IN", profile: ProfileID = "constrained"):
        safe(lambda: service.discard(run_id, country_id, profile))
        return Response(status_code=204)

    return router
