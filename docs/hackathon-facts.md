# Verified pitch facts

Use these measured prototype facts. Do not convert WAPE to an “accuracy” percentage or describe simulated records as government inventories.

| Fact | Verified value | Source |
|---|---|---|
| India coverage | 36 states/UTs, 69 illustrative districts, 207 fictional facilities | [Phase 3 report](phase3-report.md), generated India snapshot; final verifier validates partitions |
| Other logical country nodes | Brazil, Russia, China, South Africa; 6 fictional facilities each | [Federation preparation](evaluation/phase7-prepare.json) |
| History | 540 days, seed 42, origin 2026-09-27 | [Phase 3 model card](model-card.md) |
| India operational test WAPE | Footfall 2.996932%; pooled medicine demand 3.079865%; admissions 3.344126% | [Measured comparisons](phase3-results.md), [India metrics](evaluation/IN.json) |
| Public caches | 2 source adapters; 13 MoHFW/PIB and 20 WHO observations | [Final verifier](evaluation/phase8-demo.json), [data sources](data-sources.md) |
| Positive Pune target / capacity | 41,763 / 17,745 accounting items | [Current Docker acceptance](evaluation/phase8-docker.json) |
| Positive transfer / lanes | 15,679 accounting items / 10 lanes | Same report; heterogeneous medicine units, not interchangeable supplies |
| Positive unresolved | 26,084 | Same report; receiver target, not necessarily expected unmet demand |
| Expected unmet medicine demand | 27,655.2181 → 17,378.1980 | Same report; point-forecast quantities, pooled for accounting |
| Donor violations / new risks | 0 / 0 | Same report; protected across all 500 sampled paths |
| Critical receiver medicine warnings | 7 → 0 | Same report; excludes other operational warning domains |
| Maximum receiver resource risk | 100% → 100% | Same report; not all shortage/risk is solved |
| Greedy comparison | District OR-Tools and greedy tie | [Preserved optimization report](phase55-report.md) |
| Constrained Pune | Capacity 0; transfers 0; target unresolved 30,230 | [Current Docker acceptance](evaluation/phase8-docker.json) |
| FedAvg | 5 logical nodes, 5 rounds, 1 epoch/round, 417 float32 parameters | [Accepted run](evaluation/phase7-run.json) |
| Federation validation WAPE | 100%, 15.95%, 9.97%, 9.51%, 9.37%, 9.33% | Same report; validation, not held-out test |
| Federation global test WAPE | 8.9472% | Same report; experimental MLP, not a comparison against operational HGB |
| India local vs federated WAPE | 8.9496% → 8.9511%; degradation +0.0015 percentage points | Same report; retained without test-driven tuning |
| Accepted federation run | 4.8011 s; 614,235 logical serialized boundary bytes; raw rows shared 0 | Same report; same-process experiment, not international network timing |
| New Linux federation verification | 2.4401 s training; 3.5283 s full HTTP workflow; 614,356 bytes | [Docker acceptance](evaluation/phase8-docker.json); last-bit checkpoint differences reported, original experiment retained |
| Backend tests | 340 passing (8 new readiness/saved-evidence tests) | [Final technical report](final-technical-report.md) |
| Production frontend | 370.25 kB initial / 101.28 kB estimated transfer | Final Angular production build |
| Gemini requests this task | 0 | Transport prohibition in final verifier; Compose disabled/unconfigured; ledger remains 12 |
| Public deployment | None | [Deployment decision](deployment.md) |

## Claims audit

Approved wording: **decision-support prototype**, **national-scale prototype architecture**, **Calibrated Simulated Operations**, **Official Public Data**, **model-based Estimated Stock-Out Risk**, **five configured logical country nodes**, **experimental Global Federated Model**.

Rejected wording: live nationwide government network, all Indian hospitals, outbreak/diagnosis prediction, clinically validated forecasting, guaranteed donor/patient safety, inherently private federation, 100% accuracy, Google Cloud/Firebase already deployed, every participant improved, Gemini successfully live accepted.

Google OR-Tools is implemented and measured. The Gemini API layer is implemented but real-provider acceptance remains blocked. Firebase Hosting / Cloud Run are **deployment targets**. Firestore is an existing unverified opt-in snapshot adapter, not a durable workflow implementation.
