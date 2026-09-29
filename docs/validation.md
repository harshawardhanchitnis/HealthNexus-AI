# Validation — 2026-09-29

## Phase 6 — final synthesis budget fix

- Pre-live regression passed **479 backend tests in 71.00 seconds**, retaining all 459 previous cases. Shared Lite/3.6 official SDK HTTP mocks, compilation, dependency checks, canonical results, all ten country/profile partitions, saved federation and security/preservation passed. [Preflight](evaluation/phase6-synthesis-preflight.json).
- Exactly one Lite synthesis send returned HTTP 200 / completed, complete four-claim JSON, 10,557 input / 470 output / 0 thought / 11,027 total tokens in 2.958 seconds at low/4,096. It used deterministic reconstructed local evidence and no native provider planning, previous interaction, retry or fallback. The ledger preserves 28 historical sends and appends one (29 total).
- The answer's execution wording fails manual factual acceptance. Initial live fact/numeric/solver validation was not reached because the stateless verifier unnecessarily required a nonempty ID. The SDK makes that field optional; local tests fix that check and reject execution variants. Original live evidence is unchanged; no second live send tested the correction. Unknown-ID/unsupported-number counts are not asserted as zero. [Live trace](evaluation/phase6-synthesis-live.json), [independent review](evaluation/phase6-synthesis-review.json).
- Final local regression passes **484 tests in 120.78 seconds** (459 retained + 25 new), with shared SDK mocks, compilation, dependencies and security/preservation PASS. [Final evidence](evaluation/phase6-synthesis-final.json). Frontend files and their previous successful TypeScript/production build are preserved. No additional live case, deployment, key/project change or billing change occurred. [Detailed report](phase6-synthesis-report.md).
- **Positive live workflow remains pending because: the completed synthesis describes advisory transfers as executed actions.**

## Phase 6 — historical full live workflow attempt

- Preflight passed **458 backend tests in 70.04 s**, retaining all previous 436 plus 22 verifier cases. Existing fact-ID mocks, all four workflow mocks, canonical plans/federation, compilation, dependencies, TypeScript/build and security passed. Google AI Studio headroom was independently confirmed by the user; no quota was inferred from the ledger.
- Actual native scenario and optimization calls passed declaration, Pydantic, permission, context/identity and canonical plan checks. Final synthesis returned HTTP 200 / `incomplete` with truncated JSON, producing `response_incomplete`. Schema/fact-ID/qualitative/numeric final validation was not reached; those counts are not reported as zero.
- Exactly three new Lite sends preserved the historical 25 (28 total). No retry, failover, later live cases or deployment followed. The accepted 2/2 smoke and all frozen application/engine/UI/federation evidence remain intact. A verifier-only sanitation test follows the stopped attempt; [final local regression/security](evaluation/phase6-workflow-final.json) records it.
- Final local regression passes **459 tests in 111.96 s**, retaining the original 436 plus 23 verifier cases. Compilation/dependencies and unchanged TypeScript/build pass, with one existing upstream warning. Final preservation/security checks pass; there are no further live sends.
- **Phase 6 remains pending because: the positive workflow's final structured synthesis returned `incomplete` with truncated JSON (`response_incomplete`).** [Full report](phase6-full-live-report.md), [live trace](evaluation/phase6-workflow-live.json), [diagnosis](evaluation/phase6-workflow-diagnosis.json).

## Phase 6 — request-local fact citations

- **436 backend tests pass in 119.98 s**, retaining all 385 previous cases and adding 39 fact-contract plus 12 verifier cases. Python compilation, Windows `pip check`, strict TypeScript and Angular production build pass; one existing Starlette/AnyIO deprecation warning remains.
- Shared Lite and 3.6 mocks pass schema, ID, qualitative/numeric grounding and context validation, with zero unknown IDs or unsupported numbers. Official SDK wire mocks verify actual-send accounting and current fact-ID schema enums. No model-specific answer logic is added.
- The exact requested bed-utilisation migration resolves a server fact ID to `summary.bed_utilisation = 79.8%`; `bed_utilisation` remains rejected, without path repair. Numeric validation, canonical engines, ten country/profile partitions, saved federation, UI and production fallback order remain unchanged.
- Zero live sends occurred before all local gates passed. The dedicated verifier preserves 23 historical requests, allows one Lite smoke followed by a second only on full PASS, and never retries/fails over. Full Phase 6 workflow acceptance remains pending. [Current report](phase6-fact-citations-report.md), [regression gates](evaluation/phase6-facts-regression.json), [mock evidence](evaluation/phase6-facts-mock.json), [migration](evaluation/phase6-facts-migration.json), [canonical verification](evaluation/phase6-facts-canonical.json).

