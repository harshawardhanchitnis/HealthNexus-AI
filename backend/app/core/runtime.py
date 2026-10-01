"""Explicit infrastructure policy; independent of provider or deployment hostname."""
import os

MAX_COMPUTE_FACILITIES = 12
SCENARIO_LIMIT = 2
PLAN_LIMIT = 3  # district, cross-district and constrained demos can coexist


class ComputeScopeError(ValueError):
    """Explicit deployment limit, not missing artifacts or a provider outage."""


def compute_scope(facilities, *, cross_district=False):
    if not low_memory():
        return
    districts = {f.district_id for f in facilities}
    states = {f.state_id for f in facilities}
    if (not facilities or None in districts or len(states) != 1 or
            len(districts) > (2 if cross_district else 1) or
            len(facilities) > MAX_COMPUTE_FACILITIES):
        raise ComputeScopeError('Select one district for live forecasts, warnings and simulations. '
            'The public demo supports district planning and cross-district planning within one state '
            '(at most two districts and 12 facilities). Nationwide browsing and the network map remain available.')


def planning_scope(request):
    if low_memory() and (not request.district_id or request.scope not in ('district', 'cross_district')):
        raise ComputeScopeError('Select a receiver district and District or Cross-District donor scope. '
            'Live state and national planning are disabled on the public demo; nationwide browsing remains available.')


def capabilities():
    return {'district_computation_only': low_memory(), 'maximum_compute_facilities': MAX_COMPUTE_FACILITIES if low_memory() else None,
            'planning_scopes': ['district', 'cross_district'] if low_memory() else ['district', 'cross_district', 'state', 'national'],
            'national_network_available': True, 'national_live_warnings': not low_memory(),
            'maximum_active_scenarios': SCENARIO_LIMIT if low_memory() else None,
            'maximum_active_plans': PLAN_LIMIT if low_memory() else None}


def low_memory():
    return os.getenv('HEALTHNEXUS_LOW_MEMORY', 'false').lower() == 'true'


def operational_country(country):
    if low_memory() and country != 'IN':
        raise ValueError('This public deployment is India-operational-only; foreign nodes are saved federation evidence only.')
