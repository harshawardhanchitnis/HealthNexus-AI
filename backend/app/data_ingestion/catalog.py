from pathlib import Path

from app.core.config import ROOT
from app.data_ingestion.base import read_raw, save_json
from app.data_ingestion.india_hdi import IndiaHDIAdapter
from app.data_ingestion.who_gho import WHOGHOAdapter
from app.models.provenance import PublicDataset

ADAPTERS = {"india_hdi": IndiaHDIAdapter, "who_gho": WHOGHOAdapter}
RAW_PATHS = {"india_hdi": "india/hdi-2023.json", "who_gho": "who/brics-indicators.json"}


def import_source(name: str, refresh: bool = False, root: Path = ROOT) -> PublicDataset:
    adapter = ADAPTERS[name]()
    raw_path = root / "data/official" / RAW_PATHS[name]
    raw = adapter.fetch() if refresh else read_raw(raw_path)
    data = adapter.normalize(raw)  # Fully validate before touching the previous good files.
    if refresh:
        save_json(raw_path, raw)
    save_json(root / "data/normalized" / f"{name}.json", data)
    return data


def datasets(root: Path = ROOT) -> list[PublicDataset]:
    result = []
    for name, adapter in ADAPTERS.items():
        raw_path = root / "data/official" / RAW_PATHS[name]
        if not raw_path.exists():
            continue
        raw = read_raw(raw_path)
        expected = adapter().normalize(raw)
        normalized = root / "data/normalized" / f"{name}.json"
        if normalized.exists():
            data = PublicDataset.model_validate_json(normalized.read_text(encoding="utf-8"))
            if data.provenance.checksum_sha256 == raw.checksum_sha256 and data.adapter_version == adapter.version:
                if data != expected:
                    raise ValueError("Normalized public cache differs from the verified raw source")
                result.append(data)
                continue
        # Read-only fallback: reproducible offline normalization, never a network call.
        result.append(expected)
    return result


def latest_observations(country_id: str, root: Path = ROOT):
    latest = {}
    for dataset in datasets(root):
        for row in dataset.records:
            if row.country_id == country_id and (row.indicator not in latest or row.year > latest[row.indicator].year):
                latest[row.indicator] = row
    return latest
