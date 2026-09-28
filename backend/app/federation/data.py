"""Client-local read of existing frozen-origin Phase 3 footfall tables only."""
import hashlib
import json
from pathlib import Path
import numpy as np
from app.federation.config import COUNTRIES, FEATURES
from app.forecasting.features import FEATURES as SOURCE_FEATURES


class CountryDataLoader:
    def __init__(self,country_id,root):
        if country_id not in COUNTRIES: raise ValueError('Unknown country')
        self.country_id = country_id
        base = (Path(root)/'data/generated/training').resolve()
        self.folder = (base/country_id).resolve()
        if self.folder != base/country_id: raise ValueError('Country directory escapes its country partition')

    def load(self,country_id=None):
        if country_id is not None and country_id != self.country_id: raise ValueError('Cross-country client read denied')
        manifest_path = self.folder/'manifest.json'
        if manifest_path.resolve().parent != self.folder:raise ValueError('Manifest escapes country partition')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['country_id'] != self.country_id or any(s['country_id'] != self.country_id for s in manifest['series']['footfall']):
            raise ValueError('Country manifest mismatch')
        if manifest['feature_schema'] != SOURCE_FEATURES: raise ValueError('Source feature schema mismatch')
        path = self.folder/'footfall.npz'
        if path.resolve().parent != self.folder: raise ValueError('Country table escapes its directory')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != manifest['tables']['footfall']['sha256']: raise ValueError('Stale/corrupt local training table')
        with np.load(path,allow_pickle=False) as source:
            raw = source['X']; scale = source['scale'].astype(np.float32); y = source['y'].astype(np.float32)
            split = source['split']; origin = source['origin']; day = source['target_day']
            if not (len(raw)==len(y)==len(scale)==len(split)) or np.any(scale<=0) or np.any(origin>=day):
                raise ValueError('Invalid scaling or leaked forecast origin')
            if not np.isfinite(raw).all() or not np.isfinite(y).all() or not np.isfinite(scale).all() or np.any(y<0):
                raise ValueError('Non-finite or negative observations')
            if set(split.tolist()) != {0,1,2,3}: raise ValueError('Missing temporal partitions')
            for a,b in zip((0,1,2),(1,2,3)):
                if day[split==a].max() >= day[split==b].min(): raise ValueError('Temporal partitions overlap')
            col = lambda name: raw[:,SOURCE_FEATURES.index(name)]
            weekday = col('weekday')*2*np.pi/7
            kind = col('facility_type')
            x = np.column_stack([col('horizon')/14,np.sin(weekday),np.cos(weekday),col('annual_sin'),
                col('annual_cos'),col('trend')/2,*[col(n) for n in ('lag1_ratio','lag7_ratio','lag14_ratio',
                'mean7_ratio','mean14_ratio','std28_ratio','growth7')],*(kind==i for i in range(3))]).astype(np.float32)
        if x.shape[1] != len(FEATURES): raise ValueError('Federation feature mismatch')
        # Arrays never leave FederatedClient. No multi-country concatenation.
        self.manifest = manifest
        self.table_sha256 = digest
        return {name: {'x':x[split==index].copy(),'y':(y/scale)[split==index].copy(),'scale':scale[split==index].copy()}
            for name,index in (('train',0),('validation',1),('test',3))}

    def describe(self,data):
        return {'country_id':self.country_id,'facility_count':len(self.manifest['series']['footfall']),
            'local_samples':len(data['train']['y']),'validation_samples':len(data['validation']['y']),
            'test_samples':len(data['test']['y']),'history_days':self.manifest['days'],
            'table_sha256':self.table_sha256,'history_sha256':self.manifest['history_sha256'],
            'as_of':self.manifest['as_of'],'windows':self.manifest['windows'],
            'data_type':'calibrated simulated operations','data_source':'country-local Phase 3 source-history footfall tables',
            'inventory_profile_dependence':'none; operational inventory profiles do not change footfall histories'}


def prepare_country(country_id,root):
    """Local preparation boundary exports only a summary, never loaded arrays."""
    loader = CountryDataLoader(country_id,root)
    local_data = loader.load()
    return loader.describe(local_data)
