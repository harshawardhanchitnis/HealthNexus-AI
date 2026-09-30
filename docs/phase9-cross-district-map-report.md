# Phase 9 — Cross-District Resilience and Geospatial Command Centre

## Baseline and preservation

Started from commit `723c6a8`. Phase 6 was fully accepted; this phase makes **zero live Gemini requests** and changes no Copilot production code. The local preservation guard compares 346 original file identities, including `.env`, original profiles, model/planning assets, accepted federation, Phase 6 evidence and the historical Gemini ledger (42 requests). The original canonical plans are independently rerun. This feature uses no cloud billing or map key and has not been deployed.

## Existing optimizer audit

[Pre-implementation inventory](phase9-cross-district-inventory.md). The original solver supported district/state/national donor networks; state already reached other districts but also allowed same-district donors. Phase 9 adds strict `cross_district` through the *same* candidate, edge, CP-SAT and impact pipeline. The receiver remains a selected Indian district; eligible donors must be in a different district of the same Indian state. The original reserve, 7-day current-cover, 500 paired demand-path margins, known receipts, 14-day horizon, unit matching, non-negative inventory, conservation and lexicographic objective remain. International physical transfers remain prohibited. No profile or inventory was altered. A new server-owned geography annotation labels actual lanes; `action_state` remains advisory, never executed or authorized.

## Accepted measured cross-district case

Existing `redistribution-ready` profile, India → Maharashtra → Pune, severe dengue, 14 days, seed 42. The solver chose **two donor facilities in Nagpur** and **one Pune receiving facility**, with 10 actual other-district lanes. The result was **OPTIMAL**: target before 41,763 accounting items; safe donor capacity 9,307; recommended 9,307; unresolved 32,456. Units by resource: AMX 1,437; IFA 2,265; IVF 902; ORS 819; PCM 3,884 (the summed accounting items are not physically interchangeable). Expected unmet demand changed 27,655.218 → 19,974.721; critical resource warnings 7 → 0; facilities at risk 1 → 1; maximum individual stock-out risk 100% → 100%. Donor reserve violations **0**; new donor risks **0**. Baseline and scenario remained immutable. Each accepted donor passed the origin, point and all 500 sampled 14-day demand paths after its total outgoing quantity.

**Illustrative geography corrected:** The map-only `illustrative-district-v1` catalogue covers all 69 existing Indian prototype districts with rounded, project-owned display anchors near their administrative centres. Pune uses 18.53 N / 73.85 E; Nagpur uses 21.15 N / 79.09 E. A SHA-256 of catalogue version and facility ID provides the same bounded 0.5-3 km offset on every load and in both profiles. These are not surveyed district centroids or hospital coordinates. Other countries have no district catalogue and retain their original illustrative points. No runtime geocoder or map key is used.