Earlier dated measurements below are retained history.

**Live grounded smoke acceptance: PASS 2/2. Full Phase 6 workflow acceptance remains pending.** Two independent Lite requests returned HTTP 200, valid schemas and current fact IDs, configured qualitative/numeric/context PASS, and zero unknown IDs or unsupported numbers. Provider times 9.329 / 9.091 s; total tokens 8,546 / 9,304. Historical ledger 23 + exactly two sends = 25; no retry/fallback/full workflow. [Live evidence](evaluation/phase6-facts-live.json), [final security](evaluation/phase6-facts-security.json). Qualitative topic checks do not establish exhaustive natural-language truth.

## Phase 6 — exact numeric evidence contract

- **385 backend tests pass in 53.36 s**, retaining all original 340 cases and adding 45 grounding/verifier cases. The original pre-live gate passed 382 cases; three final local hardening cases and a full rerun followed the stopped smoke with zero extra live calls. Python compilation, Windows `pip check`, strict TypeScript and unchanged Angular production build pass. One existing Starlette/AnyIO deprecation warning remains.
- Shared mocked Flash-Lite and 3.6 Flash flows pass schema and numeric-evidence validation. No model-specific answer logic or new engine arithmetic is added. Production model order is unchanged.
- Canonical ready/constrained plans, conservation, donor protection, all ten country/profile partitions and original saved federation reload/evaluation pass with zero provider sends. Historical evidence, UI, engines, existing tests and `.env` remain unchanged.
- The three old rejected drafts were not persisted. Exact numbers/sentences and their A/B cause classification are explicitly unrecoverable. New numeric failures retain sanitized claim/source diagnostics. Full Phase 6 live acceptance remains pending; only a conditional two-send Flash-Lite smoke is authorized here.
- The first Flash-Lite live smoke returned **HTTP 200 / valid schema**, with no numeric literals, but cited `bed_utilisation` instead of `summary.bed_utilisation`. Exact path validation correctly rejected it. **Stopped after one send**, no second smoke or full acceptance. Provider time 8.551 s; 7,950 total tokens. Historical ledger 22 + 1 = 23; final preservation/security pass. [Live evidence](evaluation/phase6-numeric-live.json), [exact citation diagnosis](evaluation/phase6-numeric-live-diagnosis.json), [security](evaluation/phase6-numeric-security.json).

Evidence: [grounding report](phase6-grounding-report.md), [historical diagnosis](evaluation/phase6-numeric-diagnosis.json), [mock checks](evaluation/phase6-numeric-mock.json), [pre-live regressions](evaluation/phase6-numeric-regression.json), [final regressions](evaluation/phase6-numeric-final-regression.json), [canonical engines](evaluation/phase6-numeric-canonical.json).

## Phase 8.5 — premium Command Centre redesign

