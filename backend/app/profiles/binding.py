"""Validated inventory-only binding to unchanged, trusted local demand models."""
import json
from app.forecasting.data import digest
from app.profiles.config import folder, legacy_snapshot, VERSION


def bind_profile(base, country, profile, root, cache, model_identity):
    from app.forecasting.prediction import ModelUnavailable
    directory = folder(profile, country, root)
    paths = [directory/name for name in ('compatibility.json', 'network.json', 'history.json.gz')]
    paths += [legacy_snapshot(country, root), root/'data/generated/history'/f'{country}.json.gz']
    try:
        stamp = tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
        key = (country, profile, VERSION, model_identity, stamp)
        if key in cache:
            return cache[key]
        meta = json.loads(paths[0].read_text(encoding='utf-8'))
        expected = {'profile':profile, 'country':country, 'profile_version':VERSION,
            'as_of':base['manifest']['as_of'], 'model_version':base['report']['model_version'],
            'model_sha256':digest(root/'artifacts/models'/country/'bundle.joblib'),
            'snapshot_sha256':digest(paths[1]), 'history_sha256':digest(paths[2]),
            'source_snapshot_sha256':digest(paths[3]), 'source_history_sha256':digest(paths[4])}
        if any(meta.get(k) != v for k,v in expected.items()):
            raise ModelUnavailable('Operational profile artifacts are stale or incompatible. Regenerate this profile; no models are retrained automatically.')
        if meta['source_history_sha256'] != base['manifest']['history_sha256']:
            raise ModelUnavailable('Profile training-history mismatch')
        bound = {**base, 'manifest':{**base['manifest'], 'facility_hashes':meta['facility_hashes'],
            'operational_profile':profile, 'operational_history_sha256':meta['history_sha256'],
            'profile_snapshot_sha256':meta['snapshot_sha256']},
            'report':{**base['report'], 'operational_profile':profile, 'profile_version':VERSION}}
        for old in [k for k in cache if k[:2] == key[:2]]:
            del cache[old]
        cache[key] = bound
        return bound
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as error:
        raise ModelUnavailable(f'Profile {profile} is unavailable or incomplete. Run scripts/generate_data.py --profile {profile} --country {country}.') from error
