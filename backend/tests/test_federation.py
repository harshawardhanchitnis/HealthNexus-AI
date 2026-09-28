import hashlib
import json
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4
import numpy as np
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.federation.config import COUNTRIES, MODEL_VERSION, PARAMETER_COUNT, SHAPES
from app.federation.schemas import RunRequest, ClientUpdate
from app.federation.parameters import encode, decode, checksum, seal_update, wire_bytes
from app.federation.aggregator import aggregate
from app.federation.models import make_model, get_parameters
from app.federation.client import FederatedClient
from app.federation.data import CountryDataLoader
from app.federation.evaluation import evaluate_arrays, aggregate_metrics
from app.federation.artifacts import save_model, load_model
from app.federation.service import FederationService
from app.federation.storage import RunStore
from app.forecasting.features import FEATURES as SOURCE_FEATURES
from app.main import create_app


@pytest.fixture(scope='module')
def country_tables(tmp_path_factory):
    root = tmp_path_factory.mktemp('federation')
    for ci,country in enumerate(COUNTRIES):
        folder = root/'data/generated/training'/country;folder.mkdir(parents=True)
        count = 128 if country=='IN' else 32
        split = np.repeat(np.arange(4),count)
        x = np.zeros((len(split),len(SOURCE_FEATURES)),dtype=np.float32)
        x[:,0] = np.tile(np.arange(len(split))%14+1,1);x[:,1] = np.arange(len(split))%7
        x[:,2] = .4;x[:,3] = .9;x[:,4] = .8
        x[:,5:12] = 1.;x[:,12] = .1;x[:,15] = ci%3
        y = (1+.05*np.sin(np.arange(len(split))))*100
        path = folder/'footfall.npz'
        np.savez_compressed(path,X=x,y=y.astype(np.float32),scale=np.full(len(split),100,dtype=np.float32),
            split=split,origin=np.arange(len(split)),target_day=np.arange(len(split))+1)
        manifest = {'country_id':country,'series':{'footfall':[{'country_id':country}]},
            'tables':{'footfall':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}},'feature_schema':SOURCE_FEATURES,
            'days':540,'history_sha256':'local-only-history','as_of':'2026-09-27','windows':{'test':{'start':'2026-08-05','end':'2026-09-27'}}}
        (folder/'manifest.json').write_text(json.dumps(manifest))
        operational = root/'artifacts/models'/country/'bundle.joblib'
        operational.parent.mkdir(parents=True,exist_ok=True);operational.write_bytes(b'untouched operational model')
    (root/'data/generated/network.json').write_text('immutable operational snapshot')
    return root


def update(country='IN',count=100,value=1,round_number=1,start='0'*64):
    p = {name:np.full(shape,value,dtype=np.float32) for name,shape in SHAPES.items()}
    # Explicit example [1,2] vs [3,4] in the first tensor entries.
    p['0.weight'].flat[1] = value+1
    metric = evaluate_arrays(np.ones(2),np.ones(2),np.ones(2))
    return seal_update(country_id=country,round=round_number,sample_count=count,parameters=encode(p),
        parameter_checksum=checksum(p),starting_checksum=start,parameter_count=PARAMETER_COUNT,
        parameter_bytes=PARAMETER_COUNT*4,validation=metric,local_epochs=1,
        train_loss_before=1,train_loss_after=.5,training_seconds=.01)


def test_real_fedavg_equation():
    a,b = update(),update('BR',300,3)
    result,weights = aggregate([a,b],1,'0'*64,expected_countries=('IN','BR'))
    np.testing.assert_array_equal(result['0.weight'].flat[:2],[2.5,3.5])
    assert weights=={'IN':.25,'BR':.75}
    assert all(np.all(v==2.5) for k,v in result.items() if k!='0.weight')


def test_balanced_policy_explicit_and_distinct():
    a,b = update(),update('BR',300,3)
    result,weights = aggregate([a,b],1,'0'*64,'balanced-country',('IN','BR'))
    np.testing.assert_array_equal(result['0.weight'].flat[:2],[2,3]);assert weights=={'IN':.5,'BR':.5}


