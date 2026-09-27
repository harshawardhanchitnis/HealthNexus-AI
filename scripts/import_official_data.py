"""Offline by default. --refresh downloads from verified, fixed public URLs."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.data_ingestion.catalog import ADAPTERS, import_source

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["all", *ADAPTERS], default="all")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for name in ADAPTERS if args.source == "all" else [args.source]:
        dataset = import_source(name, refresh=args.refresh)
        print(f"{name}: normalized {len(dataset.records)} real observations; accessed {dataset.provenance.accessed_at}; version {dataset.provenance.version}")
