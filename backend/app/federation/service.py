from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib.util import find_spec
import json
import logging
from threading import RLock
from uuid import uuid4
from app.core.config import ROOT
from app.federation.config import COUNTRIES, MODEL_VERSION, NOTICE, PARAMETER_COUNT, PHASE6_STATUS
from app.federation.schemas import RunRequest
from app.federation.storage import RunStore


def now():return datetime.now(timezone.utc).isoformat()


class FederationService:
    def __init__(self,root=ROOT,limit=8):
        self.root = root;self.store = RunStore(root,limit);self.lock = RLock()
        self.pool = ThreadPoolExecutor(max_workers=1,thread_name_prefix='federation')
        self.active = None

    def status(self):
        return {'implementation':'experimental_fedavg','available':find_spec('torch') is not None,'model_version':MODEL_VERSION,
            'target':'patient footfall, direct horizons 1–14 days','default_rounds':5,'default_local_epochs':1,
            'default_policy':'sample-weighted','parameter_count':PARAMETER_COUNT,'client_count':5,
            'raw_records_shared':0,'notice':NOTICE,'active_run_id':self.active,
            'differential_privacy':False,'secure_aggregation':False,'encrypted_transport':'not implemented; in-process prototype',
            'operational_model_replaced':False,'phase6_status':PHASE6_STATUS}

    def nodes(self):
        from app.federation.data import prepare_country
        result = []
        for country in COUNTRIES:
            try:
                summary = prepare_country(country,self.root)
                result.append({**summary,'status':'ready','raw_records_shared':0})
            except (OSError,ValueError,KeyError):result.append({'country_id':country,'status':'unavailable','raw_records_shared':0})
        return result

    def start(self,request:RunRequest,background=True):
        if not self.status()['available']:raise ValueError('Install backend/requirements-federation.txt for CPU training')
        with self.lock:
            if self.active is not None:raise ValueError('A federation run is already active')
            run_id = str(uuid4())
            run = {'run_id':run_id,'model_version':MODEL_VERSION,'policy':request.policy,'config':request.model_dump(),
                'status':'queued','created_at':now(),'completed_at':None,'client_count':5,'rounds':[],
                'nodes':[],'events':[],'current_round':0,'current_country':None,'stage':'queued','message':'Training queued',
                'raw_records_shared':0,'bytes_exchanged':0,'notice':NOTICE,'data_type':'calibrated simulated operations',
                'logical_prototype':True,'operational_model_replaced':False}
            self.store.create(run);self.active = run_id
        if background:self.pool.submit(self._execute,run_id,request)
        else:self._execute(run_id,request)
        return self.store.get(run_id)

    def _execute(self,run_id,request):
        try:
            from app.federation.training import run_training
            self.store.update(run_id,status='running')
            def progress(stage,round_number,country,message,**fields):
                row = self.store.get(run_id)
                event = {'timestamp':now(),'stage':stage,'round':round_number,'country_id':country,'message':message}
                self.store.update(run_id,stage=stage,current_round=round_number,current_country=country,message=message,
                    events=(row['events']+[event])[-160:],**fields)
            result = run_training(self.root,request,self.store.folder(run_id),progress)
            finished = {**result,'status':'completed','stage':'completed','message':'Federated training completed',
                'current_country':None,'completed_at':now()}
            output = self.store.folder(run_id)/'report.json'
            # Persist before publishing terminal state, so DELETE cannot race report writing.
            output.write_text(json.dumps({**self.store.get(run_id),**finished},indent=2,allow_nan=False),encoding='utf-8')
            self.store.update(run_id,**finished)
        except Exception:
            logging.exception('Federation run failed')
            self.store.update(run_id,status='failed',stage='failed',completed_at=now(),
                message='Local federation failed validation or training. Check country tables and server diagnostics.')
        finally:
            with self.lock:self.active = None

    def close(self):self.pool.shutdown(wait=True)

    def saved(self):
        """Read-only canonical measured experiment, available after a restart."""
        from app.federation.artifacts import load_model
        from app.federation.parameters import checksum
        from app.federation.schemas import Metric
        from app.forecasting.data import digest
        folder = self.root/'data/demo/federation'
        integrity = json.loads((folder/'integrity.json').read_text(encoding='utf-8'))
        if digest(folder/'report.json')!=integrity['report_sha256']:
            raise ValueError('Saved federation report integrity mismatch')
        result = json.loads((folder/'report.json').read_text(encoding='utf-8'))
        if result['status']!='completed' or result['model_version']!=MODEL_VERSION:
            raise ValueError('Incompatible saved federation report')
        if checksum(load_model(folder/'global'))!=result['final_checksum']:
            raise ValueError('Saved federation report/model mismatch')
        if result['raw_records_shared']!=0 or len(result['nodes'])!=5:
            raise ValueError('Invalid federation evidence')
        for row in result['rounds']:
            Metric.model_validate(row['global_validation'])
        for node in result['nodes']:
            for metric in ('local_only','initial_global','federated_global'):
                Metric.model_validate(node[metric])
        Metric.model_validate(result['global_test'])
        return {**result, 'saved_demo': True}

    # Prepared future Copilot interfaces; intentionally absent from the 13-tool registry.
    def get_federation_status(self):return self.status()
    def get_federation_results(self,run_id):return self.store.get(run_id)
