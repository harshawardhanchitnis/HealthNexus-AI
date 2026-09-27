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

Forecast artifacts freeze the historical origin. Regenerate/rebuild/retrain and restart to advance it. Model metrics use the country target evaluation pool, not a claim of individual-facility accuracy. Inference never changes model weights. All runtime endpoints remain read-only.
