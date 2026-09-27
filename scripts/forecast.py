"""Explicit Phase 3 workflow; no fitting occurs at API startup."""
import argparse
from datetime import date
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.geography import COUNTRY_BY_ID
from app.forecasting.data import generate_history, build_tables
from app.forecasting.training import train_country, evaluate_saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["generate", "build", "train", "evaluate"])
    parser.add_argument("--country", choices=["all", *COUNTRY_BY_ID], default="all")
    parser.add_argument("--days", type=int, default=540)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 9, 27))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    for country in COUNTRY_BY_ID if args.country == "all" else [args.country]:
        if args.action == "generate":
            result = generate_history(country, args.days, args.as_of, args.seed)
        elif args.action == "build":
            result = build_tables(country)
        elif args.action == "train":
            result = train_country(country)
        else:
            result = evaluate_saved(country)
        print(json.dumps({"country": country, "action": args.action, "result": result}, indent=2), flush=True)
