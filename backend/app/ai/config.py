import os
from dataclasses import dataclass, field

MODEL = 'gemini-3.8-flash'
VERSION = 'copilot-config-v2'


@dataclass(frozen=True)
class AIConfig:
    api_key: str = field(default_factory=lambda: os.getenv('GEMINI_API_KEY', ''), repr=False)
    model: str = field(default_factory=lambda: os.getenv('GEMINI_MODEL') or MODEL)
    enabled: bool = field(default_factory=lambda: os.getenv('GEMINI_ENABLED', 'true').lower() == 'true')
    thinking: str = field(default_factory=lambda: os.getenv('GEMINI_THINKING_LEVEL', 'medium'))
    max_calls: int = 10
    timeout: float = 25
    workflow_timeout: float = 120
    max_output_tokens: int = 2400

    def error(self):
        if self.model != MODEL:
            return 'model_configuration', f'This integration requires exactly {MODEL}; no substitute is selected.'
        if self.thinking not in ('low', 'medium'):
            return 'thinking_configuration', 'GEMINI_THINKING_LEVEL must be low or medium.'
        if not self.enabled:
            return 'disabled', 'Gemini is disabled. Select explicitly labelled offline mode.'
        if not self.api_key:
            return 'missing_key', 'Gemini API not configured. Set GEMINI_API_KEY on the backend or select offline mode.'
        return None
