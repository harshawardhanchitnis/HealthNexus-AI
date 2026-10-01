"""Low-memory artifact capability checks; no prediction, unpickling or training."""
import json
from pathlib import Path
import zipfile
from app.core.artifact_io import artifact_sha256


def sha256(path):
    return artifact_sha256(path)


def india_artifacts(root):
    from app.profiles.config import VERSION, folder
    import sklearn
    path = root/'artifacts/deployment-integrity.json'
    if path.exists():
        manifest = json.loads(path.read_text())
    else:
        bundle = root/'deployment-assets/demo-assets.zip'
        if sha256(bundle) != '966f452b95d7bacff92ccfdbb0fce8ba1beb4593ad0bcb8064d6c0d03397f7dd':
            raise ValueError('Deployment bundle integrity mismatch')
        with zipfile.ZipFile(bundle) as archive:
            manifest = json.loads(archive.read('demo-assets-manifest.json'))
    names = [name for name in manifest if name.startswith(('artifacts/models/IN/', 'data/generated/training/IN/'))
             or name in ('data/generated/network.json','data/generated/history/IN.json.gz')
             or any(name.startswith(f'data/generated/profiles/{p}/IN/') or name == f'artifacts/planning/{p}/IN.json.gz'
                    for p in ('constrained','redistribution-ready'))]
    if not names or any(sha256(root/name) != manifest[name] for name in names):
        raise ValueError('India asset integrity mismatch')
    model = json.loads((root/'artifacts/models/IN/integrity.json').read_text())
    if model['sklearn_version'] != sklearn.__version__:
        raise ValueError('Incompatible forecasting runtime')
    report = json.loads((root/'artifacts/models/IN/metrics.json').read_text())
    source = json.loads((root/'data/generated/training/IN/manifest.json').read_text())
    for profile in ('constrained','redistribution-ready'):
        meta = json.loads((folder(profile,'IN',root)/'compatibility.json').read_text())
        expected = dict(country='IN',profile=profile,profile_version=VERSION,as_of=source['as_of'],
                        model_version=report['model_version'],model_sha256=model['sha256'],
                        source_history_sha256=source['history_sha256'])
        if any(meta.get(key) != value for key,value in expected.items()):
            raise ValueError('India profile compatibility mismatch')
        if not (root/f'artifacts/planning/{profile}/IN.json.gz').is_file():
            raise ValueError('Canonical planning artifact missing')
    return {f'{p}:IN':True for p in ('constrained','redistribution-ready')}
