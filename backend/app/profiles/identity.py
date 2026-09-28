import hashlib
from app.forecasting.data import facility_hash


def fingerprint(snapshot, facilities):
    parts = [snapshot.country, snapshot.operational_profile, snapshot.profile_version, str(snapshot.as_of)]
    parts.extend(facility_hash(f) for f in sorted(facilities, key=lambda f:f.id))
    return hashlib.sha256('|'.join(parts).encode()).hexdigest()
