"""Long histories and compact, inspectable temporal training tables."""
from datetime import timedelta
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

from app.core.config import ROOT
from app.data_ingestion.base import save_json
from app.forecasting.features import FEATURES, feature_block, origins_for, split_bounds
from app.models.network import Snapshot
from app.simulation.generator import generate_snapshot

TARGETS = ("footfall", "medicine", "admissions")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def facility_hash(facility):
    return hashlib.sha256(facility.model_dump_json().encode()).hexdigest()


def generate_history(country: str, days: int, as_of, seed: int, root: Path = ROOT):
    split_bounds(days)
    data = generate_snapshot(seed, as_of, country, history_days=days)
    path = root / "data/generated/history" / f"{country}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 makes the compressed source hash reproducible.
    payload = gzip.compress(data.model_dump_json().encode(), compresslevel=5, mtime=0)
    path.with_suffix(".tmp").write_bytes(payload)
    path.with_suffix(".tmp").replace(path)
    for f in data.facilities:
        f.history = f.history[-28:]
        for item in f.inventory:
            item.ledger = item.ledger[-28:]
    snapshot = root / "data/generated" / ("network.json" if country == "IN" else f"nodes/{country}/network.json")
    save_json(snapshot, data)
    return {"country": country, "days": days, "facilities": len(data.facilities), "history_sha256": digest(path)}


def series_from(data: Snapshot, target: str):
    for f in data.facilities:
        context = {"facility_id": f.id, "country_id": f.country_id, "region_id": f.state_id,
            "district_id": f.district_id, "facility_type": f.type,
            "type_index": ["PHC", "CHC", "District Hospital", "Primary Care Centre", "Community Hospital", "Regional Hospital"].index(f.type) % 3,
            "catchment": f.catchment_population, "beds": f.beds.total,
            "scheduled_staff": f.history[0].scheduled_staff, "latitude": f.latitude}
        if target == "medicine":
            for index, item in enumerate(f.inventory):
                yield {**context, "medicine_index": index, "resource_id": item.medicine_id, "unit": item.unit}, np.array([r.requested for r in item.ledger], dtype=np.float32)
        else:
            # Requested admissions avoids learning the bed-capacity censoring ceiling.
            values = [r.footfall if target == "footfall" else r.admissions + r.unmet_admissions for r in f.history]
            yield {**context, "medicine_index": -1, "resource_id": target, "unit": "visits" if target == "footfall" else "admissions requested"}, np.array(values, dtype=np.float32)


def build_tables(country: str, root: Path = ROOT):
    source = root / "data/generated/history" / f"{country}.json.gz"
    data = Snapshot.model_validate_json(gzip.decompress(source.read_bytes()))
    if data.country != country:
        raise ValueError("History country mismatch")
    start = data.facilities[0].history[0].date
    days = len(data.facilities[0].history)
    expected_dates = [start+timedelta(days=i) for i in range(days)]
    for f in data.facilities:
        if [r.date for r in f.history] != expected_dates or any([r.date for r in item.ledger] != expected_dates for item in f.inventory):
            raise ValueError("Training histories must be complete aligned daily series")
        if any(row.scheduled_staff is None for row in f.history) or f.catchment_population is None:
            raise ValueError("Rebuild historical data with Phase 3 context")
    folder = root / "data/generated/training" / country
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {"country_id": country, "start": str(start), "as_of": str(data.as_of), "days": days,
        "history_sha256": digest(source), "feature_schema": FEATURES, "seed": data.seed,
        "calibration": data.calibration, "data_type": "calibrated simulated operations",
        "source_vintage_note": "Public aggregates accessed in 2026 are held fixed for this retrospective synthetic experiment; this is not an as-published real-world backtest.",
        "windows": {}, "tables": {}, "series": {}, "facility_hashes": {}}
    for name, (a, b) in zip(("train", "selection", "calibration", "test"), split_bounds(days)):
        manifest["windows"][name] = {"start": str(start+timedelta(days=a)), "end": str(start+timedelta(days=b-1))}
    for target in TARGETS:
        blocks = {key: [] for key in ("X", "y", "scale", "baselines", "split", "origin", "target_day", "series")}
        contexts = []
        for sid, (context, values) in enumerate(series_from(data, target)):
            contexts.append({**context, "last28": values[-28:].tolist()})
            for split, origin in origins_for(days, sid):
                x, scale, base = feature_block(values, origin, start, context)
                h = len(x)
                for key, value in {"X": x, "y": values[origin+1:origin+h+1], "scale": np.full(h, scale),
                    "baselines": base, "split": np.full(h, split), "origin": np.full(h, origin),
                    "target_day": np.arange(origin+1, origin+h+1), "series": np.full(h, sid)}.items():
                    blocks[key].append(value)
        arrays = {key: np.concatenate(value).astype(np.float32 if key in ("X", "y", "scale", "baselines") else np.int32) for key, value in blocks.items()}
        np.savez_compressed(folder / f"{target}.npz", **arrays)
        manifest["tables"][target] = {"rows": len(arrays["y"]), "sha256": digest(folder / f"{target}.npz")}
        manifest["series"][target] = contexts
    for f in data.facilities:
        f.history = f.history[-28:]
        for item in f.inventory:
            item.ledger = item.ledger[-28:]
        manifest["facility_hashes"][f.id] = facility_hash(f)
    save_json(folder / "manifest.json", manifest)
    return {target: item["rows"] for target, item in manifest["tables"].items()}
