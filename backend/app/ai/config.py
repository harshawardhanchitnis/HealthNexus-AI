import os
from dataclasses import dataclass, field

MODEL = 'gemini-3.8-flash'
DEFAULT_CHAIN = (MODEL, 'gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-3.5-flash-lite')
VERSION = 'copilot-config-v5-stage-generation'


@dataclass(frozen=True)
class AIConfig:
    api_key: str = field(default_factory=lambda: os.getenv('GEMINI_API_KEY', ''), repr=False)
    model: str = field(default_factory=lambda: os.getenv('GEMINI_MODEL_PRIMARY') or os.getenv('GEMINI_MODEL') or MODEL)
    fallbacks: tuple[str, ...] = field(default_factory=lambda: tuple(x.strip() for x in
        os.getenv('GEMINI_MODEL_FALLBACKS', ','.join(DEFAULT_CHAIN[1:])).split(',') if x.strip()))
    failover_enabled: bool = field(default_factory=lambda: os.getenv('GEMINI_FAILOVER_ENABLED', 'true').lower() == 'true')
    same_model_attempts: int = 2
    enabled: bool = field(default_factory=lambda: os.getenv('GEMINI_ENABLED', 'true').lower() == 'true')
    thinking: str = field(default_factory=lambda: os.getenv('GEMINI_THINKING_LEVEL', 'medium'))
    max_calls: int = 10
    timeout: float = 60
    workflow_timeout: float = 300
    max_output_tokens: int = 2400
    synthesis_thinking: str = field(default_factory=lambda: os.getenv('GEMINI_SYNTHESIS_THINKING_LEVEL', 'low'))
    synthesis_max_output_tokens: int = 4096

    def generation(self, synthesis=False):
        return {'thinking_level':self.synthesis_thinking if synthesis else self.thinking,
            'max_output_tokens':self.synthesis_max_output_tokens if synthesis else self.max_output_tokens}

    @property
    def chain(self):
        return (self.model,) + tuple(m for m in self.fallbacks if m != self.model) if self.failover_enabled else (self.model,)

    def error(self):
        if self.model not in DEFAULT_CHAIN or any(m not in DEFAULT_CHAIN for m in self.fallbacks) or len(set(self.fallbacks)) != len(self.fallbacks):
            return 'model_configuration', 'Configure only approved stable Gemini Flash-family models without duplicate fallbacks.'
        if self.thinking not in ('low', 'medium'):
            return 'thinking_configuration', 'GEMINI_THINKING_LEVEL must be low or medium.'
        if self.synthesis_thinking not in ('low', 'medium'):
            return 'thinking_configuration', 'GEMINI_SYNTHESIS_THINKING_LEVEL must be low or medium.'
        if not self.enabled:
            return 'disabled', 'Gemini is disabled. Select explicitly labelled offline mode.'
        if not self.api_key:
            return 'missing_key', 'Gemini API not configured. Set GEMINI_API_KEY on the backend or select offline mode.'
        return None
