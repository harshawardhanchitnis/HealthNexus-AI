"""Cache hints cannot change artifact bytes, validation or platform support."""
import hashlib
import os
import pytest

from app.core.artifact_io import artifact_bytes, artifact_reader, artifact_sha256
from app.core.integrity import sha256
from app.forecasting.data import digest


@pytest.mark.parametrize('enabled', [False, True])
def test_streamed_hash_and_read_are_identical(tmp_path, monkeypatch, enabled):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', str(enabled).lower())
    payload = bytes(range(256)) * 8193
    path = tmp_path/'immutable.bin'
    path.write_bytes(payload)
    hints = []
    monkeypatch.setattr(os, 'POSIX_FADV_DONTNEED', 4, raising=False)
    monkeypatch.setattr(os, 'posix_fadvise', lambda *args: hints.append(args), raising=False)
    expected = hashlib.sha256(payload).hexdigest()
    assert artifact_bytes(path) == payload
    assert artifact_sha256(path) == sha256(path) == digest(path) == expected
    assert len(hints) == (4 if enabled else 0)
    assert all(offset == size == 0 and advice == 4 for _, offset, size, advice in hints)
    # Changed source bytes must still produce a different identity.
    path.write_bytes(payload+b'changed')
    assert artifact_sha256(path) != expected


@pytest.mark.parametrize('supported', [False, True])
def test_optional_hint_never_hides_read_or_validation_errors(tmp_path, monkeypatch, supported):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', 'true')
    path = tmp_path/'immutable.bin'
    path.write_bytes(b'actual bytes')
    if supported:
        def unsupported_filesystem(*args):
            raise OSError('advisory hint unavailable')
        monkeypatch.setattr(os, 'posix_fadvise', unsupported_filesystem, raising=False)
        monkeypatch.setattr(os, 'POSIX_FADV_DONTNEED', 4, raising=False)
    else:
        monkeypatch.delattr(os, 'posix_fadvise', raising=False)
    assert artifact_bytes(path) == b'actual bytes'
    with pytest.raises(ValueError, match='validation failure'):
        with artifact_reader(path) as stream:
            assert stream.read() == b'actual bytes'
            raise ValueError('validation failure')
    assert stream.closed
    with pytest.raises(FileNotFoundError):
        artifact_bytes(tmp_path/'missing.bin')
