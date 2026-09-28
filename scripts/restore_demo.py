"""Restore a trusted local demo bundle after validating paths and every checksum."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);args=parser.parse_args()
    with zipfile.ZipFile(args.bundle) as archive:
        manifest=json.loads(archive.read('demo-assets-manifest.json'))
        names=archive.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(manifest)|{'demo-assets-manifest.json'}:
            raise SystemExit('Invalid demo bundle file manifest')
        for name,expected in manifest.items():
            path=PurePosixPath(name)
            target=(ROOT/str(path)).resolve()
            if path.is_absolute() or '..' in path.parts or not target.is_relative_to(ROOT.resolve()) or not name.startswith(('data/generated/','artifacts/models/','artifacts/planning/')):
                raise SystemExit('Unsafe archive path')
            content=archive.read(name)
            if hashlib.sha256(content).hexdigest()!=expected:raise SystemExit('Demo bundle checksum mismatch')
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
                raise SystemExit('Existing asset differs. Refusing to overwrite measured data: '+name)
        restored=0
        for name in manifest:
            target=ROOT/name
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_suffix(target.suffix+'.tmp')
                temp.write_bytes(archive.read(name));temp.replace(target);restored+=1
    print(f'PASS · {restored} missing assets restored; existing measured data preserved. Run scripts/prepare_demo.py next.')
