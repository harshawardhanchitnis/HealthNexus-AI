# Validation — 2026-09-28

## Phase 6

- **207 backend tests pass**: all existing 156 plus 51 Copilot cases; final full run 27.23 seconds. Native official-SDK HTTP encoding is verified with a mock transport, not Google network calls.
- Python compilation and `pip check` pass. Strict TypeScript and Angular production build pass: 366.12 kB initial raw / 100.24 kB estimated transfer; Copilot lazy chunk 21.32 kB / 6.06 kB.
- Four-case mocked-model and explicit-offline verification passes using actual local forecasting/scenario/OR-Tools engines. Their outputs match authoritative stored plan fields exactly and preserve country/profile, donor safety, conservation and baseline/scenario immutability.
- Constrained Pune reproduces 30,230 unresolved, zero safe capacity/transfers. Ready Pune reproduces 15,679 transferred accounting items, ten lanes, 26,084 unresolved and zero donor violations/new risks. IVF/PCM remaining stock-out risks remain explicit. All five original snapshot hashes match the committed Phase 5.5 report; protected engine/policy files are unchanged.
- Desktop browser verifies explicit offline labelling, both actual demo outcomes, six-tool trace, same-conversation retained-plan follow-up, profile reset, actual optimizer-result navigation and simulated/government provenance distinction. Mobile 390×844 has 375 CSS px document/scroll width, contained tables and the same measured plan. No captured application console errors occurred. These checks use keyboard/select interaction; no live model response is claimed.
- Exact `gemini-3.8-flash` uses the official 2.25.0 SDK / Interactions API with medium thinking. **Live verification is not run because server credentials are absent**; no Google token usage/inference latency is claimed. Explicit `--live` remains available after configuration.

See [Phase 6 report](phase6-report.md), [integration/setup](gemini.md), [mock evidence](evaluation/phase6-mock.json), [offline evidence](evaluation/phase6-offline.json), [live status](evaluation/phase6-live.json), [snapshot preservation](evaluation/phase6-preservation.json) and [browser evidence](evaluation/phase6-browser.json). One existing upstream Starlette/AnyIO deprecation warning remains. FedAvg, production authentication/cloud deployment and real operational/clinical validity remain unimplemented or unverified.

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

## Limits of verification

- Pytest emits one upstream Starlette/AnyIO deprecation warning; test results pass.
- Firestore adapter is implemented but has not been exercised against a live or emulator project. No cloud upload or deployment performed.
- Container/Firebase configurations are scaffolds and have not been deployed or tested with Docker here.
- Phase 1 had no ML forecasts. Current forecasting, emergency projections and OR-Tools planning are tested as described above; Gemini and FedAvg remain unimplemented.
- Browser checks were interactive checks, not a committed automated end-to-end test suite.
