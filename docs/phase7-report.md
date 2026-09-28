# Phase 7 measured federation report

28 September 2026. Genuine local MLP training and parameter FedAvg implemented across the five configured logical country nodes. The operational engines remain unchanged. **Raw operational training records shared: 0.** Phase 6 status: **Implementation complete; live provider acceptance pending due to Gemini service availability.** Zero live Gemini requests were made during Phase 7; the cumulative verifier ledger remains 12.

## Model and run

- Framework: PyTorch 2.8.0+cpu CPU.
- Architecture: 16 → Dense(16)/ReLU → Dense(8)/ReLU → Dense(1); **417 parameters / 1,668 float32 parameter bytes**.
- Task: direct daily patient-footfall forecasting, horizons 1–14, normalized by the pre-origin 28-day mean (minimum 1), rescaled to visits locally.
- Inputs: 16 common calendar/horizon/trend, lag/recent-demand ratio/growth and three facility-role features. Full schema, normalization, splits and boundary contract: [federated learning](federated-learning.md).
- Five rounds, one epoch each, seed 42, sample-weighted FedAvg. SGD LR 0.03, batch 1,024, two CPU threads; fixed before test evaluation. Clients receive the same initial checksum and each round's global checksum before training.
- Standard formula: `Σ (n_country / Σ n_country) × trained_country_parameters`. India weight 89.6062%; each other node 2.5985%. Balanced-country averaging is implemented, explicitly separate and equation-tested, but these measurements use standard FedAvg.
- Run ID: `fdbaaedb-773d-4b67-be50-ad406b130950`. [Complete measured run](evaluation/phase7-run.json), [local preparation](evaluation/phase7-prepare.json), [independent saved-model evaluation](evaluation/phase7-reload-evaluation.json).

## Held-out results

| Country | Train / validation / test examples | Local-only test WAPE | Initial-global WAPE | Federated-global WAPE | Change | Latest update bytes |
|---|---:|---:|---:|---:|---|---:|
| India | 139,524 / 11,592 / 11,592 | 8.9496% | 100.0000% | 8.9511% | degraded (+0.0015 pp) | 9,611 |
| Brazil | 4,046 / 336 / 336 | 26.7746% | 100.0000% | 8.7975% | improved (-17.9772 pp) | 9,597 |
| Russia | 4,046 / 336 / 336 | 28.3658% | 100.0000% | 9.0454% | improved (-19.3204 pp) | 9,604 |
| China | 4,046 / 336 / 336 | 28.3849% | 100.0000% | 8.9523% | improved (-19.4326 pp) | 9,608 |
| South Africa | 4,046 / 336 / 336 | 27.1055% | 100.0000% | 8.8088% | improved (-18.2967 pp) | 9,613 |

The independent local-only MLP receives five total local epochs, the same exposure as each federated client. Larger countries perform more SGD batches per epoch. These are forecast-origin/horizon examples, not unique patients or independent raw daily records. All sources are 540-day simulated/calibrated country histories. India has 207 fictional facilities; every other node has six. There is no manufactured foreign-facility expansion or test-driven hyperparameter tuning.

Four representative foreign nodes improve, while India's test WAPE worsens by **0.0015 percentage points**. No outcome is hidden. The initial model's nonpositive predictions clip to zero and measure 100% WAPE. Global final test WAPE is **8.9472%**, MAE **30.5503 visits**, RMSE **53.4988 visits**, across 12,936 test examples. These results are not clinical accuracy or an improvement claim over operational HGB forecasts. Shared simulation patterns and unequal local training counts limit external validity.

## Rounds, bytes and performance

| Round | Global validation WAPE | Global MAE (visits) | Uplink update bytes | Raw records sent |
|---|---:|---:|---:|---:|
| 0 | 100.0000% | 292.3346 | 0 | 0 |
| 1 | 15.9527% | 46.6353 | 48,053 | 0 |
| 2 | 9.9723% | 29.1525 | 48,083 | 0 |
| 3 | 9.5148% | 27.8149 | 48,027 | 0 |
| 4 | 9.3651% | 27.3775 | 48,009 | 0 |
| 5 | 9.3282% | 27.2694 | 48,033 | 0 |

Per-round metrics are chronological validation, not held-out test. Global WAPE is reconstructed from country-level summed absolute error and summed actual visits, never a mean of final country metrics passed off as FedAvg.

