# Federated footfall learning — Phase 7

HealthNexus demonstrates federated predictive learning across five configured BRICS country nodes. Each country trains locally on its own simulated operational history; only model parameters and aggregate metadata are sent to the federation service. India retains its detailed showcase; Brazil, Russia, China and South Africa are representative nodes with six fictional facilities each. This is local prototype infrastructure, not connected government systems or an exhaustive list of BRICS members.

## Separate experimental model

Operational forecasting remains the existing country-local HistGradientBoosting/selected baseline engine. Trees are not parameter-averaged. The separate collaboration model uses **PyTorch 2.8.0 CPU**, `16 → Linear(16)/ReLU → Linear(8)/ReLU → Linear(1)`: **417 learned float32 parameters**, 1,668 parameter bytes. The last layer is linear; evaluation clips negative predicted footfall to zero. The seed-42 untrained model predicts nonpositive values in this dataset and measures 100% initial WAPE; this result is retained, not substituted with a trained baseline.

No Phase 3 weights, operational snapshot, scenario, safety reserve or optimizer policy is updated by federation. It is not a deployable replacement for the operational engine. The local-only comparator is this same MLP, not the operational HGB champion.

## Local data, features and temporal evaluation

Each logical `FederatedClient(country_id)` owns a `CountryDataLoader` restricted to `data/generated/training/<country>/manifest.json` and `footfall.npz`. It verifies country identity, source schema, table hash, finite values, positive scales, origin-before-target and separated target-day partitions. Resolving another country's directory, redirected file or requesting another country through the loader is rejected. This is a software boundary, not OS sandboxing: the prototype runs in one process and the host still has access to its files.

Phase 3's existing footfall tables derive from **540-day simulated/calibrated histories**. No new facilities, histories, public-source imports or raw global training table are generated. Operational inventory profiles have identical historical footfall inputs, so federation explicitly uses the preserved source-history tables independently of inventory profile. Country/table/history hashes, origin and temporal windows remain in node metadata.

The common 16 inputs are:

| Inputs | Transformation |
|---|---|
| Forecast horizon | horizon / 14, direct daily horizons 1–14 |
| Target weekday | sine and cosine of 2π × weekday / 7 |
| Annual phase | existing sine/cosine of forecast date |
| Trend | existing years-since-history-start / 2 |
| Past demand | lag 1, lag 7, lag 14 / past-28-day scale |
| Recent demand | mean 7, mean 14, std 28 / past-28-day scale |
| Recent growth | preceding mean-7 ratio against the earlier mean-7, minus 1 |
| Facility type | three common one-hot roles: primary, community, hospital |

Target = daily footfall / `max(1, preceding 28-day mean at the frozen forecast origin)`. Predictions are scaled back to **visits** locally. This handles country/facility size differences without sending normalization rows, facility-level scales or fitted scaling statistics. Shared normalization formulas and feature order are fixed in advance. Features never read post-origin demand; target weekday/date are known calendar values.

Chronological training uses Phase 3 split 0; per-round validation uses its selection window (split 1). Split 2 remains unused by federation; test uses split 3, untouched by training, weight/policy/epoch selection. Test metrics are evaluated for initial, independent local-only and final global models under fixed settings. The local-only model receives `rounds × local_epochs`, with the same per-round deterministic shuffles, before being reset to initial weights for federation. This matches local epoch exposure, not optimizer-step count across differently sized nodes. Forecast-origin/horizon examples overlap in time and are not IID patient records.

## Genuine FedAvg

Every client receives identical initial tensors. Each round starts from the latest global tensors, performs local SGD and exports a strict `ClientUpdate`. The default is standard sample-weighted FedAvg:

`w_global = Σ (n_country / Σ n_country) × w_country`

The aggregator averages **actual named parameter arrays**, accumulating in float64 and distributing float32 tensors. It does not average predictions or accuracy numbers. The optional `balanced-country` policy uses equal weights and is explicitly labelled; it never silently replaces standard FedAvg. Default India weight is 89.6062%, each foreign node about 2.5985%, reflecting the prototype's substantial imbalance.

Defaults: five rounds, one local epoch, seed 42, minibatches of 1,024, SGD learning rate 0.03, no momentum, two CPU threads, deterministic algorithms. UI/API permit 1–10 rounds and 1–5 epochs. Settings were fixed before held-out evaluation and are not tuned to guarantee improvements.

Every update is revalidated after serialization: participant set/unique country, positive sample count, model version, round, starting global checksum, exact names/shapes, finite float32 values, parameter checksum and exact byte count. Unknown fields are forbidden. The deterministic equation test checks `[1,2]` with 100 examples plus `[3,4]` with 300 examples gives `[2.5,3.5]`.

## Exactly what crosses boundaries

- Downlink: named float32 global parameters, model version, round and checksum.
- Uplink: locally trained parameters, country, round, training sample count, version, starting/final parameter checksums, parameter count/bytes, measured serialized bytes, local epochs/losses/time and aggregate validation metrics.
- Separate aggregate metadata: country preparation summary and initial/local-only/final test and per-round global validation metrics, including counts and summed absolute/squared errors/target totals. Aggregate source hashes, windows and facility counts are disclosed.

**Raw operational records shared: 0.** There are no footfall rows, inventory rows, individual records, feature matrices, labels, per-example scales or raw batches in the update contract, aggregator input or run response. The aggregator imports no data loader or client. The coordinator invokes local client methods and receives only serialized DTOs and aggregate metadata; it never concatenates countries' training arrays. Client-local arrays remain private to clients in this process.