- **340 backend tests pass in 55.88 s** with backend source/tests unchanged; one existing Starlette/AnyIO deprecation warning. Python compilation, Windows/container dependency checks, strict TypeScript and Angular production build pass. No build warnings or new dependencies; production npm audit reports zero known vulnerabilities.
- Initial bundle **387.99 kB / estimated 104.69 kB transfer**, compared with Phase 8’s **370.25 / 101.28 kB**. Shared design system, accessible mobile drawer, real priority signals, functional four-family Scenario Library, protected transfer-lane cards, precise federation country comparisons and offline/evidence Copilot workspace are implemented. Five additional final guide checks pass after scoping sidebar styles; Next preserves Pune/profile context.
- **70 browser checks** cover 14 routes at 1440×900, 1280×800, 1024×768, 768×1024 and 390×844. Zero document overflow, application alerts or captured console warnings/errors. Keyboard drawer, skip link, real forecast-point readout, profile-preserving guide/warning navigation and all four actual scenario workflows pass.
- Production frontend Docker build and healthy unchanged backend pass liveness/readiness, all ten country/profile overview partitions, original saved federation and SPA deep routes. No accepted experiment retraining, data generation or cloud deployment occurred.
- Both original severe Pune plans reproduce exactly: ready **41,763 / 17,745 / 15,679 / 10 / 26,084**, constrained **30,230 / 0 / 0 / 0 / 30,230**. Donor violations/new risks stay zero, critical receiver medicine warnings stay **7 → 0**, maximum stock-out risk stays **100% → 100%**, and per-resource conservation passes. Saved federation evidence remains byte-identical.
- Before the final matrix, **all 260 protected files**, `.env` and the historical **12-request ledger** are unchanged. Zero live Gemini calls occurred during redesign/browser testing. The end-only authorized two-attempt/five-model diagnostic has a hard ceiling of ten additional sends, no retry/failover/resumed interactions, and preserves historical accounting. Its measured results are recorded separately; smoke acceptance does not complete Phase 6.

- Final controlled live matrix completed **10 actual sends**, preserving the historical 12 and recording 22 total. Provider-available models: 2; accepted grounded smoke models: 0. No full Phase 6 workflow followed; [post-matrix preservation](evaluation/phase85-security.json) passes.

Evidence: [Phase 8.5 report](phase85-report.md), [regressions](evaluation/phase85-regression.json), [canonical engines](evaluation/phase85-demo.json), [browser](evaluation/phase85-browser.json), [current captures](screenshots/README.md), [final Gemini matrix](evaluation/phase85-gemini-availability.json). Earlier phase measurements below remain dated history.

## Phase 8 — current final integration

- **340 backend tests pass in 54.88 s**, retaining all 332 earlier cases and adding eight capability/saved-artifact checks. Python compilation, Windows and Linux-container `pip check`, strict TypeScript and production Angular build pass. Initial bundle 370.25 kB / estimated 101.28 kB transfer. One existing upstream Starlette/AnyIO deprecation warning remains.
- Actual Docker build/up, liveness/readiness, ten compatible forecast/profile partitions, real scenarios/warnings/OR-Tools, five-round CPU training, explicit offline summaries and restart/saved-model reload pass. No cloud deployment is claimed. New Linux training/checkpoint differences are reported separately; the accepted Phase 7 experiment remains unchanged.
- The canonical verifier passes: ready Pune 41,763 target, 17,745 safe capacity, 15,679 accounting items / 10 lanes, 26,084 remaining; constrained 30,230 remaining / zero capacity / zero transfers. Donor violations/new risks are zero. Assets and conservation remain intact.
- Desktop and 390×844 mobile product checks exercise both actual guided solver flows, saved federation, deterministic summaries, empty filters, lazy/deep routes and keyboard navigation. No document overflow or console errors/warnings in the final acceptance tab. Current actual screenshots cover all nine requested pages. The skip target is keyboard-focusable. Manual accessibility review is not WCAG certification.
- Tracked/non-ignored source and frontend bundle secret checks pass; `.env` is ignored/untracked and unchanged. Production npm audit reports zero known vulnerabilities. This is not penetration testing. All 115 protected operational/Copilot files retain their hashes. No live Gemini calls, key changes, billing changes or cloud resource creation occurred; ledger remains 12.
- Exact Phase 6 status remains **Implementation complete; live provider acceptance pending due to Gemini service availability.** The core demo uses explicitly labelled offline summaries. Live Gemini remains unverified.

Evidence: [final report](final-technical-report.md), [canonical verifier](evaluation/phase8-demo.json), [actual Docker acceptance](evaluation/phase8-docker.json), [startup](evaluation/phase8-container-startup.json), [reload](evaluation/phase8-federation-reload.json), [browser](evaluation/phase8-browser.json), [publication checks](evaluation/phase8-security.json), [deployment decision](deployment.md). Earlier measurements below remain historical.

