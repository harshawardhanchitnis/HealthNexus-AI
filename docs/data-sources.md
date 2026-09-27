# Data provenance

Reviewed on 2026-09-27.

| Source | URL / file | Fields / use | Classification | Access / import status |
| --- | --- | --- | --- | --- |
| National Portal of India, states/UTs and districts | https://www.india.gov.in/explore-india/facts-of-india/states-ut-districts | Administrative scope reference | Public reference | Accessed 2026-09-27; dynamic page, no machine-readable registry imported |
| Prototype geographic fixture | `data/metadata/india-regions.csv` | State/UT names, internal codes, selected district labels, regional centroids, macro-zones | Manually curated reference / illustrative sample | Authored 2026-09-27; district completeness/currentness not asserted; no official boundary data |
| HealthNexus generator | `backend/app/simulation/generator.py` | Fictional facilities, demand, beds, attendance, medicine stock, alerts | Synthetic / derived from synthetic | Seed 42; explicit snapshot date; no government health calibration |

The region list represents 28 states and 8 UTs. Coordinates are approximate illustrative centroids; facility points are synthetic jitter around these centroids and should not be used as actual routes. Internal state/district IDs are not official LGD identifiers.

## Public-data import procedure (future)

Obtain a dated export from the source publisher. Do not invent an API endpoint. Save the untouched file under `data/official/` with its source URL, license/terms, access date, release date, checksum, units and geographic identifiers recorded alongside it. Verify schema and reconcile administrative changes before using aggregates to calibrate the generator. Record coverage gaps explicitly.

Potential sources named by the original brief: MoHFW HMIS, data.gov.in healthcare datasets, IPHS and Indian essential medicine lists. These have not been downloaded or validated in this phase and are not presented as sources of the displayed values. No WHO/foreign-country data is required by the India-only scope.

For extending the illustrative sample, append district labels in `data/metadata/india-regions.csv`, separated by `|`, and regenerate. Keep this separate from an official complete district import. Names and codes must be stable and unique within each state/UT.