@pytest.mark.parametrize('kind',['shape','names','version','round','checksum','start','count','bytes','duplicate','missing','policy'])
def test_invalid_update_rejected(kind):
    a,b = update(),update('BR',300,3);round_number=1;start='0'*64;policy='sample-weighted';countries=('IN','BR')
    if kind=='shape':a.parameters['0.weight'].shape=[1]
    if kind=='names':a.parameters.pop('4.bias')
    if kind=='version':a.model_version='foreign'
    if kind=='round':round_number=2
    if kind=='checksum':a.parameter_checksum='f'*64
    if kind=='start':start='f'*64
    if kind=='count':a.sample_count=0
    if kind=='bytes':a.bytes_transferred+=1
    if kind=='duplicate':b.country_id='IN'
    if kind=='missing':countries=COUNTRIES
    if kind=='policy':policy='hidden-equal'
    with pytest.raises((ValueError,ValidationError)):aggregate([a,b],round_number,start,policy,countries)


@pytest.mark.parametrize('value',[float('nan'),float('inf'),1e100])
def test_nonfinite_or_float32_overflow_rejected(value):
    a = update();a.parameters['4.bias'].values=[value]
    with pytest.raises((ValueError,ValidationError)):aggregate([a],1,'0'*64,expected_countries=('IN',))


@pytest.mark.parametrize('field',['footfall_rows','inventory_rows','patient_rows','X','y','targets','training_features'])
def test_raw_data_cannot_enter_update(field):
    payload = update().model_dump();payload[field]=[[123]]
    with pytest.raises(ValidationError):ClientUpdate.model_validate(payload)


def test_aggregator_only_accepts_update_objects():
    with pytest.raises(ValueError):aggregate([{'X':np.zeros((2,2))}],1,'0'*64)
    from app.federation import aggregator
    source = Path(aggregator.__file__).read_text()
    assert 'CountryDataLoader' not in source and 'FederatedClient' not in source


def test_parameter_byte_and_raw_boundary_counters():
    u = update();assert u.raw_records_shared==0
    assert u.parameter_bytes==sum(v.nbytes for v in decode(u.parameters).values())==417*4
    assert u.bytes_transferred==wire_bytes(u)>u.parameter_bytes
    assert set(u.model_dump())=={'country_id','round','sample_count','model_version','starting_checksum','parameter_checksum',
        'parameters','parameter_count','parameter_bytes','bytes_transferred','raw_records_shared','validation',
        'train_loss_before','train_loss_after','local_epochs','training_seconds'}


def test_same_initial_weights_and_real_local_changes(country_tables):
    a = FederatedClient('IN',country_tables);b = FederatedClient('BR',country_tables)
    initial = checksum(a.get_parameters());assert initial==checksum(b.get_parameters())
    info = a.train_local(1,1);assert checksum(a.get_parameters())!=initial
    assert checksum(b.get_parameters())==initial
    u = a.export_update(1,initial,1,info)
    assert u.sample_count==128 and u.starting_checksum==initial and u.raw_records_shared==0
    assert info['train_loss_before']!=info['train_loss_after']


def test_country_loader_cannot_read_other_node(country_tables):
    loader = CountryDataLoader('IN',country_tables)
    with pytest.raises(ValueError):loader.load('BR')
    with pytest.raises(ValueError):CountryDataLoader('../BR',country_tables)
    assert loader.load()['train']['x'].shape==(128,16)


def test_manifest_country_and_table_integrity(country_tables,tmp_path):
    import shutil
    folder=tmp_path/'data/generated/training/IN';shutil.copytree(country_tables/'data/generated/training/IN',folder)
    path=folder/'manifest.json';manifest=json.loads(path.read_text());manifest['country_id']='BR';path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):CountryDataLoader('IN',tmp_path).load()
    shutil.copyfile(country_tables/'data/generated/training/IN/manifest.json',path)
    with (folder/'footfall.npz').open('ab') as stream:stream.write(b'changed')
    with pytest.raises(ValueError):CountryDataLoader('IN',tmp_path).load()


