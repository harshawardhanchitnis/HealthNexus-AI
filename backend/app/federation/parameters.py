"""Wire format: named float32 tensors and strict aggregate metadata only."""
import hashlib
import json
import numpy as np
from app.federation.config import SHAPES, PARAMETER_COUNT, MODEL_VERSION
from app.federation.schemas import Parameter, ClientUpdate


def encode(parameters):
    return {name: Parameter(shape=list(value.shape), values=np.asarray(value,dtype='<f4').ravel().tolist())
        for name,value in parameters.items()}


def decode(packet):
    if set(packet) != set(SHAPES): raise ValueError('Parameter names mismatch')
    result = {}
    for name, expected in SHAPES.items():
        item = packet[name]
        if tuple(item.shape) != expected or len(item.values) != int(np.prod(expected)):
            raise ValueError('Parameter shape mismatch')
        with np.errstate(over='ignore'):
            value = np.asarray(item.values,dtype='<f4').reshape(expected)
        if not np.isfinite(value).all(): raise ValueError('Non-finite parameters')
        result[name] = value.copy()
    return result


def checksum(parameters):
    h = hashlib.sha256()
    for name in sorted(parameters):
        a = np.asarray(parameters[name],dtype='<f4')
        h.update(name.encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()


def wire_payload(update):
    return json.dumps(update.model_dump(mode='json'),sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def wire_bytes(update):return len(wire_payload(update))


def seal_update(**fields):
    update = ClientUpdate(**fields,bytes_transferred=0)
    # Includes its own counter; digit count converges after at most a few passes.
    for _ in range(5):
        size = wire_bytes(update)
        if size == update.bytes_transferred: return update
        update = update.model_copy(update={'bytes_transferred':size})
    raise ValueError('Update size failed to converge')


def validate_update(update, round_number, starting_checksum):
    update = ClientUpdate.model_validate(update.model_dump())
    if update.model_version != MODEL_VERSION or update.round != round_number:
        raise ValueError('Model version or round mismatch')
    if update.starting_checksum != starting_checksum: raise ValueError('Client did not start from global weights')
    parameters = decode(update.parameters)
    if checksum(parameters) != update.parameter_checksum: raise ValueError('Update checksum mismatch')
    if update.parameter_count != PARAMETER_COUNT or update.parameter_bytes != PARAMETER_COUNT*4:
        raise ValueError('Parameter byte/count mismatch')
    if wire_bytes(update) != update.bytes_transferred: raise ValueError('Wire byte count mismatch')
    return parameters
