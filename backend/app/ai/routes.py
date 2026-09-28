from fastapi import APIRouter, Request, HTTPException, Response
from app.models.provenance import CountryCode
from app.profiles.config import ProfileID
from app.profiles.access import selected_profile
from app.ai.schemas import CopilotRequest, CopilotResponse
from app.ai.client import CopilotError


def copilot_router(service):
    router=APIRouter(prefix='/api/ai',tags=['resilience-copilot'])
    def safe(action):
        try: return action()
        except CopilotError as error:
            raise HTTPException(error.status,{'code':error.code,'message':error.message}) from None
        except (ValueError,LookupError):
            raise HTTPException(422,{'code':'context_invalid','message':'Selected geography, profile or saved result is invalid or stale.'}) from None
        except Exception:
            raise HTTPException(503,{'code':'copilot_unavailable','message':'Copilot unavailable. Check trusted artifacts and server configuration.'}) from None

    @router.get('/status')
    def status(): return service.status()

    @router.post('/copilot',response_model=CopilotResponse)
    def copilot(body:CopilotRequest,request:Request):
        if 'profile' in request.query_params and selected_profile(request)!=body.profile:
            raise HTTPException(422,{'code':'profile_mismatch','message':'Body and query profile disagree.'})
        request.state.operational_profile=body.profile
        return safe(lambda:service.run(request.app.state.repository,body))

    @router.get('/requests/{request_id}')
    def progress(request_id:str,country_id:CountryCode='IN',profile:ProfileID='constrained'):
        try: return service.progress(request_id,country_id,profile)
        except LookupError: raise HTTPException(404,'Copilot request not found') from None

    @router.delete('/conversations/{conversation_id}',status_code=204)
    def discard(conversation_id:str,country_id:CountryCode='IN',profile:ProfileID='constrained'):
        safe(lambda:service.discard(conversation_id,country_id,profile))
        return Response(status_code=204)
    return router
