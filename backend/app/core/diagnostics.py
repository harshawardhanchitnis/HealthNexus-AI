"""Request-local development timings; never change planner decisions."""
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

ACTIVE = ContextVar('planning_timings', default=None)

@contextmanager
def stage(name):
    start = perf_counter()
    try:
        yield
    finally:
        values = ACTIVE.get()
        if values is not None:
            values[name] = values.get(name, 0.) + perf_counter()-start


def clone(model):
    # Pydantic's Rust JSON round-trip copies nested validated values without
    # Python deepcopy's per-field recursion. No cached object escapes mutable.
    return type(model).model_validate_json(model.model_dump_json())


def diagnosed(function):
    from functools import wraps
    @wraps(function)
    def wrapped(*args, **kwargs):
        values = {}
        token = ACTIVE.set(values)
        started = perf_counter()
        try:
            result = function(*args, **kwargs)
            values['total_service'] = perf_counter()-started
            result.diagnostics = dict(values)
            if hasattr(result, 'run_id') and hasattr(args[0], 'results'):
                with args[0].lock:
                    args[0].results[result.run_id] = clone(result)
            return result
        finally:
            ACTIVE.reset(token)
    return wrapped