## Phase 7

- **332 backend tests pass** in 105.63 s, retaining all previous 289 and adding 43 federation cases. Actual parameter averaging, shared initialization, local training changes, sample/equal weighting, malformed updates, finite values/checksums, deterministic seed, raw-data contract, client country isolation, numeric save/reload, evaluation, artifact/model immutability, bounded run storage and API/delete are covered.
- Python compilation, `pip check`, strict TypeScript and Angular production build pass. Initial 366.50 kB / estimated 100.33 kB transfer; federation lazy chunk 18.22 kB / 5.38 kB.
- Existing country-local preparation, five-round actual CPU MLP/FedAvg run, independent saved-model evaluation and report commands pass. Final CLI training 4.8011 s; 417 parameters, 614,235 logical boundary bytes, zero raw operational records sent. Global test WAPE 8.9472%; foreign nodes improve against independent local-only MLPs and India degrades slightly. No claim of improvement over operational HGB is made.
- Real local API background training/progress, exact round retrieval, invalid request and delete/404 checks pass. Desktop and 390×844 mobile UI render actual data, zero console errors/warnings, no document overflow; result tables scroll internally. Temporary viewport restored.
- All 115 protected Copilot/forecast/scenario/optimizer/data/model files retain their hashes. Copilot's 13-tool schema/system prompt/failover/verifier are unchanged; no federation tool registration. Necessary new modules/main routing change the existing broad all-backend evidence digest; its invalidation remains intact and old evidence is preserved.
- **Zero live Gemini requests** during Phase 7; ledger remains 12, same ignored/untracked key and `.env`, no billing changes. Phase 6 remains: implementation complete; live provider acceptance pending due to Gemini service availability. No deployment, secure aggregation, differential privacy, encrypted network transport or production federation is claimed.

See [Phase 7 measured report](phase7-report.md), [federated model and privacy boundary](federated-learning.md), [actual run](evaluation/phase7-run.json), [API](evaluation/phase7-live-api.json), [browser](evaluation/phase7-browser.json) and [preservation](evaluation/phase7-preservation.json).

## Phase 6

- **Current targeted verification: 289 backend tests pass in 45.88 s**, preserving the previous 281 and adding eight verifier-selection/budget cases. Python compilation, `pip check`, strict TypeScript and Angular production build pass; initial 366.12 kB / estimated 100.26 kB transfer. Fresh [offline acceptance](evaluation/phase6-targeted-offline.json) reproduces positive and constrained real-engine plans with zero provider requests.
- [Targeted live smoke](evaluation/phase6-targeted-live-smoke.json) skipped 3.8/3.7/3.6 and sent once each to 3.5 Flash and Flash-Lite; both returned 503 HIGH DEMAND. The explicitly authorized cumulative ceiling is 14: ten retained sends plus two new sends total 12, leaving two unused. No successful model, live schema/evidence/numeric validation or subsequent flagship/UI acceptance is claimed. Historical evidence below remains intact. [Current consolidated result](evaluation/phase6-targeted-verification.json).
- **281 backend tests pass**, including the prior 237 and 44 failover cases. Mocked/official-SDK wire tests cover all five requested models, native calls/results, medium thinking, structured synthesis, exact fallback order, bounded attempts, global budget, safe handoff, sticky state, quota circuits, grounding failures and explicit offline mode.
- Python compilation, pip dependency checks, strict TypeScript and Angular production build pass. Initial bundle 366.12 kB / estimated 100.26 kB transfer; Copilot lazy chunk 22.89 kB / 6.35 kB.
- [Mock acceptance](evaluation/phase6-failover-mock.json), [offline acceptance](evaluation/phase6-failover-offline.json), and [five-model scripted matrix](evaluation/phase6-failover-candidates-mock.json) pass. No operational engines, safety reserves, inventories, profiles or ML artifacts were modified.
- [Live automatic smoke](evaluation/phase6-failover-live-smoke.json): one request each to 3.8/3.7/3.6 Flash; all returned 503 HIGH DEMAND. No successful interactions. Daily ledger reached 10/10, so 3.5 Flash was blocked before sending; Flash-Lite was not reached. Live schema/grounding/native compatibility remains unverified for these fallbacks. No full live dengue workflow followed the failed smoke.
- Desktop and 390×844 mobile Copilot UI checked with explicit offline mode, zero console errors/warnings, no horizontal mobile overflow, and no extra Gemini requests. Live fallback rendering has not been observed because no model answered.
- Same ignored/untracked key, no billing changes, no Phase 7. [Measured report and limits](phase6-failover-report.md). The upstream Starlette/AnyIO deprecation warning remains. Production authentication, durable model health/session storage and clinical validation remain separate.

