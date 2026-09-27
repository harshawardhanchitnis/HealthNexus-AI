"""Run from the repository root: python scripts/generate_data.py."""
import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.simulation.generator import generate_snapshot
from app.core.geography import COUNTRY_BY_ID
from app.data_ingestion.base import save_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--country", choices=["all", *COUNTRY_BY_ID], default="IN")
    args = parser.parse_args()
    for code in COUNTRY_BY_ID if args.country == "all" else [args.country]:
        snapshot = generate_snapshot(args.seed, args.as_of, code)
        target = ROOT / "data/generated/network.json" if code == "IN" else ROOT / "data/generated/nodes" / code / "network.json"
        save_json(target, snapshot)
        print(f"{code}: generated {len(snapshot.facilities)} calibrated synthetic facilities across {len(snapshot.regions)} regions; {target}")
