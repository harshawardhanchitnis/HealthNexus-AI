"""Create a portable, checksummed local demo asset bundle, without credentials or retraining."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    output=ROOT/'artifacts/demo-assets.zip'
    files=[p for folder in ('data/generated','artifacts/models','artifacts/planning') for p in (ROOT/folder).rglob('*') if p.is_file()]
    if not files:raise SystemExit('Missing canonical assets. See docs/deployment.md for fresh-clone bootstrap.')
    checksums={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in files:archive.write(p,p.relative_to(ROOT).as_posix())
        archive.writestr('demo-assets-manifest.json',json.dumps(checksums,indent=2))
    print(json.dumps({'bundle':'artifacts/demo-assets.zip','files':len(files),'bytes':output.stat().st_size,
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'contains_credentials':False},indent=2))