## Phase 5.5

- **156 backend tests pass**, retaining all 135 Phase 1–5 tests and adding 21 profile/preparation cases. Serial and batched forecasts match exactly in both profiles. Ledger conservation, requested-demand parity, deterministic generation, profile hashes/provenance, safe positive plans, immutable copies, cache keys/invalidation/corruption and API isolation are covered.
- Both profile generators were run across all five countries with the original seed/origin preserved. Model weights were reused after demand-input and hash compatibility checks; no retraining occurred.
- Constrained Pune severe dengue remains exactly 30,230 target units unresolved, zero safe donor units, zero transfers and OPTIMAL status. Ready Pune produces 17,745 safe donor units, 15,679 transferred units over 10 lanes and 26,084 unresolved target units. Both use actual OR-Tools; the district comparison ties greedy.
- Ready expected unmet demand falls from 27,655.2181 to 17,378.1980; total warnings 36 → 25, receiver critical medicine warnings 7 → 0, AMX/IFA/ORS sampled stock-out risk 100% → 0%. IVF/PCM risk and the maximum risk remain 100%. Donor violations/new risks remain zero, and all resource stocks are conserved.
- National cold baseline planning measured 15.78 s without disk preparation, 10.28 s with it and 4.54 s warm. Warm Pune district is 0.20 s and Maharashtra scope 0.20 s. Actual stage timings and serialization sizes are retained in the report; these are local measurements, not controlled load benchmarks.
- Python compilation, strict TypeScript and Angular production build pass (362.93 kB initial raw / 99.49 kB estimated transfer). All ten country/profile combinations pass live API model and run-isolation checks, exact GET roundtrips, inventory/scenario immutability and profile validation.
- Desktop/mobile browser checks exercise profile demo loading, real scenario/solver flow and profile-preserving navigation. The 390×844 mobile layout has no document overflow; tables scroll internally. No application console errors were observed in the final check window. These checks use keyboard/select controls and are manual.

See [Phase 5.5 report](phase55-report.md), [reproducible results](evaluation/phase55-verification.json), [live API results](evaluation/phase55-live-api.json), and `docs/screenshots/phase55-*.png`. One existing upstream Starlette/AnyIO deprecation warning remains. Gemini, cloud/Docker deployment, real inventory and clinical/transport validity are not claimed implemented or validated.

## Phase 5

- **135 backend tests passed**: all 105 existing tests plus 30 optimization cases. Actual CP-SAT covers multiple donors/receivers, discrete quantities, scarcity, strict-full-service infeasibility, deterministic optimality, critical-priority dominance, no-incumbent timeout and retained-incumbent FEASIBLE classification. The latter uses a controlled wall clock around a real first-stage solve.
- Donor checks cover demand, future receipts, worst sampled paths, origin stock, reserve and cover. Impact tests execute a 181-tablet transfer, recompute risk/warnings, remove 130 units of expected unmet demand, introduce no donor risk and conserve 1,010 origin units. Baseline/scenario/store copy isolation, scenario identity and country boundaries are checked.
- Python compilation passes; `pip check` reports no broken requirements with OR-Tools 9.15.6755, NumPy 2.2.6 and existing Firestore dependencies.
- Strict TypeScript passes. Angular production build passes: 360.34 kB initial raw / 98.90 kB estimated transfer; planner lazy chunk 27.32 kB / 7.44 kB.
- Live API smoke passes five baseline country plans, foreign-run 404s, exact GET roundtrips, country-aware DELETE, inventory/scenario immutability and Pune district/state/national plans. See [measured output](evaluation/phase5-smoke.json).
- Desktop browser: Severe Pune Dengue → active scenario optimization link → candidate preview → CP-SAT result → greedy/impact view → discard with scenario retained. Mobile: 390×844 viewport, resource/scope controls and IV-fluid optimization; measured document width equals scroll width (375 CSS px after scrollbar), with tables scrolling internally. Screenshots are in `docs/screenshots/phase5-*.png`.
- Browser interaction checks use keyboard activation of controls plus select operations; native mouse/touch input and positive-transfer cards against a replenished live snapshot are not established by these checks. No new application console errors were observed in the final check window.
- **Open demo prerequisite:** the existing snapshot has no protected donor surplus in any country. Pune reports zero transfers, 30,230 target units unresolved, 17,075.1558 expected unmet units and an honest OR-Tools/greedy tie. Nonzero correctness is tested separately; a positive-transfer Pune success demonstration is not claimed complete.

