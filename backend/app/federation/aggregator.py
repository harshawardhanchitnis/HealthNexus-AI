"""No data loader, client, training array or target dependency at this boundary."""
import numpy as np
from app.federation.config import COUNTRIES
from app.federation.schemas import ClientUpdate
from app.federation.parameters import validate_update


def aggregate(updates: list[ClientUpdate], round_number: int, starting_checksum: str,
              policy='sample-weighted', expected_countries=COUNTRIES):
    if policy not in ('sample-weighted','balanced-country'): raise ValueError('Unknown policy')
    if not updates or any(not isinstance(u,ClientUpdate) for u in updates):
        raise ValueError('Aggregator accepts typed model updates only')
    ids = [u.country_id for u in updates]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_countries): raise ValueError('Country participants mismatch')
    arrays = [validate_update(u,round_number,starting_checksum) for u in updates]
    total = sum(u.sample_count for u in updates)
    weights = {u.country_id: u.sample_count/total if policy=='sample-weighted' else 1/len(updates) for u in updates}
    result = {name: sum((a[name].astype(np.float64)*weights[u.country_id] for a,u in zip(arrays,updates)),
        np.zeros_like(arrays[0][name],dtype=np.float64)).astype(np.float32) for name in arrays[0]}
    if any(not np.isfinite(v).all() for v in result.values()): raise ValueError('Non-finite aggregate')
    return result, weights
