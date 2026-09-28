"""Coordinator sees model updates/aggregate metadata, never local arrays."""
import json
from time import perf_counter
from threading import Lock
import torch
from app.federation.config import COUNTRIES, MODEL_VERSION, FEATURES, PARAMETER_COUNT, LEARNING_RATE, BATCH_SIZE, CPU_THREADS
from app.federation.models import make_model, get_parameters
from app.federation.client import FederatedClient
from app.federation.schemas import ClientUpdate
from app.federation.parameters import checksum, encode, wire_bytes, wire_payload
from app.federation.aggregator import aggregate
from app.federation.evaluation import aggregate_metrics
from app.federation.artifacts import save_model, load_model

TRAINING_LOCK = Lock()


def run_training(root,request,folder,progress):
    with TRAINING_LOCK:
        previous_threads = torch.get_num_threads()
        previous_determinism = torch.are_deterministic_algorithms_enabled()
        torch.set_num_threads(CPU_THREADS);torch.use_deterministic_algorithms(True)
        try:return _run(root,request,folder,progress)
        finally:
            torch.set_num_threads(previous_threads);torch.use_deterministic_algorithms(previous_determinism)


def _run(root,request,folder,progress):
    began = perf_counter();metadata_bytes = 0
    def metadata_packet(data):
        nonlocal metadata_bytes
        payload = json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        metadata_bytes += len(payload)
        return json.loads(payload)
    clients = []
    for country in COUNTRIES:
        progress('loading',0,country,f'{country}: loading only its own footfall table')
        clients.append(FederatedClient(country,root,request.seed))
    nodes = [metadata_packet(c.describe()) for c in clients]
    parameters = get_parameters(make_model(request.seed));initial_checksum = checksum(parameters)
    save_model(folder/'global/initial',parameters)
    def distribute(parameters,round_number):
        # A serialized tensor packet actually crosses each logical client boundary.
        payload = json.dumps({'model_version':MODEL_VERSION,'round':round_number,
            'checksum':checksum(parameters),'parameters':{k:v.model_dump() for k,v in encode(parameters).items()}},
            sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        for client in clients:client.receive_global(payload)
        return len(payload)*len(clients)
    downlink = distribute(parameters,0);uplink = 0
    initial_test = {c.country_id:metadata_packet(c.evaluate('test').model_dump()) for c in clients}
    initial_validation = [c.evaluate() for c in clients]
    for metric in initial_validation:metadata_packet(metric.model_dump())
    rounds = [{'round':0,'global_validation':aggregate_metrics(initial_validation).model_dump(),
        'parameter_checksum':initial_checksum,'update_bytes':0,'downlink_bytes':downlink,'raw_records_shared':0,'raw_records_sent':0,
        'clients':[],'weights':{},'seconds':0}]
    progress('initialized',0,None,'Identical initial global weights distributed to all five clients',rounds=rounds,nodes=nodes)
    # Independent baseline uses the same total local epochs and per-round shuffles.
    local_test = {}
    for client in clients:
        progress('local-baseline',0,client.country_id,f'{client.country_id}: training independent local-only comparator')
        for r in range(1,request.rounds+1):client.train_local(request.local_epochs,r)
        client.save_local_model(folder/'country'/client.country_id/'local-only')
        local_test[client.country_id] = metadata_packet(client.evaluate('test').model_dump())
    for round_number in range(1,request.rounds+1):
        started = perf_counter();start_hash = checksum(parameters);updates = []
        # Restores all clients to round-0 weights after local-only training.
        # Later rounds already received the newly aggregated model below.
        if round_number==1:downlink += distribute(parameters,0)
        for client in clients:
            progress('local-training',round_number,client.country_id,f'{client.country_id}: local epoch training')
            info = client.train_local(request.local_epochs,round_number)
            exported = client.export_update(round_number,start_hash,request.local_epochs,info)
            payload = wire_payload(exported)
            # Aggregator receives a validated wire DTO, not a client or dataset.
            update = ClientUpdate.model_validate_json(payload)
            updates.append(update);uplink += wire_bytes(update)
            client.save_local_model(folder/'country'/client.country_id/'latest-local')
            progress('update-sent',round_number,client.country_id,
                f'{client.country_id}: {update.bytes_transferred} update bytes sent; raw records shared 0')
        progress('aggregating',round_number,None,'Averaging model parameters under the selected policy')
        parameters,weights = aggregate(updates,round_number,start_hash,request.policy)
        progress('distributing',round_number,None,'Distributing the new global parameters to each country')
        sent_down = distribute(parameters,round_number);downlink += sent_down
        metrics = [c.evaluate() for c in clients]
        for metric in metrics:metadata_packet(metric.model_dump())
        summary = [{k:v for k,v in u.model_dump(mode='json').items() if k!='parameters'} for u in updates]
        for item,metric in zip(summary,metrics):item['global_validation'] = metric.model_dump()
        row = {'round':round_number,'global_validation':aggregate_metrics(metrics).model_dump(),
            'parameter_checksum':checksum(parameters),'update_bytes':sum(u.bytes_transferred for u in updates),
            'downlink_bytes':sent_down,'raw_records_shared':sum(u.raw_records_shared for u in updates),
            'raw_records_sent':sum(u.raw_records_shared for u in updates),
            'clients':summary,'weights':weights,'seconds':perf_counter()-started}
        rounds.append(row)
        progress('round-completed',round_number,None,'Global model updated; validation evaluated locally',rounds=rounds)
    save_model(folder/'global/final',parameters)
    restored = load_model(folder/'global/final')
    if checksum(restored)!=checksum(parameters):raise ValueError('Global save/reload differs')
    downlink += distribute(restored,request.rounds)
    results = [];test_metrics = []
    for client,node in zip(clients,nodes):
        final = client.evaluate('test');test_metrics.append(final)
        final_dict = metadata_packet(final.model_dump())
        baseline = local_test[client.country_id];delta = final.wape-baseline['wape'] if final.wape is not None and baseline['wape'] is not None else None
        results.append({**node,'local_only':baseline,'initial_global':initial_test[client.country_id],
            'federated_global':final_dict,'wape_change_vs_local':delta,
            'change':'unchanged' if delta is None or abs(delta)<=1e-8 else ('improved' if delta<0 else 'degraded'),
            'raw_records_shared':0,'latest_update_bytes':rounds[-1]['clients'][COUNTRIES.index(client.country_id)]['bytes_transferred']})
        results[-1]['local_only_artifact'] = f'country/{client.country_id}/local-only/parameters.npz'
        results[-1]['latest_local_artifact'] = f'country/{client.country_id}/latest-local/parameters.npz'
    return {'nodes':results,'rounds':rounds,'global_test':aggregate_metrics(test_metrics).model_dump(),
        'initial_checksum':initial_checksum,'final_checksum':checksum(parameters),'model_reload_verified':True,
        'parameter_count':PARAMETER_COUNT,'parameter_bytes':PARAMETER_COUNT*4,'features':list(FEATURES),
        'update_bytes':uplink,'downlink_bytes':downlink,'aggregate_metadata_bytes':metadata_bytes,
        'bytes_exchanged':uplink+downlink+metadata_bytes,'raw_records_shared':0,'training_seconds':perf_counter()-began,
        'global_artifact':'global/final/parameters.npz','framework':f'PyTorch {torch.__version__} CPU',
        'architecture':'16 → Dense(16)/ReLU → Dense(8)/ReLU → Dense(1)',
        'training_settings':{'optimizer':'SGD, no momentum','learning_rate':LEARNING_RATE,'batch_size':BATCH_SIZE,'cpu_threads':CPU_THREADS,
            'deterministic_algorithms':True,'target_normalization':'footfall / preceding 28-day mean at frozen forecast origin; minimum scale 1'},
        'evaluation_note':'Round metrics are selection-window validation; test is excluded from training and tuning. Local-only receives the same total epochs. Overlapping forecast-origin/horizon samples are not IID patient records.'}