def test_model_numeric_save_reload_and_corruption(tmp_path):
    original=get_parameters(make_model());save_model(tmp_path,original)
    loaded=load_model(tmp_path);assert checksum(original)==checksum(loaded)
    for name in original:np.testing.assert_array_equal(original[name],loaded[name])
    metadata=json.loads((tmp_path/'model.json').read_text());metadata['parameter_checksum']='f'*64
    (tmp_path/'model.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError):load_model(tmp_path)


def test_aggregate_evaluation_not_average_wapes():
    a=evaluate_arrays(np.array([1.,1.]),np.array([.5,.5]),np.ones(2))
    b=evaluate_arrays(np.array([10.]),np.array([10.]),np.ones(1))
    metric=aggregate_metrics([a,b]);assert metric.wape==pytest.approx(1/12)
    assert metric.mae==pytest.approx(1/3) and metric.samples==3


@pytest.fixture(scope='module')
def run_pair(country_tables):
    service=FederationService(country_tables)
    try:
        before={str(p):p.read_bytes() for p in (country_tables/'data').rglob('*') if p.is_file()}
        models_before={str(p):p.read_bytes() for p in (country_tables/'artifacts/models').rglob('*') if p.is_file()}
        a=service.start(RunRequest(rounds=2),background=False)
        b=service.start(RunRequest(rounds=2),background=False)
        assert all(p.read_bytes()==before[str(p)] for p in (country_tables/'data').rglob('*') if p.is_file())
        assert all(p.read_bytes()==models_before[str(p)] for p in (country_tables/'artifacts/models').rglob('*') if p.is_file())
        yield service,a,b
    finally:service.close()


def test_seed_determinism_and_metrics(run_pair):
    _,a,b=run_pair;assert a['status']==b['status']=='completed'
    assert a['final_checksum']==b['final_checksum']!=a['initial_checksum']
    assert [r['global_validation'] for r in a['rounds']]==[r['global_validation'] for r in b['rounds']]
    assert a['global_test']==b['global_test']
    assert {n['country_id'] for n in a['nodes']}==set(COUNTRIES)


def test_shared_round_initialization_and_weighting(run_pair):
    _,a,_=run_pair
    for previous,row in zip(a['rounds'],a['rounds'][1:]):
        assert {u['starting_checksum'] for u in row['clients']}=={previous['parameter_checksum']}
        total=sum(u['sample_count'] for u in row['clients'])
        for u in row['clients']:assert row['weights'][u['country_id']]==u['sample_count']/total
        assert row['raw_records_shared']==0


def test_run_bytes_and_no_raw_results(run_pair):
    _,a,_=run_pair
    assert a['raw_records_shared']==0 and a['bytes_exchanged']==a['update_bytes']+a['downlink_bytes']+a['aggregate_metadata_bytes']
    assert a['update_bytes']==sum(r['update_bytes'] for r in a['rounds'])
    assert a['model_reload_verified'] and a['parameter_count']==417
    assert all('parameters' not in u for r in a['rounds'] for u in r['clients'])
    assert not {'X','y','targets','patient_rows'} & a.keys()


def test_bounded_store_deletion_and_copy_isolation(tmp_path):
    store=RunStore(tmp_path,limit=1);a=str(uuid4());b=str(uuid4())
    store.create({'run_id':a,'status':'running'})
    with pytest.raises(ValueError):store.delete(a)
    store.update(a,status='completed');store.folder(a).mkdir(parents=True)
    (store.folder(a)/'model.txt').write_text('weights')
    got=store.get(a);got['status']='modified';assert store.get(a)['status']=='completed'
    store.create({'run_id':b,'status':'completed'});assert not store.folder(a).exists()
    with pytest.raises(KeyError):store.get(a)
    with pytest.raises(ValueError):store.folder('../../unrelated')
    store.delete(b)
    with pytest.raises(KeyError):store.get(b)


@pytest.mark.parametrize('body',[{'rounds':0},{'rounds':11},{'local_epochs':0},{'local_epochs':6},{'policy':'fake'},{'rounds':True},{'raw_rows':[]},{'seed':-1}])
def test_request_bounds(body):
    with pytest.raises(ValidationError):RunRequest(**body)


def test_api_async_progress_rounds_and_delete(country_tables):
    service=FederationService(country_tables)
    with TestClient(create_app(federation_service=service)) as client:
        assert client.get('/api/federation/status').json()['parameter_count']==417
        assert len(client.get('/api/federation/nodes').json()['items'])==5
        assert client.post('/api/federation/runs',json={'rounds':11}).status_code==422
        response=client.post('/api/federation/runs',json={'rounds':1});assert response.status_code==202
        run_id=response.json()['run_id'];seen=[];deadline=monotonic()+15
        while monotonic()<deadline:
            row=client.get('/api/federation/runs/'+run_id).json();seen.append(row['status'])
            if row['status'] in ('completed','failed'):break
            sleep(.01)
        assert row['status']=='completed' and row['events'] and row['raw_records_shared']==0
        assert len(client.get(f'/api/federation/runs/{run_id}/rounds').json()['items'])==2
        assert client.delete('/api/federation/runs/'+run_id).status_code==204
        assert client.get('/api/federation/runs/'+run_id).status_code==404
