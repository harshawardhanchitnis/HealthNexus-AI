"""Reproducible separate FedAvg prototype. Never calls Gemini or retrains HGB."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.federation.schemas import RunRequest
from app.federation.service import FederationService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','run','evaluate','report'])
    parser.add_argument('--rounds',type=int,default=5);parser.add_argument('--local-epochs',type=int,default=1)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--policy',choices=['sample-weighted','balanced-country'],default='sample-weighted')
    parser.add_argument('--report',type=Path);parser.add_argument('--output',type=Path)
    args = parser.parse_args();service = FederationService()
    try:
        if args.command=='prepare':
            result = {'model':service.status(),'nodes':service.nodes()}
            if any(n['status']!='ready' for n in result['nodes']):raise ValueError('Prepare existing country-local Phase 3 tables first')
        elif args.command=='run':
            request = RunRequest(rounds=args.rounds,local_epochs=args.local_epochs,seed=args.seed,policy=args.policy)
            result = service.start(request,background=False)
            if result['status']!='completed':raise ValueError(result['message'])
        else:
            if not args.report:parser.error('--report is required for evaluate/report')
            result = json.loads(args.report.read_text(encoding='utf-8'))
            if args.command=='evaluate':
                import numpy as np
                from app.federation.artifacts import load_model
                from app.federation.client import FederatedClient
                from app.federation.parameters import checksum
                folder = ROOT/'artifacts/federation/runs'/result['run_id']/'global/final'
                parameters = load_model(folder)
                if checksum(parameters)!=result['final_checksum']:raise ValueError('Report/model mismatch')
                evaluated = {}
                for node in result['nodes']:
                    client = FederatedClient(node['country_id'],ROOT,result['config']['seed'])
                    if client.describe()['table_sha256']!=node['table_sha256']:raise ValueError('Evaluation data changed')
                    client.set_parameters(parameters);metric = client.evaluate('test').model_dump()
                    if any(not np.isclose(v,node['federated_global'][k],rtol=1e-6,atol=1e-8)
                        for k,v in metric.items() if v is not None):raise ValueError('Saved model evaluation differs')
                    evaluated[node['country_id']] = metric
                result = {'status':'passed','run_id':result['run_id'],'reload_evaluation':evaluated,
                    'floating_point_tolerance':{'rtol':1e-6,'atol':1e-8}}
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
        print(json.dumps(result if args.command!='run' else {k:result[k] for k in ('run_id','status','training_seconds','bytes_exchanged','raw_records_shared','global_test')},indent=2))
    finally:service.close()


if __name__=='__main__':main()
