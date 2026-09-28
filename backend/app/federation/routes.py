from fastapi import APIRouter, HTTPException, Response
from app.federation.schemas import RunRequest


def federation_router(service):
    router = APIRouter(prefix='/api/federation',tags=['experimental federation'])

    @router.get('/status')
    def status():return service.status()

    @router.get('/nodes')
    def nodes():return {'items':service.nodes()}

    @router.get('/saved-demo')
    def saved():
        try:return service.saved()
        except (OSError,ValueError,KeyError):raise HTTPException(503,'Saved federation evidence is unavailable or incompatible. Run scripts/prepare_demo.py.')

    @router.post('/runs',status_code=202)
    def start(request:RunRequest):
        try:return service.start(request)
        except ValueError as error:raise HTTPException(409,str(error))

    @router.get('/runs/{run_id}')
    def get(run_id:str):
        try:return service.store.get(run_id)
        except KeyError:raise HTTPException(404,'Federation run not found')

    @router.get('/runs/{run_id}/rounds')
    def rounds(run_id:str):return {'items':get(run_id)['rounds']}

    @router.delete('/runs/{run_id}',status_code=204)
    def delete(run_id:str):
        try:service.store.delete(run_id)
        except KeyError:raise HTTPException(404,'Federation run not found')
        except ValueError as error:raise HTTPException(409,str(error))
        return Response(status_code=204)
    return router
