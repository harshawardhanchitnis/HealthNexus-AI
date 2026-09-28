# HealthNexus AI — final technical report

Verified 2026-09-28. Phase 8 integrates the existing decision-support prototype and verifies its local Docker demonstration. No cloud deployment, billing change or live Gemini request was performed. The operational engines and accepted Phase 7 experiment remain unchanged.

## Product and architecture

The Command Centre shows current medicine, bed and workforce conditions, projected warning counts, geography, operational profile and provenance. Guided Demo selects actual Pune inputs and links Network → Forecast → Dengue → Warnings → Redistribute → Federation → Offline summary. Switching between redistribution-ready and constrained demonstrations clears old scenario/plan context. Engines calculate every result. Expired plans offer recovery through a new scenario.

Angular provides the administrator interface. FastAPI validates geography, profile and request schemas. Official observations feed documented calibration; simulated facility ledgers feed operational forecasts, sampled stock paths, warning evaluation, emergency projections and Google OR-Tools. Gemini is an optional orchestration layer above these authoritative tools. A separate experimental country-local PyTorch branch exchanges parameters through FedAvg. See the [architecture diagram](architecture.md).

## Data, models and provenance

India contains 207 fictional facilities across all 36 states/UTs and 69 illustrative districts. Brazil, Russia, China and South Africa each have six representative fictional facilities. These are five logical prototype nodes, not live government connections. Operational history contains 540 days, seed 42, origin 2026-09-27. Two integrated source adapters preserve 13 MoHFW/PIB and 20 WHO public aggregate observations, their years, units and publisher URLs. See [source methodology](data-sources.md) and [model card](model-card.md).

The final verifier checks all ten country/profile partitions, facility hashes, forecast artifacts, optional planning caches and accepted federation checkpoint/table identities. Inventory profiles remain explicit and isolated. No snapshot regeneration, retraining or test-driven tuning was needed for this integration.

Operational forecasting remains the existing saved pipeline, with temporal holdouts, baseline comparisons and uncertainty evaluation. India held-out WAPE: footfall **2.996932%**, pooled medicine demand **3.079865%**, requested admissions **3.344126%**. These are simulated operational prediction results, not clinical accuracy or outbreak prediction. [Original measured results](phase3-results.md).

Early warnings use the existing deterministic rules and model-based stock-out estimates. The Emergency Digital Twin applies a documented demand shock to an immutable baseline. Stock/receipts/consumption remain conserved; scenario provenance and model identity remain bound to country/profile. Five hundred sampled paths support estimated stock-out risks and donor protection. Clinical, transport and real inventory validity are not claimed.

## Reproduced Pune severe-dengue results

Both use India → Maharashtra → Pune, severe dengue, 14 days, seed 42 and district donor search. Values are freshly computed by actual engines, not saved optimizer answers. Mixed medicine quantities below are accounting items; tablets, bags, capsules and sachets are not interchangeable.

| Measured quantity | Redistribution-ready | Constrained |
|---|---:|---:|
| Receiver target before | 41,763 | 30,230 |
| Safe donor capacity | 17,745 | 0 |
| Transferred accounting items | 15,679 | 0 |
| Transfer lanes | 10 | 0 |
| Remaining receiver target | 26,084 | 30,230 |
| Expected unmet medicine demand before | 27,655.2181 | 17,075.1558 |
| Expected unmet medicine demand after | 17,378.1980 | 17,075.1558 |
| Critical receiver medicine warnings | 7 → 0 | 0 → 0 |
| Maximum individual resource stock-out risk | 100% → 100% | 100% → 100% |
| New donor risks / protection violations | 0 / 0 | 0 / 0 |
| Solver status | OPTIMAL | OPTIMAL |

The constrained case still has warning-level shortages despite zero critical medicine warnings. OR-Tools and nearest-safe-donor greedy tie in both district demonstrations. Remaining shortages stay visible. Donors retain the existing protection policy; no reserve, objective or inventory was changed to manufacture a result. Conservation and baseline/model immutability pass. [Current Docker acceptance](evaluation/phase8-docker.json), [canonical verifier](evaluation/phase8-demo.json), [preserved detailed comparison](phase55-report.md).

