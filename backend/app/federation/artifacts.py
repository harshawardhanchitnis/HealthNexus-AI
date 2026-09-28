"""Trusted local numeric checkpoints only; no pickle or raw training tables."""
import json
from pathlib import Path
import numpy as np
from app.federation.config import MODEL_VERSION, FEATURES
from app.federation.parameters import checksum, decode, encode


def save_model(folder,parameters):
    folder = Path(folder);folder.mkdir(parents=True,exist_ok=True)
    decode(encode(parameters))
    temp = folder/'parameters.tmp'
    with temp.open('wb') as stream: np.savez_compressed(stream,**parameters)
    temp.replace(folder/'parameters.npz')
    metadata = {'model_version':MODEL_VERSION,'features':list(FEATURES),'parameter_checksum':checksum(parameters)}
    (folder/'model.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return metadata


def load_model(folder):
    folder = Path(folder)
    metadata = json.loads((folder/'model.json').read_text(encoding='utf-8'))
    if metadata['model_version']!=MODEL_VERSION or metadata['features']!=list(FEATURES): raise ValueError('Incompatible saved model')
    with np.load(folder/'parameters.npz',allow_pickle=False) as data: parameters = {k:data[k].copy() for k in data.files}
    parameters = decode(encode(parameters))
    if checksum(parameters)!=metadata['parameter_checksum']: raise ValueError('Saved model checksum mismatch')
    return parameters
