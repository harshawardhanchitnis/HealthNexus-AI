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
        return CopilotError('rate_limited', 'Gemini rate limit or quota reached. Retry later or select offline mode.', 429)
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
        # Disable SDK retries; the application permits one retry for 502/503 only.
        self.client = genai.Client(api_key=config.api_key, http_options=types.HttpOptions(
            timeout=int(config.timeout*1000), retry_options=types.HttpRetryOptions(attempts=1)))

    def create(self, **body):
        for attempt in range(2):
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
                    'http_status':code if isinstance(code,int) else None,'transport_attempts':attempt+1}
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
