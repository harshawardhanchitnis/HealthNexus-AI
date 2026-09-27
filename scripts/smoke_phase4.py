"""Live HTTP smoke verification; creates and discards only its own scenarios."""
import argparse
import json
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="docs/evaluation/phase4-smoke.json")
    args = parser.parse_args()

    def call(path, method="GET", body=None):
        data = None if body is None else json.dumps(body).encode()
        request = Request(args.base_url+path, data=data, method=method, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=120) as response:
            payload = response.read()
            return json.loads(payload) if payload else None

    def expected_error(path, code):
        try:
            call(path)
        except HTTPError as error:
            assert error.code == code
        else:
            raise AssertionError(f"Expected {code}: {path}")

    assert len(call("/api/scenarios/presets")["types"]) == 4
    records = []
    for country in ("IN", "BR", "RU", "CN", "ZA"):
        scope = f"country_id={country}" + ("&state_id=MH&district_id=MH-PUNE" if country == "IN" else "")
        facilities = call("/api/facilities?limit=250&"+scope)["items"]
        facility_id = facilities[0]["id"]
        baseline_path = f"/api/facilities/{facility_id}?country_id={country}"
        unchanged = call(baseline_path)
        baseline_forecast = call(f"/api/forecasts/facilities/{facility_id}/footfall?country_id={country}")
        for kind in ("DENGUE_SURGE", "DELIVERY_DELAY", "STAFF_SHORTAGE", "FACILITY_DISRUPTION"):
            body = {"scenario_type": kind, "country_id": country, "severity": "severe", "duration": 14, "seed": 42}
            if country == "IN":
                body.update(state_id="MH", district_id="MH-PUNE")
            if kind == "DELIVERY_DELAY":
                body["parameters"] = {"medicine_id": "IVF", "delay_days": 14}
            start = perf_counter()
            result = call("/api/scenarios", "POST", body)
            elapsed = perf_counter()-start
            sid = result["scenario"]["scenario_id"]
            try:
                query = f"country_id={country}&scenario_id={sid}"
                assert call(f"/api/scenarios/{sid}/comparison?country_id={country}")["delta"] == result["delta"]
                warnings = call("/api/warnings?"+query)
                assert warnings == result["warnings_created"]
                assert call("/api/warnings/summary?"+query) == warnings["summary"]
                assert sum(warnings["summary"]["counts"].values()) == len(warnings["items"])
                if warnings["items"]:
                    wid = warnings["items"][0]["warning_id"]
                    assert call(f"/api/warnings/{wid}?"+query)["warning_id"] == wid
                expected_error(f"/api/scenarios/{sid}?country_id={'BR' if country == 'IN' else 'IN'}", 404)
                assert call(baseline_path) == unchanged
                assert call(f"/api/forecasts/facilities/{facility_id}/footfall?country_id={country}") == baseline_forecast
                records.append({"country_id": country, "scenario_type": kind, "seconds": round(elapsed, 4),
                    "baseline": result["baseline"]["metrics"], "scenario": result["scenario_result"]["metrics"],
                    "resource_impact": result["resource_impact"], "warning_counts": warnings["summary"]["counts"],
                    "model_versions": sorted({f["provenance"]["model_version"] for f in result["scenario_result"]["facilities"]})})
                print(country, kind, round(elapsed, 3), warnings["summary"]["counts"])
            finally:
                call(f"/api/scenarios/{sid}?country_id={country}", "DELETE")
            expected_error(f"/api/scenarios/{sid}?country_id={country}", 404)
            assert call(baseline_path) == unchanged
    start = perf_counter()
    national = call("/api/warnings/summary?country_id=IN")
    national_seconds = perf_counter()-start
    assert len(national["by_region"]) <= 36
    expected_error("/api/warnings?country_id=IN&severity=invalid", 422)
    output = {"checks": "20 live scenarios; comparison, warnings, detail, summary, cross-country 404, unchanged baseline+forecast, discard 404; invalid severity 422", "records": records,
        "india_national_summary": national, "india_national_seconds": round(national_seconds, 4)}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    print("Saved", path, "national seconds", round(national_seconds, 3))


if __name__ == "__main__":
    main()
