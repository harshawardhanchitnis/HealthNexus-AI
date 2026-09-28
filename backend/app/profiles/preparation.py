"""Optional checked JSON baseline cache. Reading a cache never trains models."""
import gzip
import hashlib
import json
from pathlib import Path
from app.core.config import ROOT
from app.forecasting.schemas import ForecastResponse
from app.scenarios.models import FacilityProjection
from app.warnings.models import Warning
from app.profiles.identity import fingerprint

FORMAT = 'planning-baseline-v1'

def calculation_version():
    base = Path(__file__).resolve().parents[1]
    files = ['forecasting/prediction.py','forecasting/features.py','forecasting/stockout.py','forecasting/evaluation.py',
        'scenarios/effects.py','scenarios/engine.py','warnings/engine.py','core/risk_config.py',
        'forecasting/schemas.py','scenarios/models.py','warnings/models.py','profiles/preparation.py',
        'profiles/config.py','profiles/binding.py','profiles/identity.py','core/diagnostics.py']
    return hashlib.sha256(b''.join((base/f).read_bytes() for f in files)).hexdigest()

def identity(snapshot, bundle):
    return {'format':FORMAT, 'snapshot':fingerprint(snapshot,snapshot.facilities),
        'country':snapshot.country,'profile':snapshot.operational_profile,'origin':str(snapshot.as_of),
        'model':bundle['report']['model_version'], 'model_sha256':bundle.get('artifact_sha256'),
        'calculation_version':calculation_version()}

def cache_path(snapshot, root=ROOT):
    return root/'artifacts/planning'/snapshot.operational_profile/f'{snapshot.country}.json.gz'

def save(engine, snapshot):
    bundle = engine.forecasts.bundle(snapshot.country,snapshot.operational_profile)
    rows = {}
    for f in snapshot.facilities:
        engine.baseline(snapshot,[f])
        key = engine.key(snapshot,f,bundle)
        projection,warnings = engine.baseline_cache[key]
        rows[f.id] = {'forecasts':{k:v.model_dump(mode='json') for k,v in engine.cache[key].items()},
            'projection':projection.model_dump(mode='json'), 'warnings':[w.model_dump(mode='json') for w in warnings]}
    payload = json.dumps(rows,sort_keys=True,separators=(',',':'))
    envelope = {'identity':identity(snapshot,bundle),'sha256':hashlib.sha256(payload.encode()).hexdigest(),'payload':payload}
    path = cache_path(snapshot,engine.forecasts.root)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_bytes(gzip.compress(json.dumps(envelope).encode(),mtime=0))
    temp.replace(path)
    return {'path':str(path),'disk_bytes':path.stat().st_size,'uncompressed_payload_bytes':len(payload.encode()),'facilities':len(rows)}

def restore(engine, snapshot, bundle):
    path = cache_path(snapshot,engine.forecasts.root)
    if not path.exists():
        return False
    try:
        envelope = json.loads(gzip.decompress(path.read_bytes()))
        payload = envelope['payload']
        if envelope['identity'] != identity(snapshot,bundle) or hashlib.sha256(payload.encode()).hexdigest() != envelope['sha256']:
            return False
        rows = json.loads(payload)
        if set(rows) != {f.id for f in snapshot.facilities}:
            return False
        forecasts, baselines = {}, {}
        for f in snapshot.facilities:
            row=rows[f.id]; key=engine.key(snapshot,f,bundle)
            forecasts[key] = {k:ForecastResponse.model_validate(v) for k,v in row['forecasts'].items()}
            projection=FacilityProjection.model_validate(row['projection'])
            if projection.facility_id != f.id or projection.provenance.operational_profile != snapshot.operational_profile:
                return False
            baselines[key]=(projection,[Warning.model_validate(w) for w in row['warnings']])
        engine.cache.update(forecasts);engine.baseline_cache.update(baselines)
        return True
    except (OSError,ValueError,KeyError,TypeError):
        return False  # corrupt/stale optional caches miss; original artifacts still validate
