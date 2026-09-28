from time import perf_counter
import torch
from app.federation.config import COUNTRIES, MODEL_VERSION, PARAMETER_COUNT, LEARNING_RATE, BATCH_SIZE
from app.federation.data import CountryDataLoader
from app.federation.models import make_model, get_parameters, set_parameters
from app.federation.evaluation import evaluate_arrays
from app.federation.parameters import checksum, encode, seal_update


class FederatedClient:
    def __init__(self,country_id,root,seed=42):
        self.country_id = country_id;self.seed = seed
        self._loader = CountryDataLoader(country_id,root)
        self._data = self._loader.load()
        self.model = make_model(seed)
        self._x = torch.from_numpy(self._data['train']['x'])
        self._y = torch.from_numpy(self._data['train']['y']).reshape(-1,1)

    def describe(self): return self._loader.describe(self._data)
    def get_parameters(self): return get_parameters(self.model)
    def set_parameters(self,parameters): set_parameters(self.model,parameters)

    def receive_global(self,payload):
        import json
        from app.federation.parameters import decode
        from app.federation.schemas import Parameter
        packet = json.loads(payload)
        if set(packet)!={'model_version','round','checksum','parameters'} or packet['model_version']!=MODEL_VERSION:
            raise ValueError('Invalid global distribution packet')
        if type(packet['round']) is not int or not 0<=packet['round']<=10:raise ValueError('Invalid global round')
        parameters = decode({k:Parameter.model_validate(v) for k,v in packet['parameters'].items()})
        if checksum(parameters)!=packet['checksum']:raise ValueError('Global checksum mismatch')
        self.set_parameters(parameters)

    def save_local_model(self,folder):
        from app.federation.artifacts import save_model
        return save_model(folder,self.get_parameters())

    def loss(self):
        with torch.no_grad():return float(torch.mean((self.model(self._x)-self._y)**2))

    def train_local(self,epochs,round_number):
        before = self.loss();began = perf_counter();self.model.train()
        optimizer = torch.optim.SGD(self.model.parameters(),lr=LEARNING_RATE)
        generator = torch.Generator().manual_seed(self.seed+round_number*100+COUNTRIES.index(self.country_id))
        for _ in range(epochs):
            order = torch.randperm(len(self._y),generator=generator)
            for batch in order.split(BATCH_SIZE):
                optimizer.zero_grad();loss = torch.mean((self.model(self._x[batch])-self._y[batch])**2)
                loss.backward();optimizer.step()
        after = self.loss()
        return {'train_loss_before':before,'train_loss_after':after,'training_seconds':perf_counter()-began}

    def evaluate(self,partition='validation'):
        if partition not in ('validation','test'): raise ValueError('Evaluation partition not allowed')
        data = self._data[partition]
        self.model.eval()
        with torch.no_grad(): pred = self.model(torch.from_numpy(data['x'])).squeeze(1).numpy()
        return evaluate_arrays(data['y'],pred,data['scale'])

    def export_update(self,round_number,starting_checksum,epochs,training):
        parameters = self.get_parameters()
        return seal_update(country_id=self.country_id,round=round_number,sample_count=len(self._y),
            model_version=MODEL_VERSION,parameters=encode(parameters),parameter_checksum=checksum(parameters),
            starting_checksum=starting_checksum,parameter_count=PARAMETER_COUNT,parameter_bytes=PARAMETER_COUNT*4,
            validation=self.evaluate(),local_epochs=epochs,**training)
