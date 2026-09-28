"""Explicit reusable baseline preparation; never trains or changes source data."""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.services.repository import LocalRepository
from app.scenarios.engine import ScenarioEngine
from app.profiles.preparation import save

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['constrained','redistribution-ready'],required=True)
    parser.add_argument('--country',choices=['IN','BR','RU','CN','ZA','all'],default='IN')
    args=parser.parse_args()
    repo=LocalRepository();engine=ScenarioEngine()
    for country in (['IN','BR','RU','CN','ZA'] if args.country=='all' else [args.country]):
        start=perf_counter();report=save(engine,repo.profile_snapshot(country,args.profile))
        print(json.dumps({**report,'country':country,'profile':args.profile,'seconds':perf_counter()-start}),flush=True)
