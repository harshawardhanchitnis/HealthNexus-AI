"""Run from the repository root: python scripts/generate_data.py."""
import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.simulation.generator import generate_snapshot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    snapshot = generate_snapshot(args.seed, args.as_of)
    target = ROOT / "data/generated/network.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    print(f"Generated {len(snapshot.facilities)} synthetic facilities across {len(snapshot.regions)} states/UTs: {target}")

