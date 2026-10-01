"""Read immutable local artifacts without retaining their Linux filesystem cache.

Only the explicit low-memory runtime requests this advisory hint. It releases
already-read file pages, not Python objects, hashes or artifacts. Linux may
ignore the hint; unsupported platforms use the identical ordinary read. No
host-wide cache flush is performed. Callers still validate the complete bytes.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path

from app.core.runtime import low_memory


@contextmanager
def artifact_reader(path):
    with Path(path).open('rb') as stream:
        try:
            yield stream
        finally:
            if low_memory() and hasattr(os, 'posix_fadvise') and hasattr(os, 'POSIX_FADV_DONTNEED'):
                try:
                    os.posix_fadvise(stream.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
                except OSError:
                    # Filesystem/kernel support is optional; correctness never
                    # depends on a cache hint succeeding.
                    pass


def artifact_bytes(path):
    with artifact_reader(path) as stream:
        return stream.read()


def artifact_sha256(path):
    checksum = hashlib.sha256()
    with artifact_reader(path) as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            checksum.update(chunk)
    return checksum.hexdigest()
