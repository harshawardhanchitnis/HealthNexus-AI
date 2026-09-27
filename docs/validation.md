# Validation — 2026-09-27

## Phase 3

- **73 backend tests passed**, preserving all original 38. New tests cover history generation, ledgers, latent requested targets, frozen-origin feature leakage, temporal partitions/final evaluation dates, baseline calculations, repeat fitting, saved model reload/integrity, horizon validation, country/facility/resource isolation, empirical intervals and reproducible depletion probabilities.
- Generated **540 days for all 231 facilities**, built country-local tables, trained 15 pooled candidate models and compared all three mandatory baselines. Independently loaded/evaluated all five saved bundles; metrics reproduced within numerical tolerance. Reports: [all results](phase3-results.md), [full JSON reports](evaluation/IN.json).
- FastAPI restarted with saved artifacts and without training. Live country-scoped forecast/metrics requests succeed; missing/stale model API states are tested. Original operational APIs remain runnable.
- Angular production build and strict TypeScript checks pass; initial bundle approximately **337.69 kB raw / 93.94 kB estimated transfer**. Python compilation passes. No standalone lint configuration exists.
- Desktop browser: India → Maharashtra → Pune → facility → IV fluids, 1/7/14-day horizons, admissions target, interval chart, receipt-aware stock projection and model report; Russia shows six local facilities and the genuine seasonal-naive admissions champion. Facility Predictive Outlook uses API results.
- Mobile at **390 × 844**: layout, resource/horizon selection and direct-link reloads checked. Reload testing found and fixed dropdown selected-option synchronization for asynchronous geography/resource choices. Temporary viewport was reset.
- Screenshots: [forecast](screenshots/phase3-forecast.png), [model performance](screenshots/phase3-performance.png), [mobile](screenshots/phase3-mobile.png).

One upstream Starlette/AnyIO deprecation warning remains. Browser checks are manual, not an automated end-to-end suite. Docker/cloud execution and real-world predictive or probability validation remain unverified. No Gemini, OR-Tools, emergency scenario or federated training was run.

## Phase 2

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
- No ML forecasts, OR-Tools solves, Gemini responses or FedAvg rounds were executed; those features are subsequent milestones.
- Browser checks were interactive checks, not a committed automated end-to-end test suite.