Final CLI run: **4.8011 seconds** including local loading, independent comparators, federation, local evaluations and model save/reload within the training function; CLI process import/startup overhead is separate. Initial exploratory five-round run took 5.6142 s and had identical final metrics. Final API run took **5.4660 s**; final browser run **3.9965 s**. These are workstation measurements, not production load tests; all measured five-round runs were below the 30-second demonstration target.

- Uplink: **240,205 bytes** of actual serialized updates, including parameters/training/validation metadata.
- Downlink: **360,045 bytes** of actual serialized global packets delivered to clients, including initial/reset and final reload distribution.
- Other aggregate metadata: **13,985 bytes**.
- Total logical boundary traffic: **614,235 bytes**. API and browser totals are 614,241 and 614,237; timing metadata causes small serialization-size variation despite identical tensors/metrics.
- Experiment artifacts for the retained CLI run: **112,624 disk bytes** including report and initial/final/local-only/latest-local numeric checkpoints. Model files are saved under the ignored `artifacts/federation/` tree, separate from Phase 3 models.

Byte counts measure in-process UTF-8 wire DTOs and numeric tensor payloads, not actual international packets or TLS overhead. Each update's raw-record count is zero because the strict update contract and executed path contain no operational records, feature matrices, labels, batches or per-example scaling rows. Both `raw_records_sent` and `raw_records_shared` are zero in every round.

## Validation

- **332 full backend tests pass**: all prior 289 plus **43 federation cases**. Final full run: 105.63 s. Tests prove actual `[1,2]`/100 + `[3,4]`/300 parameter averaging equals `[2.5,3.5]`, sample/equal weighting, shared initialization, real local weight changes, seed determinism, strict raw-data boundary, country isolation, malformed shapes/NaN/overflow/version/round/checksum rejection, byte counts, evaluation, numeric save/reload, bounded store and API/delete behavior. Operational model/snapshot sentinel files remain unchanged during training tests.
- Python compilation and `pip check` pass. Optional CPU PyTorch installed without changing existing backend requirements or Gemini dependencies.
- `prepare`, default five-round `run`, independent `evaluate`, and saved `report` CLI commands pass. Numeric parameter reload checksum is exact; aggregate inference checks tolerate CPU floating-point reductions (rtol 1e-6, atol 1e-8).
- [Actual local API smoke](evaluation/phase7-live-api.json): 202 background training, real progress observed, five nodes, exact rounds GET, invalid request 422, DELETE 204 and subsequent 404. No raw training data in API responses.
- [Desktop/mobile browser evidence](evaluation/phase7-browser.json): Run Federated Training triggers real work, honest metrics and precise slight degradation render; 390×844 mobile document/body width 375, tables scroll internally, zero console errors/warnings. Temporary viewport reset. [Desktop](screenshots/phase7-desktop.png), [results](screenshots/phase7-desktop-results.png), [mobile](screenshots/phase7-mobile.png).
- [Preservation and security](evaluation/phase7-preservation.json): all **115 protected files** byte-identical, including existing Copilot/forecast/scenario/optimizer source and generated/model artifacts. The 13-tool declaration hash and system-prompt hash are unchanged. Existing ledger is 12 before/after; no live provider call, key/billing/project change or ledger reset. `.env` remains ignored/untracked; source/report/frontend/diff credential scan is clean.

The pre-existing Gemini verifier hashes every backend application module. Necessary isolated federation files/main-router changes therefore change its broad implementation identity; conservative invalidation is preserved. Copilot files, tool schema, response schemas, prompt, failover and verifier remain untouched; no historical evidence is rewritten or rebound. Future federation read adapters are prepared but **not registered** with the existing Copilot. There was no complete live Gemini PASS to invalidate.

## Privacy and next step

Raw operational training records remain local in this prototype; model parameters and aggregate metadata are exchanged. Model updates can leak information. No secure aggregation, differential privacy, encrypted network transport, adversarial-client defense, production authentication or connected national government nodes are implemented. The aggregator is local prototype infrastructure and storage is bounded/process-local. Physical redistribution remains domestic; the experimental global model does not replace authoritative operational forecasts.

**Phase 7 local prototype acceptance passes and is ready for final integration/polish and deployment preparation.** Deployment itself remains unverified and is not initiated here. Gemini live acceptance retains its external availability blocker; it is not declared passed. See [reproducible demo](demo-script.md).
