"""Prepare named inventory profiles without replacing original demand data or model weights."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.profiles.generation import generate_profile

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=['constrained','redistribution-ready'],required=True)
    p.add_argument('--country',choices=['all','IN','BR','RU','CN','ZA'],default='all')
    a=p.parse_args()
    for c in ['IN','BR','RU','CN','ZA'] if a.country=='all' else [a.country]:
        result=generate_profile(c,a.profile)
        print(json.dumps({k:result[k] for k in ('country','profile','seed','snapshot_sha256','weights_retrained')}),flush=True)
