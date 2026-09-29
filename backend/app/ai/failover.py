"""Availability failover only. Local state/evidence never depends on provider memory."""
from copy import deepcopy
from dataclasses import replace
from time import perf_counter, monotonic
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.ai.client import CopilotError, GeminiTransport


def fallback_reason(error):
    d = getattr(error, 'diagnostic', {})
    status = d.get('http_status')
    if error.code == 'provider_timeout':
        return 'provider_timeout'
    if error.code == 'provider_unavailable' and status == 503:
        return 'high_demand' if any(s in d.get('provider_message', '').lower() for s in ('high demand', 'overload')) else 'service_unavailable'
    if error.code == 'rate_limited' and d.get('model_specific_quota') and d.get('quota_kind') in ('RPM', 'TPM', 'RPD'):
        return 'model_quota_' + d['quota_kind'].lower()
    if error.code == 'model_unavailable' and d.get('model_endpoint_unavailable'):
        return 'model_endpoint_unavailable'
    return None


def quota_cooldown(attempt):
    """Conservative process-local circuit; never claims remaining Google quota."""
    if not str(attempt.get('fallback_reason','')).startswith('model_quota_'):
        return 0
    if attempt.get('quota_kind') == 'RPD':
        try:
            now=datetime.now(ZoneInfo('America/Los_Angeles'))
            reset=datetime.combine(now.date()+timedelta(days=1),datetime.min.time(),now.tzinfo)
            return (reset.astimezone(timezone.utc)-now.astimezone(timezone.utc)).total_seconds()
        except ZoneInfoNotFoundError:
            return 86400
    for field in ('retry_after','retry_delay'):
        try:return max(60,float(str(attempt.get(field,'')).rstrip('s')))
        except ValueError:pass
    return 60


class FailoverSession:
    def __init__(self, config, factory, handoff, sticky=None, unsuitable=(), deadline=None, notify=None, sticky_reason=None, quota_blocked=()):
        self.config, self.handoff, self.notify = config, handoff, notify
        self.skipped=[{'model':m,'reason':'UNSUITABLE_FOR_HEALTHNEXUS' if m in unsuitable else 'known_model_quota_exhausted'}
            for m in config.chain if m in unsuitable or m in quota_blocked]
        self.chain = tuple(m for m in config.chain if m not in unsuitable and m not in quota_blocked)
        if sticky in self.chain:
            self.chain = self.chain[self.chain.index(sticky):]
        if not self.chain:
            if quota_blocked:
                raise CopilotError('provider_unavailable_all_models','Gemini temporarily unavailable. Configured model quotas are cooling down; deterministic operational tools remain available.')
            raise CopilotError('model_unsuitable', 'Configured models are unsuitable for HealthNexus grounding; inspect quality diagnostics.')
        self.effective_model = self.chain[0]
        self.last_successful_model = None
        self.factory = factory
        # One bounded attempt per model when failover is enabled. Never hammer an overloaded model.
        self.transport = factory(replace(config, model=self.effective_model,
            same_model_attempts=1 if config.failover_enabled else config.same_model_attempts))
        self.official = isinstance(self.transport, GeminiTransport)
        self.provider_requests = 0
        self.attempts, self.handoffs, self.attempted = [], [], []
        self.per_model = {}
        self.deadline = deadline
        self.last_reason = sticky_reason if sticky and sticky != config.model else None
        if self.effective_model != config.model and not self.last_reason and self.skipped:
            self.last_reason = self.skipped[0]['reason']

    def create(self, **original):
        body = deepcopy(original)
        while True:
            if self.deadline and monotonic() >= self.deadline:
                raise CopilotError('workflow_timeout', 'Copilot workflow time limit reached.', 504)
            model = self.effective_model
            body['model'] = model
            body['generation_config'] = {**body.get('generation_config', {}),
                **self.config.generation(synthesis='response_format' in body)}
            counts = self.per_model.setdefault(model, {'provider_requests':0, 'successful_interactions':0,
                'failed_attempts':0, 'provider_seconds':0.})
            before = getattr(self.transport, 'provider_requests', None)
            began = perf_counter()
            failure = None
            try:
                response = self.transport.create(**body)
            except CopilotError as error:
                failure = error
            finally:
                sent = self.transport.provider_requests-before if before is not None else 1
                elapsed = perf_counter()-began
                self.provider_requests += sent
                if sent and model not in self.attempted:
                    self.attempted.append(model)
                counts['provider_requests'] += sent
                counts['provider_seconds'] += elapsed
            if failure is None:
                if response.get('model') and response['model'] != model:
                    raise CopilotError('response_model', 'Provider response model differs from the requested model; no answer accepted.')
                counts['successful_interactions'] += 1
                self.last_successful_model = model
                counts['failed_attempts'] += max(0, sent-1)
                self.attempts.append({'model':model, 'status':'connected', 'provider_requests':sent, 'seconds':elapsed})
                if self.notify: self.notify(self.metadata())
                return response
            counts['failed_attempts'] += sent
            reason = fallback_reason(failure)
            self.attempts.append({'model':model, 'status':failure.code, 'provider_requests':sent,
                'seconds':elapsed, **getattr(failure, 'diagnostic', {}), 'fallback_reason':reason})
            if self.notify: self.notify(self.metadata())
            if not reason or not self.config.failover_enabled:
                raise failure
            self.last_reason = reason
            index = self.chain.index(model)+1
            if index >= len(self.chain):
                error = CopilotError('provider_unavailable_all_models',
                    'Gemini temporarily unavailable. HealthNexus deterministic operational tools remain available. Offline mode can be selected explicitly.')
                error.diagnostic = getattr(failure, 'diagnostic', {})
                raise error
            target = self.chain[index]
            # Never send foreign function-result call IDs or previous interaction IDs to a new model.
            body.pop('previous_interaction_id', None)
            body['input'] = self.handoff()
            self.handoffs.append({'handoff_from_model':model, 'handoff_to_model':target, 'handoff_reason':reason})
            self.transport.close()
            self.effective_model = target
            self.transport = self.factory(replace(self.config, model=target, same_model_attempts=1))

    def metadata(self):
        return {'requested_model':self.config.model, 'effective_model':self.last_successful_model,
            'selected_model':self.effective_model,
            'fallback_used':self.effective_model != self.config.model,
            'fallback_chain_attempted':list(self.attempted), 'fallback_reason':self.last_reason,
            'model_attempts':deepcopy(self.attempts), 'model_handoffs':deepcopy(self.handoffs),
            'models_skipped':deepcopy(self.skipped),
            'provider_requests_per_model':deepcopy(self.per_model)}

    def close(self):
        self.transport.close()
