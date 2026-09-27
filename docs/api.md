# API — through Phase 3

FastAPI exposes interactive documentation at `/docs`. All routes are read-only. Network routes accept `country_id=IN|BR|RU|CN|ZA`, defaulting to India for compatibility.

| GET route | Behavior |
| --- | --- |
| `/api/health` | Selected snapshot date, storage mode and synthetic operations flag |
| `/api/countries` | Five configured nodes, coverage labels, domestic redistribution scope, federation not implemented |
| `/api/data-sources` | Public source catalog, normalized records, provenance and current calibration preview; optional country filter |
| `/api/regions` | Country regions and optional India districts |
| `/api/overview` | Summary, history, region index, alerts, calibration and honest coverage |
| `/api/facilities` | Paginated/searchable country-scoped list |
| `/api/facilities/{id}` | Facility histories, stock ledgers, alerts, provenance registry and frozen calibration inputs |
| `/api/inventory` | Aggregated stock/consumption/reserve flags |
| `/api/alerts` | Rule-based resource alerts |

`state_id` remains the region-filter query name for backward compatibility. India also supports `district_id`. Facility lists accept `search`, `status`, `offset` and `limit` (1–250); alerts accept `severity`. Scope validation rejects foreign regions/facilities with 404 and unknown country codes with 422. Storage failures return 503. There is no cross-country aggregate operational endpoint.

Examples: `/api/overview?country_id=BR&state_id=BR-SP`, `/api/overview?state_id=MH&district_id=MH-PUNE`, `/api/data-sources?country_id=ZA`.

The sources endpoint keeps the full integrated source catalog visible even when records are country-filtered, because calibration has cross-country public aggregate dependencies. Its current preview may differ from a previously generated facility's frozen inputs. Public records carry reference years; synthetic snapshots carry explicit `as_of` dates. No training, transfer, Gemini or optimization write endpoint exists in Phase 2.

## Forecasting

All forecast responses use typed Pydantic schemas. Country defaults to `IN`. `horizon` accepts only 1, 7 or 14 (default 14); invalid values return 422. Unknown/cross-country facilities and unknown medicines return 404. Missing, stale or corrupt model artifacts return 503 with a clear unavailable state. No fallback silently manufactures predictions.

| GET route | Response |
| --- | --- |
| `/api/forecasts/facilities/{id}/footfall` | Historical and future patient demand, daily intervals, summaries, provenance and metrics |
| `/api/forecasts/facilities/{id}/medicines/{medicine_id}` | Requested medicine demand plus full 14-day stock trajectory and calculated probabilities |
| `/api/forecasts/facilities/{id}/beds` | Requested admissions, including unserved admission demand; not occupied-bed predictions |
| `/api/forecasts/facilities/{id}/stockout-risks` | All five medicine forecasts/intelligence for a facility |
| `/api/models/forecasting/metrics` | Country-local comparisons, champions, temporal windows and interval coverage |

Example: `/api/forecasts/facilities/IN-MH-PUNE-001/medicines/IVF?country_id=IN&horizon=7`. Medicine stock intelligence always uses a 14-day projection so its 3/7/14-day probabilities remain comparable when the chart horizon changes. Probabilities are fractions (0–1). Null crossing dates mean no crossing within the horizon; cover is null for zero predicted demand. The `/beds` target is labelled admissions requested in the UI.

Forecast artifacts freeze the historical origin. Regenerate/rebuild/retrain and restart to advance it. Model metrics use the country target evaluation pool, not a claim of individual-facility accuracy. Inference never changes model weights. Phase 3 forecast endpoints remain read-only; Phase 4 adds isolated scenario creation/discard below.

## Phase 4 scenario and warning API

Scenario results are isolated copies. Runtime writes create/discard process-local scenario records; they do not alter baseline snapshots or model artifacts. All scenario IDs are country scoped; supply `country_id` on reads/deletes. Store capacity is 20 completed runs and a server restart clears it.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/scenarios/presets` | Four typed scenario presets and numeric effects |
| POST | `/api/scenarios` | Create/run, returns 201 with full paired result |
| GET | `/api/scenarios?country_id=IN` | Metadata for retained runs |
| GET | `/api/scenarios/{id}?country_id=IN` | Retrieve retained result |
| GET | `/api/scenarios/{id}/comparison?country_id=IN` | Full baseline/scenario comparison |
| DELETE | `/api/scenarios/{id}?country_id=IN` | Discard, returns 204; subsequent reads return 404 |
| GET | `/api/warnings` | Sorted warnings and matching summary |
| GET | `/api/warnings/summary` | Geographic/severity aggregation |
| GET | `/api/warnings/{id}` | Structured facts, provenance and severity transition |

Warning list/summary filters: `country_id`, `state_id`, `district_id`, `facility_id`, `severity` (INFO/WATCH/WARNING/CRITICAL), `warning_type`, `category` (medicine/demand/beds/personnel/emergency), `scenario_id`. Omit scenario ID for baseline warnings. Detail supports country/scenario/facility scope. Invalid enums/parameters return 422; unknown/cross-scope geography or discarded runs return 404; missing/stale saved forecasts return 503. Store-full and invalid event windows return 422 with actionable messages.

```json
{
  "scenario_type": "DENGUE_SURGE",
  "country_id": "IN",
  "state_id": "MH",
  "district_id": "MH-PUNE",
  "facility_ids": [],
  "severity": "severe",
  "duration": 14,
  "seed": 42,
  "parameters": {}
}
```

Optional `start_date` must be after the saved origin, with the entire 1–14-day event inside the next 14 days. Other scenario types are DELIVERY_DELAY (`medicine_id`, `delay_days`), STAFF_SHORTAGE (`unavailable_fraction`), FACILITY_DISRUPTION (`capacity_reduction`). Fractions are 0–1, strictly greater than zero. Delay is 1–30 days. Unknown or inapplicable fields are rejected.

Response includes `scenario`, `baseline`, `scenario_result`, `delta`, `resource_impact`, `baseline_warnings`, `warnings_created`. Stock probabilities use fractions; resource-impact risk comparisons explicitly use percentages/percentage points. Maximum risk is a maximum across facilities, not the probability of a network event. Zero capacity yields null ratios and explicit unmet demand/overflow. A null date means no point-trajectory crossing within 14 days. Scenario uncertainty is conditional on fixed assumptions; no outbreak model is trained.

The [Phase 4 report](phase4-report.md) defines exact equations, thresholds and limitations. Interactive OpenAPI is available at `/docs`.
