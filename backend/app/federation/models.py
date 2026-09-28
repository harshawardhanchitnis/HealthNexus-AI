import numpy as np
import torch
from torch import nn
from app.federation.config import FEATURES, SHAPES


def make_model(seed=42):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return nn.Sequential(nn.Linear(len(FEATURES),16),nn.ReLU(),nn.Linear(16,8),nn.ReLU(),nn.Linear(8,1))


def get_parameters(model):
    return {name:value.detach().cpu().numpy().copy() for name,value in model.state_dict().items()}


def set_parameters(model,parameters):
    if set(parameters)!=set(SHAPES): raise ValueError('Parameter names mismatch')
    if any(tuple(parameters[n].shape)!=SHAPES[n] or not np.isfinite(parameters[n]).all() for n in SHAPES):
        raise ValueError('Invalid model parameters')
    model.load_state_dict({name:torch.from_numpy(value.copy()) for name,value in parameters.items()},strict=True)
