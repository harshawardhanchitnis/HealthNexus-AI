# API — Phase 2

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
