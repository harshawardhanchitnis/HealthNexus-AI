from unittest.mock import Mock
from app.core import allocator


def test_optional_trim_only_in_low_memory(monkeypatch):
    trim = Mock(return_value=1)
    monkeypatch.setattr(allocator, '_trim_function', lambda: trim)
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', 'false')
    allocator.release_transient_memory()
    trim.assert_not_called()
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', 'true')
    allocator.release_transient_memory()
    trim.assert_called_once_with(0)


def test_platform_without_trim_is_supported(monkeypatch):
    monkeypatch.setenv('HEALTHNEXUS_LOW_MEMORY', 'true')
    monkeypatch.setattr(allocator, '_trim_function', lambda: None)
    allocator.release_transient_memory()
