"""Return unused allocator pages after serialized low-memory requests.

glibc otherwise retains temporary JSON/model/response buffers for future reuse.
This optional Linux hint frees no live objects and evicts no application cache.
It is deliberately disabled in the unrestricted development runtime.
"""
import ctypes
from functools import lru_cache
import sys

from app.core.runtime import low_memory


@lru_cache(maxsize=1)
def _trim_function():
    if sys.platform != 'linux':
        return None
    try:
        trim = ctypes.CDLL(None).malloc_trim
        trim.argtypes = [ctypes.c_size_t]
        trim.restype = ctypes.c_int
        return trim
    except (AttributeError, OSError):
        return None


def release_transient_memory():
    if low_memory():
        trim = _trim_function()
        if trim is not None:
            trim(0)
