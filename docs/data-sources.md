# Data sources and provenance

Public sources calibrate the prototype; all facility operations remain simulated. The following integrations were downloaded and normalized on **2026-09-27**, then verified from their offline caches.

| Dataset | Organization / country | URL | Format | Fields used | Source type | Usage note | Access date | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Health Dynamics of India 2022–23, published summary | MoHFW through PIB / India | [Release 2053070](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2053070) | HTML, cached factual paragraphs | 13 national facility/workforce totals, reference March 31, 2023 | official_public | Small factual extract attributed to MoHFW/PIB; no blanket open-data license asserted | 2026-09-27 | Integrated; cached; calibration |
| Hospital beds and medical doctors per 10,000 | WHO GHO / IN, BR, RU, CN, ZA | [OData documentation](https://www.who.int/data/gho/info/gho-odata-api), [API](https://ghoapi.azureedge.net/api/) | OData JSON | WHS6_102 and HWF_0001, country, year, numeric value; two latest non-null unstratified observations per indicator/country | public_international | [WHO data terms](https://www.who.int/about/policies/publishing/data-policy/terms-and-conditions); attribution and third-party exceptions apply | 2026-09-27 | Integrated; 20 cached observations; calibration |
| Geographic hierarchy | Project-curated India state/UT list, illustrative districts and foreign regions | Local metadata CSVs | CSV | Internal IDs, labels, illustrative coordinates and country relations | derived | Project-authored arrangement; not an official boundary or facility registry | Recorded in generated metadata | Integrated |
| Operational network | HealthNexus / all five nodes | Local generator | JSON | Fictional facilities, attendance, patient visits, syndrome counts, admissions, beds, stock ledgers and rule alerts | synthetic / derived | MIT project implementation; unvalidated simulation assumptions | Snapshot generation date | Integrated; 231 facilities |
| Emergency scenarios | HealthNexus | Not available yet | Planned | Future scenario deltas and event inputs | simulation | Not implemented | — | Planned |

## What the Indian source actually supplies

The PIB release dated September 9, 2024 summarizes Health Dynamics of India 2022–23. It reports 169,615 sub-centres, 31,882 PHCs, 6,359 CHCs, 1,340 sub-divisional hospitals, 714 district hospitals and 362 medical colleges. The same summary supplies seven workforce totals. The adapter extracts those two quantitative paragraphs and handles duplicated accessibility text. It does not import the full report or a real facility registry.

Calibration uses PHC doctor/nurse totals divided by PHC counts, CHC workforce totals divided by CHC counts, and pooled SDH+DH doctor totals divided by pooled hospital counts. These are national aggregate ratios, not individual facility staffing standards. The CHC source category combines specialists and medical officers. No HMIS API integration or OPD/IPD data ingestion is claimed.

## WHO selection and vintage

Each indicator request filters the five configured ISO3 countries and orders years descending. The adapter then retains two latest available non-null, unstratified numeric observations per country. Null values are skipped, never converted to zero. Pagination is supported; no undocumented API is invented. The cache retains original selected API records and their request URLs.

| Country | Latest bed-density year | Latest doctor-density year |
| --- | --- | --- |
| India | 2021 | 2024 |
| Brazil | 2021 | 2024 |
| Russia | 2023 | 2022 |
| China | 2023 | 2023 |
| South Africa | 2010 | 2024 |

Latest observations are not a same-year comparison. South Africa's bed indicator is particularly old. All values remain historical public indicators, even when used to generate a 2026 operational snapshot.

Attribution: World Health Organization, Global Health Observatory, hospital beds (WHS6_102) and medical doctors (HWF_0001), reference years retained in each record; country data for Brazil, China, India, the Russian Federation and South Africa; accessed September 27, 2026. Refer to WHO records for underlying source details. WHO terms permit relevant public-health uses subject to their conditions and third-party rights; commercial promotion and implied endorsement are excluded. WHO does not endorse HealthNexus AI. Project MIT licensing does not relicense WHO or government material.

## Reproduce and refresh

```powershell
.\.venv\Scripts\python.exe scripts\import_official_data.py
.\.venv\Scripts\python.exe scripts\import_official_data.py --source india_hdi --refresh
.\.venv\Scripts\python.exe scripts\import_official_data.py --source who_gho --refresh
.\.venv\Scripts\python.exe scripts\forecast.py generate --country all --days 540 --seed 42 --as-of 2026-09-27
.\.venv\Scripts\python.exe scripts\forecast.py build --country all
.\.venv\Scripts\python.exe scripts\forecast.py train --country all
.\.venv\Scripts\python.exe scripts\forecast.py evaluate --country all
```

Restart the backend after regeneration. These adapters intentionally select small subsets. The WHO API documentation describes queries for larger downloads; adapt the selection and review licensing before expanding. The PIB page links the underlying report; the current parser imports only its published summary. Endpoint or publication changes should fail clearly and require an adapter update, not silently create substitute official values.

Raw snapshots live under `data/official/india` and `data/official/who`; normalized records under `data/normalized`. Source hashes and schema validation catch corruption. Offline import needs no network. `GET /api/data-sources` returns 33 public observations, source metadata and calibration assumptions. A country filter narrows observations but keeps both source dependencies visible, because foreign calibration also borrows India's care-centre templates. Facility details expose the snapshot's frozen calibration inputs rather than claiming refreshed data changed an older snapshot.

## Provenance interpretation

`official_public`: India's dated government aggregates. `public_international`: WHO observations. `derived`: curated geography, ratios and rule calculations with input references. `synthetic`: all invented facility identities and operational values. `simulation`: reserved for explicit emergency scenarios; none exist yet.

Metadata includes source name/URL, access date, usage terms, geography, synthetic flag, methodology, version, input IDs and payload checksum where applicable. A synthetic value remains synthetic after public calibration. Missing public data is surfaced through assumption/fallback lists.

## Candidate sources not yet integrated

HMIS, data.gov.in downloads, IPHS/essential-medicines references, World Bank indicators and additional national open-data portals remain candidates. Their availability, fields, access terms and update mechanisms must be verified before adding adapters. No data from those candidates is presented as integrated here.
