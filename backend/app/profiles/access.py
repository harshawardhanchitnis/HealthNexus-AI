from fastapi import HTTPException
from app.profiles.config import NOTICES


def selected_profile(request):
    profile = request.query_params.get('profile','constrained')
    if profile not in NOTICES:
        raise HTTPException(422,'Unsupported operational profile')
    return profile


def snapshot_for(request, country, profile=None):
    selected = selected_profile(request)
    if profile is not None and 'profile' in request.query_params and profile != selected:
        raise ValueError('Request body and query operational profiles disagree')
    profile = profile or selected
    request.state.operational_profile = profile
    repo = request.app.state.repository
    if hasattr(repo,'profile_snapshot'):
        return repo.profile_snapshot(country,profile)
    if profile != 'constrained':
        raise ValueError('Operational profile is unavailable in this repository')
    return repo.snapshot() if country == 'IN' else repo.country_snapshot(country)
