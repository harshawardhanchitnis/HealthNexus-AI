from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from uuid import UUID
from pathlib import Path
import shutil


class RunStore:
    def __init__(self,root,limit=8):
        self.root = Path(root)/'artifacts/federation/runs'
        self.limit = limit;self.lock = RLock();self.runs = OrderedDict()

    def folder(self,run_id):
        UUID(run_id)
        folder = (self.root/run_id).resolve()
        if folder.parent!=self.root.resolve(): raise ValueError('Invalid artifact path')
        return folder

    def create(self,run):
        with self.lock:
            if len(self.runs)>=self.limit:
                old = next((k for k,v in self.runs.items() if v['status'] in ('completed','failed')),None)
                if old is None: raise ValueError('Run store full')
                self.delete(old)
            self.runs[run['run_id']] = deepcopy(run)

    def update(self,run_id,**fields):
        with self.lock:self.runs[run_id].update(deepcopy(fields))

    def get(self,run_id):
        with self.lock:
            if run_id not in self.runs: raise KeyError('Federation run not found')
            return deepcopy(self.runs[run_id])

    def delete(self,run_id):
        with self.lock:
            run = self.get(run_id)
            if run['status'] not in ('completed','failed'): raise ValueError('Cannot delete active training')
            folder = self.folder(run_id)
            if folder.exists():shutil.rmtree(folder)
            del self.runs[run_id]