One existing upstream Starlette/AnyIO deprecation warning remains. Forecast preparation lies outside the solver budget (final cold all-India baseline API call 109.50 s; warm Pune national 8.71 s; district 0.24 s). An earlier cold run took 44.23 s, so preparation latency is variable and remains a performance limitation. Docker/cloud execution, production authentication/durability, real logistics and clinical validity remain unverified. No Gemini or federated training is implemented. See [full Phase 5 report](phase5-report.md).

## Phase 4

- **105 backend tests passed** (73 existing + 32 Phase 4 cases); Python compilation passes.
- Angular strict TypeScript and production build pass, 357.22 kB initial / 98.40 kB estimated transfer.
- Actual saved bundles loaded across all five countries. Twenty live scenario runs passed comparison, warning list/detail/summary, country isolation, validation, discard and baseline/forecast non-mutation checks. [Recorded results](evaluation/phase4-smoke.json).
- Keyboard-driven desktop checks: Pune severe dengue, paired KPIs, affected facilities, IV-fluid trajectories, warning navigation/filter/details, scenario reset and preserved baseline navigation.
- Mobile 390×844: form controls, delay/staff/disruption runs, warning details, responsive curves and contained tables. Measured document width stayed within the viewport; no captured console errors in final checks.
- District HTTP runs approximately 0.08–1.32 s with models loaded. Cold national warning summary 19.88 s; measured cached summary ~1.72 s.
- Screenshots: [dengue comparison](screenshots/phase4-dengue.png), [inventory](screenshots/phase4-inventory.png), [warning facts](screenshots/phase4-warning-detail.png), [mobile warnings](screenshots/phase4-mobile-warnings.png).
- See [Phase 4 report](phase4-report.md) for full methods, thresholds, assumptions and exact commands. No epidemiological/clinical validation, Docker/cloud validation, optimization, Gemini or federated training is claimed. One upstream Starlette/AnyIO deprecation warning remains.

## Historical Phase 3

- **73 backend tests passed**, preserving all original 38. New tests cover history generation, ledgers, latent requested targets, frozen-origin feature leakage, temporal partitions/final evaluation dates, baseline calculations, repeat fitting, saved model reload/integrity, horizon validation, country/facility/resource isolation, empirical intervals and reproducible depletion probabilities.
- Generated **540 days for all 231 facilities**, built country-local tables, trained 15 pooled candidate models and compared all three mandatory baselines. Independently loaded/evaluated all five saved bundles; metrics reproduced within numerical tolerance. Reports: [all results](phase3-results.md), [full JSON reports](evaluation/IN.json).
- FastAPI restarted with saved artifacts and without training. Live country-scoped forecast/metrics requests succeed; missing/stale model API states are tested. Original operational APIs remain runnable.
- Angular production build and strict TypeScript checks pass; initial bundle approximately **337.69 kB raw / 93.94 kB estimated transfer**. Python compilation passes. No standalone lint configuration exists.
- Desktop browser: India → Maharashtra → Pune → facility → IV fluids, 1/7/14-day horizons, admissions target, interval chart, receipt-aware stock projection and model report; Russia shows six local facilities and the genuine seasonal-naive admissions champion. Facility Predictive Outlook uses API results.
- Mobile at **390 × 844**: layout, resource/horizon selection and direct-link reloads checked. Reload testing found and fixed dropdown selected-option synchronization for asynchronous geography/resource choices. Temporary viewport was reset.
- Screenshots: [forecast](screenshots/phase3-forecast.png), [model performance](screenshots/phase3-performance.png), [mobile](screenshots/phase3-mobile.png).