## Gemini architecture and exact status

**Implementation complete; live provider acceptance pending due to Gemini service availability.**

The existing official SDK / Interactions API / native function-calling layer retains 13 authoritative tools, structured responses, evidence validation, model stickiness, safe local rehydration and a total model-aware request budget. The configured default order remains 3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite. Availability failover does not hide tool/application/evidence defects. Historical live attempts returned HTTP 503 HIGH DEMAND; no model has passed real-provider acceptance.

**Zero live Gemini requests during Phase 8.** The retained verification ledger remains 12. Compose disables Gemini and passes no API key. Readiness never invokes inference. Missing-key behavior is checked with live mode enabled but an empty key and a transport that raises if invoked. The UI defaults to explicitly labelled OFFLINE deterministic summaries; this is not Gemini and is not an automatic provider failover. [Gemini documentation](gemini.md), [retained Phase 6 report](phase6-report.md).

## Genuine federation, preserved evidence

The accepted seed-42 five-round, one-epoch-per-round sample-weighted FedAvg experiment uses 417 float32 MLP parameters and five logical country clients. Actual CPU training took **4.8011 s** and exchanged **614,235 logical serialized boundary bytes**, with **zero raw operational training rows shared**. Global held-out test WAPE is **8.9472%**. Validation progression is 100% → 15.95% → 9.97% → 9.51% → 9.37% → 9.33%.

India's local-only WAPE **8.9496%** versus federated **8.9511%** remains visible: degradation of approximately **0.0015 percentage points**. All four representative foreign nodes improve against their local-only MLP comparison. No comparison is claimed against the operational forecasting model. [Accepted report](evaluation/phase7-run.json).

The original numeric checkpoint/report is now packaged as small canonical public demonstration assets. `/api/federation/saved-demo` validates report and parameter integrity, metric arithmetic, completion and model version; it neither trains nor fabricates results. The UI labels it SAVED MEASURED RUN. It survives a container restart. Newly started run indexes remain process-local.

Actual Linux container training was also verified: **2.4401 s** training, **3.5283 s** HTTP workflow and **614,356 bytes**. Linux checkpoint bytes differ from the accepted Windows experiment, while measured metrics agree within declared numeric tolerance. The original experiment was not replaced or relabelled. [Reload evaluation](evaluation/phase8-federation-reload.json), [Docker comparison](evaluation/phase8-docker.json).

Raw training records remain at each simulated node; parameters and aggregate metadata cross the boundary. Secure aggregation, differential privacy, adversarial-client defenses and encrypted federation network transport are not implemented. Updates can leak information. This same-process experiment does not inherently guarantee privacy. [Full federation boundary](federated-learning.md).

## Measured performance

These are local single-run observations, not load benchmarks or cloud guarantees. HTTP timings include local preparation/serialization. UI journey timing, if retained in browser evidence, includes automation overhead and is not a browser performance metric.

| Docker flow | Measured seconds |
|---|---:|
| Command Centre overview API, ready Pune | 0.150 |
| Facility IVF forecast API | 0.159 |
| Severe 14-day scenario | 1.579 |
| Scenario warnings API | 0.032 |
| District redistribution | 0.156 |
| Offline local summary | 0.048 |
| Five-round federation training / HTTP flow | 2.440 / 3.528 |
| Backend restart to liveness | 4.607 |
| Cached readiness | 0.020 |

The earlier uncached Docker readiness check took 1.657 s. Capability results cache for 30 seconds; liveness avoids loading datasets. Existing planning caches and immutable projections remain intact. No micro-optimization or operational model redesign was introduced. [Timing evidence](evaluation/phase8-docker.json), [startup observation](evaluation/phase8-container-startup.json).

The final Windows TestClient verifier was slower: app startup after imports 0.985 s, uncached readiness 7.618 s, ready overview 0.456 s, scenario 4.880 s, optimization 0.518 s and offline summary 0.080 s. These distinct measurements remain in the canonical verifier report; they are not substituted for the Docker HTTP observations above. Host contention and environment affect latency, so no instant cold-start promise is made.

