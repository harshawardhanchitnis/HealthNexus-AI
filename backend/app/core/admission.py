"""One operational request through response serialization; no waiting work queue.

ASGI response lifetime matters: releasing at response headers would let the next
request overlap serialization/body buffers. Status and progress remain responsive.
"""
from starlette.responses import JSONResponse
from app.core.runtime import low_memory
from app.core.allocator import release_transient_memory


def operational_request(scope):
    path = scope.get('path', '')
    if scope.get('method') == 'OPTIONS' or not path.startswith('/api/'):
        return False
    if path in ('/api/countries', '/api/operational-profiles', '/api/scenarios/presets', '/api/ai/status'):
        return False
    # Small navigation metadata must remain usable during a long Copilot call.
    # The repository already serializes first profile loading; scenario metadata
    # is bounded by the two-handle store. Neither endpoint predicts or clones paths.
    if scope.get('method') == 'GET' and path in ('/api/regions', '/api/scenarios'):
        return False
    return not path.startswith('/api/ai/requests/')


class OperationalAdmission:
    def __init__(self, app):
        self.app, self.busy = app, False

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not low_memory() or not operational_request(scope):
            return await self.app(scope, receive, send)
        # Check and set contain no await: atomic on this worker's event loop.
        if self.busy:
            response = JSONResponse(status_code=429, headers={'Retry-After': '2'}, content={'detail': {
                'code': 'operational_busy', 'message': 'An operational calculation is active. Retry shortly; your request has not started.'}})
            return await response(scope, receive, send)
        self.busy = True
        try:
            if scope.get('method') == 'POST':
                chunks, size = [], 0
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    size += len(chunk)
                    if size > 32768:
                        response = JSONResponse(status_code=413, content={'detail':'Operational requests must be at most 32 KiB.'})
                        return await response(scope, receive, send)
                    chunks.append(chunk)
                    if not message.get('more_body', False):break
                body = b''.join(chunks)
                received = False
                original_receive = receive
                async def bounded_receive():
                    nonlocal received
                    if not received:
                        received = True
                        return {'type':'http.request','body':body,'more_body':False}
                    return await original_receive()
                receive = bounded_receive
            await self.app(scope, receive, send)
        finally:
            try:
                release_transient_memory()
            finally:
                self.busy = False
