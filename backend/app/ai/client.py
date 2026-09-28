"""Official SDK transport. Model failures are never relabelled as success."""
from time import sleep
import httpx
from google import genai
from google.genai import types


class CopilotError(Exception):
    def __init__(self, code, message, status=503):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


def provider_error(error):
    code = getattr(error, 'code', None) or getattr(error, 'status_code', None)
    if code in (401,403):
        return CopilotError('authentication', 'Gemini authentication failed. Check server-side key permissions.')
    if code == 404:
        return CopilotError('model_unavailable', 'gemini-3.8-flash is unavailable for this API configuration. No substitute was selected.')
    if code == 429:
        detail = getattr(error, 'body', {})
        message = str(detail).lower()
        kind = 'RPD' if any(x in message for x in ('per day', 'perday', 'daily', 'requestsperday')) else 'TPM' if any(x in message for x in ('token', 'tokensperminute')) else 'RPM' if any(x in message for x in ('per minute', 'perminute', 'rpm')) else 'unknown'
        safe = CopilotError('rate_limited',
            'Gemini daily quota exhausted. Resume after the quota resets or select offline mode.' if kind == 'RPD'
            else 'Gemini rate limit reached. Retry later or select offline mode.', 429)
        safe.quota_kind = kind
        return safe
    cause=error
    timed_out=False
    for _ in range(5):
        if isinstance(cause,(httpx.TimeoutException,TimeoutError)):
            timed_out=True
            break
        cause=getattr(cause,'__cause__',None) or getattr(cause,'__context__',None)
        if cause is None:break
    if timed_out:
        return CopilotError('provider_timeout', 'Gemini timed out. Retry later or select offline mode.', 504)
    if code == 400:
        return CopilotError('provider_configuration', 'Gemini rejected the request configuration. Check model/API compatibility.')
    return CopilotError('provider_unavailable', 'Gemini is unavailable. Retry later or select offline mode.')


class GeminiTransport:
    def __init__(self, config):
        self.config = config
        self.provider_requests = 0
        self.before_request = None
        # Legacy retry options alone do not disable the Interactions bridge:
        # parent normalizes 0 to 1, then bridge interprets 1 as a retry count.
        self.client = genai.Client(api_key=config.api_key, http_options=types.HttpOptions(
            timeout=int(config.timeout*1000), retry_options=types.HttpRetryOptions(attempts=0)))

    def create(self, **body):
        # Pinned official SDK's generated resource supports nullable retry_config.
        # Set it on the actual Interactions resource, not just the parent client.
        # Fail before sending if a future incompatible SDK removes this surface.
        self.client.interactions.sdk_configuration.retry_config = None
        for attempt in range(2):
            # Outside the catch: a local budget denial must never become a provider failure.
            if self.before_request:
                self.before_request()
            self.provider_requests += 1
            try:
                response = self.client.interactions.create(**body, timeout=self.config.timeout)
                data = response.model_dump(mode='json', exclude_none=True)
                # SDK convenience property can be absent from the wire schema.
                data['output_text'] = getattr(response, 'output_text', None) or data.get('output_text', '')
                return data
            except Exception as error:
                code = getattr(error, 'code', None) or getattr(error, 'status_code', None)
                if attempt == 0 and code in (502,503):
                    sleep(.25)
                    continue
                safe=provider_error(error)
                safe.diagnostic={'exception_type':type(error).__name__,
                    'http_status':code if isinstance(code,int) else None,'transport_attempts':attempt+1,
                    'quota_kind':getattr(safe,'quota_kind',None)}
                headers = getattr(getattr(error,'response',None),'headers',{})
                retry_after = headers.get('retry-after') if headers else None
                if retry_after and len(str(retry_after)) < 80:
                    safe.diagnostic['retry_after'] = str(retry_after)
                body=getattr(error,'body',{})
                detail=body.get('error',body) if isinstance(body,dict) else {}
                if isinstance(detail,dict):
                    message=detail.get('message','')
                    if isinstance(message,str):
                        # Do not retain request objects, URLs, headers or raw exceptions.
                        message=message.replace(self.config.api_key,'[REDACTED]') if self.config.api_key else message
                        safe.diagnostic['provider_message']=message[:500]
                    for entry in detail.get('details',[]) if isinstance(detail.get('details'),list) else []:
                        if isinstance(entry,dict) and entry.get('@type','').endswith('RetryInfo'):
                            delay=entry.get('retryDelay')
                            if isinstance(delay,str) and len(delay)<40:
                                safe.diagnostic['retry_delay']=delay
                raise safe from None

    def close(self):
        self.client.close()