One upstream Starlette/AnyIO deprecation warning remains. Browser checks are manual, not an automated end-to-end suite. Docker/cloud execution and real-world predictive or probability validation remain unverified. No Gemini, OR-Tools, emergency scenario or federated training was run.

## Historical Phase 2

- **38 backend tests passed**, preserving the original 13. New checks cover cached imports, normalization, null handling, pagination and host restrictions, raw/normalized tampering, offline import, failed-refresh preservation, provenance, country isolation, legacy migration and causal stock/bed/demand consistency.
- Actual downloads succeeded for the MoHFW/PIB summary and both WHO indicators. Offline import then succeeded: 13 Indian and 20 WHO observations.
- Generated five snapshots with seed 42 and date 2026-09-27: India 207 facilities, four other countries six each; 231 total.
- Production build passed: **330.84 kB raw / 92.91 kB estimated transfer** initially. Strict TypeScript checking and Python compile checks passed. There is no separate lint configuration.
- Browser: India → Maharashtra → Pune shows three facilities. Brazil switching resets local scope, shows six facilities and retains country context in facility detail/provenance.
- Browser: Data Sources shows both source dependencies, correct years, country-filtered records and working text filtering. BRICS shows all five nodes and unavailable training metrics; South Africa's 2010 bed reference is visible.
- At 390 × 844, overview and Data Sources layouts and keyboard-operated mobile navigation work. Viewport reset afterward; no captured console errors during final checks.
- Screenshots: [current overview](screenshots/overview.png), [sources](screenshots/phase2-sources.png).

Firestore/cloud and Docker deployment remain unverified. No forecasting, emergency scenario, Gemini, OR-Tools or FedAvg run is claimed. Browser checks are manual. One upstream Starlette/AnyIO deprecation warning remains in otherwise passing tests.

## Historical Phase 1 checks

Figures below describe the original uncalibrated snapshot and are retained as regression history; current generated values differ.

- `python -m pytest backend -q`: **13 passed**. Covers all 36 regions, reproducible generation, unique facility IDs, inventory/bed/staff conservation, threshold boundaries, national rollups, district scoping, search, validation and sanitized storage failures.
- `npm run build`: **passed**, no build warnings after final layout changes. Initial bundle approximately 324 kB raw / 92 kB transfer.
- Live local backend at `127.0.0.1:8000`, frontend at `127.0.0.1:4200`, with real `/api` calls through the Angular proxy.
- Browser: national dashboard renders 207 facilities; Maharashtra narrows to six, Pune to three. Facility detail shows reconciled inventory, beds, attendance and history.
- Browser: nonexistent facility search produces a clean zero-result state; pagination changes 1–15 to 16–30 of 207.
- Browser: national medicine totals render all five medicines; Pune's empty alert state and national 221-alert view render correctly, with rule explanations.
- Responsive browser check at 390 × 844: overview cards, scope selectors and mobile navigation work; table pages retain horizontal scrolling inside their panel.
- Browser console: no captured errors during final checks.
- Snapshot generated with seed 42 and as-of date 2026-09-27.

Screenshot: [overview](screenshots/overview.png).

## Historical Phase 1 verification limits

These limitations record the original Phase 1 state. Current verification and remaining limits are described in the Phase 8.5 section and linked report above.

- Pytest emits one upstream Starlette/AnyIO deprecation warning; test results pass.
- Firestore adapter is implemented but has not been exercised against a live or emulator project. No cloud upload or deployment performed.
- Container/Firebase configurations are scaffolds and have not been deployed or tested with Docker here.
- Phase 1 had no ML forecasts. Current forecasting, emergency projections and OR-Tools planning are tested as described above; Gemini and FedAvg remain unimplemented.
- Browser checks were interactive checks, not a committed automated end-to-end test suite.