Every round records `raw_records_sent = raw_records_shared = 0`. This follows the enforced packet contract and actual code path, not a privacy claim about arbitrary malicious clients. JSON UTF-8 **update bytes** are computed from the exact serialized DTO sent, including metadata; **parameter bytes** are the float32 tensor payload. Downlink bytes count actual serialized global packets delivered to each client, including initialization/reset and final reload distribution. Aggregate metadata bytes are counted separately. Total logical boundary bytes = uplink + downlink + aggregate metadata. These are in-process serialization counts, not a real cross-border network capture; TLS/network overhead is not included. Timings in packets mean serialized byte totals can vary slightly across otherwise numerically deterministic runs.

Global MAE/RMSE/WAPE are reconstructed from locally computed counts and error sums; **WAPE is total absolute error / total actual visits**, not the mean of countries' WAPEs. Normalized MAE is also reported. Per-round tables use validation, while final comparison uses held-out test; neither is classification accuracy.

## Storage, API and commands

Install the optional CPU training runtime from the official PyTorch wheel source. Existing backend requirements stay unchanged:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-federation.txt
.\.venv\Scripts\python.exe scripts/federate.py prepare --output docs/evaluation/phase7-prepare.json
.\.venv\Scripts\python.exe scripts/federate.py run --rounds 5 --local-epochs 1 --seed 42 --output docs/evaluation/phase7-run.json
.\.venv\Scripts\python.exe scripts/federate.py evaluate --report docs/evaluation/phase7-run.json --output docs/evaluation/phase7-reload-evaluation.json
.\.venv\Scripts\python.exe scripts/federate.py report --report docs/evaluation/phase7-run.json
```

The Windows CPython 3.13 CPU wheel downloaded on this machine was about 619 MB; the trained model is small despite that runtime footprint. The regular operational backend can start without PyTorch; federation reports runtime unavailability and training is rejected until installed. The existing Docker image does not install this optional extra; container federation remains unverified.

`prepare` validates and reports existing local tables; it does not retrain HGB or regenerate data. `run` trains the five clients plus independent local comparators and saves the report. `evaluate` reloads the final numeric model and verifies source-table identity and aggregate test metrics (float tolerance rtol 1e-6, atol 1e-8 for CPU inference reductions). Parameter checksum/save-reload comparison is exact. `report` reads a saved report. There is no public model-download endpoint.

Artifacts live separately at `artifacts/federation/runs/<UUID>/global/{initial,final}` and `country/<code>/{local-only,latest-local}`. Numeric NPZ parameters load with `allow_pickle=False`; a version/feature/checksum manifest accompanies each. A checksum detects corruption, not a malicious trusted-host replacement. Run reports contain aggregate results and artifact references, never training data.

| Endpoint | Behavior |
|---|---|
| GET `/api/federation/status` | runtime availability, policy/model, active run, privacy limitations |
| GET `/api/federation/nodes` | five locally validated preparation summaries; no raw arrays |
| POST `/api/federation/runs` | strict request, HTTP 202, actual background training |
| GET `/api/federation/runs/{id}` | progress/events, rounds and measured results |
| GET `/api/federation/runs/{id}/rounds` | exact round table |
| DELETE `/api/federation/runs/{id}` | rejects active run; removes retained run and its experiment artifacts |

One active run per service; CPU training is serialized across service instances. Store retains at most eight runs, evicting completed/failed runs and their artifacts. API retention is process-local; restarting loses lookup/progress even though completed saved artifacts remain on disk. CLI runs are saved experiments outside the API session index and are not automatically pruned by the API. Administrative authentication, durable queues and multi-worker coordination are not implemented. No fake progress delays are added; UI polls actual backend state and preserves events that occur between polls.

## Privacy and operational limitations

Raw operational training records remain local in this prototype; model parameters and aggregate metadata are exchanged. **Federation does not guarantee privacy.** Model updates and aggregate statistics can leak information. Differential privacy, secure aggregation, encrypted network transport, adversarial-client defenses and government connectivity are not implemented. Production deployment needs stronger privacy/security controls, authenticated country clients and transport isolation.

Foreign-node performance uses six representative facilities each. Shared simulator regularities and unequal sample counts can make collaborative learning appear substantially easier than real heterogeneous operations. No clinical or international real-world generalization is established. The global model is experimental; current application forecasts, warnings, scenarios and OR-Tools remain authoritative and domestic.

## Gemini compatibility

Phase 6 status remains: **Implementation complete; live provider acceptance pending due to Gemini service availability.** No live Gemini calls, credential changes, billing changes or failover redesign occur in Phase 7. The 13 tools, declarations, system prompt, response schemas, orchestration/failover and verifier are untouched. Future read-only `get_federation_status` and `get_federation_results` adapters exist on the federation service, but are deliberately not registered as Copilot tools.

The current Phase 6 verifier hashes **all** backend application Python files. Adding the isolated federation modules and necessary main-router registration therefore changes that broad implementation digest even though Copilot code/tool identities remain byte-identical. Its conservative invalidation remains intact; old evidence is preserved without rebinding or rewriting. There was no complete live PASS to invalidate. A later authorized live run records the new broad identity while retaining the existing cumulative ledger and historical provider failures.

See [actual results and validation](phase7-report.md), [PyTorch CPU installation](https://pytorch.org/get-started/previous-versions/) and [PyTorch module parameter documentation](https://docs.pytorch.org/docs/stable/notes/modules.html).
