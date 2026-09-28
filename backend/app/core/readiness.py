"""Local capability checks. Never invokes a provider or trains a model."""
from pathlib import Path
from app.federation.config import PHASE6_STATUS
from app.forecasting.prediction import ForecastService
from app.services.repository import LocalRepository


def capabilities(root: Path, copilot, federation):
    checks = {}
    forecasts = ForecastService(root)
    repository = LocalRepository(root=root)
    for profile in ('constrained', 'redistribution-ready'):
        for country in ('IN', 'BR', 'RU', 'CN', 'ZA'):
            try:
                snapshot = repository.profile_snapshot(country, profile)
                forecasts.prepare_predictions(snapshot, [snapshot.facilities[0]])
                checks[f'{profile}:{country}'] = True
            except (OSError, ValueError, KeyError):
                checks[f'{profile}:{country}'] = False
    available = all(checks.values())
    try:
        federation.saved()
        saved = True
    except (OSError, ValueError, KeyError):
        saved = False
    status = copilot.status()
    return {'status': 'ready' if available and saved else 'degraded',
        'forecast_artifacts': checks, 'scenario_engine': available, 'optimizer': available,
        'federation_training': federation.status()['available'], 'federation_saved_run': saved,
        'storage': 'local/file assets; transient workflows are process-local',
        'gemini': {'configured': status['configured'], 'enabled': status['enabled'],
            'runtime_status': status['runtime_status'], 'acceptance_status': PHASE6_STATUS,
            'provider_probed': False, 'offline_available': True}}