## Validation and failure modes

- **340 backend tests pass**, 54.88 s; all previous 332 retained, eight readiness/saved-artifact tests added. One existing upstream Starlette/AnyIO deprecation warning remains.
- Python compilation and Windows/container `pip check` pass. Strict TypeScript and Angular production build pass: **370.25 kB initial**, **101.28 kB estimated transfer**. Production npm audit reports zero known vulnerabilities; this is not a security guarantee.
- Actual Docker build/up, forecast loading, both profile scenarios, real OR-Tools, real five-round federation, explicit offline Copilot, saved artifact reload and backend restart pass.
- The canonical demo verifier passes without Gemini. Missing key, invalid country/profile, malformed bodies, empty filters, scenario reset, cross-country lookup and unchanged assets are checked. Regression tests cover stale forecasts/caches, provider outages, evidence failures, protected donors and incompatible profiles. Missing/corrupt saved federation evidence returns a clean unavailable result.
- Desktop and 390×844 mobile browser checks exercise real guided positive/constrained flows, lazy routes, deep-link reload, saved metrics, deterministic summary, empty search and keyboard navigation. No document overflow or console errors/warnings in the final acceptance tab. Tables scroll internally. This is a manual accessibility review, not WCAG certification.

[Validation history](validation.md), [browser evidence](evaluation/phase8-browser.json), [current screenshots](screenshots/README.md).

## Security and publication review

The actual ignored `.env` and Gemini key were not modified or exposed. Tracked/non-ignored source and production frontend bundles are scanned for credential/private-key patterns. Protected operational/Copilot files retain their hashes. No debug endpoint bypassing application validation was added. CORS uses explicit configurable origins. Runtime configuration contains only a public API origin.

Docker uses an unprivileged user and root-owned immutable assets; only the federation experiment directory is writable among app assets. Forecast bundles are trusted local assets and must never be replaced with untrusted serialized models. API authentication, durable workflow state, multi-replica coordination, production audit controls and capacity/load testing remain unimplemented. No penetration testing is claimed. [Publication checks](evaluation/phase8-security.json).

## Deployment decision and reproducibility

Local Docker is verified at ₹0 without inference or cloud accounts. Firebase static SPA configuration, HTTPS API-origin configuration and backend `PORT`/health readiness are prepared. **Nothing is publicly deployed.** Cloud Run requires a billing-linked project; no billing was enabled. Static Hosting on Spark is a potential later free target, but a complete demonstration needs an approved reachable backend. Firestore migration is unnecessary; the existing snapshot adapter remains unverified and does not persist scenarios/conversations/run indexes.

Backend image is approximately **2.16 GB**, frontend approximately **94.4 MB**. A single post-readiness reading showed backend **328.5 MiB**, not peak memory. Cloud training requires suitable CPU allocation/job handling; process-local sessions cannot safely span multiple replicas. Review the [exact unexecuted deployment commands and prerequisites](deployment.md).

`prepare_demo.py` verifies existing assets instead of reseeding. `verify_demo.py` checks models, both solver cases, federation reload, frontend and secret safety. `package_demo.py` creates a trusted portable bundle of ignored canonical generated/model/planning assets; `restore_demo.py` validates paths/hashes before restoring missing files and refuses differing existing assets. The small accepted federation assets are versioned. Fresh-clone portability requires this bundle or a separately measured explicit rebuild; no fresh-clone retraining equivalence is claimed.

## Readiness and remaining blockers

The local product is ready for the final cloud deployment decision, pitch-deck creation and technical submission packaging. The [90-second and three-minute scripts](final-demo-script.md) and [verified pitch facts](hackathon-facts.md) are ready; no presentation was created.

Genuine external blockers are live Gemini acceptance and the no-billing restriction for Cloud Run. A public Hosting project/backend destination and production access design are not selected. Team name/member attribution has not been supplied. None blocks the local deterministic hackathon demonstration. Production/clinical adoption remains outside the validated prototype scope.