Map geometry and optimizer inputs are deliberately separate. Saved snapshot coordinates, hashes, identities, distance inputs and all accepted plan quantities remain unchanged. `distance_km` retains the actual original optimizer proxy (2.30-5.90 km in this accepted case); `map_distance_km` is computed from the new displayed points and measures **619.85-620.65 km**. The map inspector labels both explicitly. Haversine geographic proxy is **not road distance, travel time or logistics feasibility**; these display anchors never justify shipment execution. The district identities still come from validated operational data. Geographic cross-check references: [Pune official district context](https://pune.gov.in/en/about-pune/) and [Nagpur official district context](https://nagpur.gov.in/profile/); the catalogue remains project-owned illustrative engineering data.

[Complete zero-provider measured receipt, including individual quantities and distance evidence](evaluation/phase9-cross-district.json). Rebuild with `python scripts/verify_cross_district.py`; it fails if the positive case lacks a genuine cross-district lane or if safety/conservation checks fail.

## Canonical preservation

| Pune severe dengue | Existing district ready | Existing constrained | Strict cross-district ready |
|---|---:|---:|---:|
| Receiver target before | 41,763 | 30,230 | 41,763 |
| Safe capacity | 17,745 | 0 | 9,307 |
| Recommended accounting items | 15,679 | 0 | 9,307 |
| Lanes | 10 | 0 | 10 |
| Remaining target | 26,084 | 30,230 | 32,456 |
| New donor risks / reserve violations | 0 / 0 | 0 / 0 | 0 / 0 |

The constrained cross-district run also remains zero capacity, zero lanes and 30,230 unresolved. No deficit or solver outcome was hidden.

## Map architecture and provenance

The new read-only `/api/geospatial` endpoint validates country/profile/geography, scenario identity, origin/model SHA, plan identity and donor scope before returning GeoJSON facility points and actual advisory plan LineStrings. Network uses current snapshots; Forecast uses existing baseline projections/warnings; Emergency uses an actual saved scenario; Redistribution uses an actual saved optimizer run and includes out-of-district donors. Status, capacity summaries, stock-out risk and warnings are server-owned. Display filters never alter the plan. Incompatible or stale handles return a clear 404/422/503 rather than another profile's data.

Angular lazily loads `/geospatial` and npm MapLibre GL JS **6.11.2**. It uses the public [OpenFreeMap Positron style](https://openfreemap.org/quick_start/) with no key or registration, local package worker/CSS assets, typed GeoJSON sources, a single persistent canvas, and a synchronized keyboard-accessible list and inspector. Point status/roles, actual transfer lanes and national/state/district navigation use only HealthNexus read-model data. Lane widths are uniform because resources have different units. Every view retains [OpenFreeMap](https://openfreemap.org), [OpenMapTiles](https://openmaptiles.org) and [OpenStreetMap](https://www.openstreetmap.org/copyright) attribution. Basemap errors/timeout cancel remote style sources, keep operational overlays/list/summary and show a compact notice with no automatic retry.

The map trust label states **SIMULATED / ILLUSTRATIVE FACILITY OPERATIONS**. Fictional facilities and illustrative points are separate from historical aggregate public data. There is no live government inventory, hospital connection, geocoding, physical transfer, external authorization or real shipment tracking.

## Browser screenshots and verification

The **actual final Docker nginx + FastAPI browser flow** ran the severe Pune scenario and called OR-Tools, producing the server-owned Nagpur→Pune 10-lane result. Tiles rendered on [OpenFreeMap](https://openfreemap.org/quick_start/). The normal fresh Chromium tab recorded **zero console errors/warnings**. Actual unedited captures:

| Viewport | Screenshot | Body width vs viewport | Markers / actual lanes |
|---|---|---|---|
| 1440×900 | [Desktop](screenshots/phase9-cross-district-1440x900.png) | 1425 / 1440 | 5 / 10 |
| 1280×800 | [Desktop compact](screenshots/phase9-cross-district-1280x800.png) | 1265 / 1280 | 5 / 10 |
| 1024×768 | [Small desktop](screenshots/phase9-cross-district-1024x768.png) | 1009 / 1024 | 5 / 10 |
| 768×1024 | [Tablet](screenshots/phase9-cross-district-768x1024.png) | 753 / 768 | 5 / 10 |
| 390×844 | [Mobile](screenshots/phase9-cross-district-390x844.png), [scrolled map](screenshots/phase9-cross-district-mobile-map.png) | 375 / 390 | 5 / 10 |

No document overflow. All three required attribution links stayed present. The accessible synchronized list selected a facility and showed current percentages, the existing 14-day forecast signals and warnings. Map↔redistribution navigation preserved the plan ID and strict donor scope. The constrained UI run showed **0 safe capacity, 0 lines and 30,230 unresolved**: [actual screenshot](screenshots/phase9-constrained-mobile.png).

With only `tiles.openfreemap.org` blocked via Chromium DevTools and cache disabled, the component made **one** upstream basemap request before cancellation, displayed **Base map unavailable**, kept local pressure points, ten advisory lanes, summary and accessible list, and raised **zero** errors/warnings in a fresh browser tab. [Actual blocked-tile screenshot](screenshots/phase9-tile-failure-mobile.png). Removing the block restored normal tiles. [Browser receipt](evaluation/phase9-browser.json).

## Tests and performance

- Full backend suite: **677 passed**, one upstream Starlette/AnyIO deprecation warning, 165.69 seconds. Includes 41 new Phase 9 cases using real saved profiles, 500-path safety, GeoJSON/source identity, stale handles, all five-country isolation, no provider transport, and unchanged Phase 6 mock-fault behavior.
- Frontend: **14 ChromeHeadless unit tests passed**; one map instance, sources, tile failure, authoritative list/selection/context/keyboard IDs, disposal and safe query navigation.
- Python compile and `pip check`: passed. Strict TypeScript (app and specs) and Angular production build: passed, no Angular warnings. `npm audit --audit-level=moderate`: **0 vulnerabilities**.
- Zero-provider canonical/federation reload: [pass receipt](evaluation/phase9-baseline-and-federation.json). The accepted global checkpoint and all five participant evaluations matched without retraining; canonical district and constrained outputs matched exactly. Local preservation: **346 protected identities unchanged**, Gemini ledger remains at 42. Additional cross-district [verifier receipt](evaluation/phase9-cross-district.json).
- Final frontend and backend Docker images rebuilt successfully. `docker compose up -d --wait` passed with backend health and readiness; nginx served all 16 SPA deep links including `/geospatial`, local MapLibre workers and frontend-to-backend API connectivity. Actual container HTTP scenarios/plans reproduced canonical, constrained and cross-district values. Both containers restarted; health/readiness, deep links and all four measured plans passed again. Saved federation and ten model partitions were reloaded without retraining. Browser map runtime, attribution, actual lane inspector, constrained zero lines, tile-outage fallback and responsive desktop/mobile captures passed using these images. [Docker release receipt](evaluation/phase9-docker.json), reproducible with `python scripts/verify_phase9_release.py` against the running local production stack. No protected Docker IPC file was touched.

The measured pre-phase initial production entry bundle was **388,111 raw bytes**; post-phase **389,488 bytes**, a **+1,377-byte** change. The separately lazy-loaded Geospatial/MapLibre JavaScript chunk is **1,057,319 raw bytes** (Angular estimated transfer about **236.31 kB**). Exact sizes came from final build output and referenced entry assets. No runtime performance number is inferred from bundle size.

## Security, limitations and release boundary

`.env`, API key, Google project, billing configuration and Gemini ledger remain unchanged; there is no map API key or live Gemini request. The environment file stays ignored. OpenFreeMap's public instance has no guaranteed SLA; HealthNexus operation and accessible list remain independent of tiles. Scenario and plan handles are process-local, so links require the same running backend. Map Haversine distances use district-aware illustrative points, separately from the preserved original optimizer distance inputs; neither is road routing. No procurement, approvals, execution workflow or government integration was added. Phase 9 is a local feature; **no deployment was performed**.

## Release status

All Phase 9 release gates **PASS** on 2026-09-30: 677 backend tests, 14 frontend tests, strict TypeScript, production build, compileall, pip check, zero-vulnerability npm audit, geography review, final Docker images, runtime health/readiness, all SPA deep links, frontend API connectivity, restart recovery, cross-district verifier, canonical/constrained preservation, accepted federation reload and security/preservation. Gemini requests remain **ZERO**; the historical ledger remains 42 and `.env` is unchanged. HealthNexus feature development is frozen and ready for deployment. **No deployment was started.**
