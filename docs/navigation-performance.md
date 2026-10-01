# Frontend navigation review — 1 October 2026

This report records the prepublication review of changes based on `main` at `989e571360fe88dbcbfeb61190a933adb9310f05`. Measurements cover local builds. Publishing the updated frontend to Firebase requires separate authorization; no public frontend speed improvement is claimed here.

## Confirmed cause

Five separate lazy route configurations recreate Dashboard. Its previous `forkJoin` fetched overview and facilities on every visit, including an overview read on search, status and pagination changes. Supply added inventory; the legacy alerts view added alerts. Only countries were session-cached. Forecast Explorer repeatedly fetched the same facility selector list and saved forecast; source and performance pages fetched unchanged catalogues on every visit.

Parallel dashboard requests collided with the existing low-memory operational admission slot. The browser captured HTTP 429 `operational_busy`, followed by the existing two-second GET retry. This reproduced the reported 2–3 second delay against localhost too. `forkJoin` also waits for observable completion, so merely emitting cached data would still block during stale refresh. Common standalone chunks previously loaded only on navigation.

## Source audit and requests

| View | Reads on visit before this change | Behaviour now |
|---|---|---|
| Overview | overview + facilities(limit 5); district warnings when permitted | Cached by scope; warnings remain subject to district policy |
| Network / Facilities | overview + facilities(limit 15) | Common keys reused across recreated views |
| Supply | overview + facilities(limit 15) + inventory | Only a previously unvisited inventory key needs loading |
| Legacy `/alerts` | overview + facilities(limit 15) + alerts | Common keys reused; actual alerts cached separately |
| Facility detail | facility detail + selected-facility footfall/IVF outlook | Reuse only the same facility/profile/resource/horizon |
| Forecasts | facilities(limit 250) → one selected-facility forecast | Selector and forecast independently cached; no bulk forecast prefetch |
| Warnings | warnings + mutable scenario catalogue, previously joined to completion | Baseline warnings cached; catalogue fresh and non-blocking; scenario warnings uncached |
| Model Performance | saved forecasting metrics | 120-second TTL |
| Data Sources | public source catalogue | 120-second TTL |
| Federation | nodes + status → active run or validated saved demo | Nodes/status/run remain fresh; saved demo has 120-second TTL |
| Geospatial | selected mode/context | Only plain network data without scenario/run handles cached; map code remains on demand |
| Emergency | scenario catalogue/selected scenario; actual user-requested simulation | Mutable handles and actions unchanged; no automatic simulation added |
| Redistribution | scenario catalogue/actual plan, then existing permitted preview | Mutable handles/POST preview/solve unchanged; no automatic solve added |

Shell countries remain session-cached; regions now reuse their profile/country key. Provider status/progress and active federation/scenario/optimizer handles are not stale-cached. The sidebar links Early Warnings to `/warnings`, not the legacy `/alerts` route. Browser timings therefore cover the real sidebar flow; recreation tests separately exercise all five Dashboard routes, including `/alerts`.

## Implementation

`ReadCache` is a singleton, memory-only cache of successful read responses. Keys contain endpoint and canonicalized **all actual HTTP query parameters**, including operational profile, geography, facility, filters, pagination, resource and horizon. Forecast resource/facility also appear in the endpoint. Queued requests capture their parameters before navigation can change profile. Different selections use separate keys and never reinterpret another selection's data.

Normal reads use a 60-second TTL; catalogue, saved metrics and immutable federation demonstration use 120 seconds. Countries retain their existing session semantics. Maximum retention is 32 LRU entries, 4 MiB of serialized UTF-8 payload and 1 MiB per entry. Oversized responses are still delivered, but not retained. These are payload retention limits, not a claim about exact JavaScript heap usage. No browser storage or credentials/provider conversations are cached.

Fresh values emit synchronously without HTTP. Stale values emit immediately, then share one requested refresh. Success replaces the value; failure retains that key's last successful value with a visible, non-blocking notice. Failed stale reads have a 15-second cooldown. Explicit Dashboard Refresh bypasses TTL/cooldown and refreshes its relevant datasets while retaining visible content. Cold failures still show the legitimate error state. New, uncached scopes/filters retain their first-load indicator and do not show the preceding selection.

Concurrent identical reads share a request. Selected operational/metadata GETs are sequenced through one browser queue; this avoids causing an admission collision from Dashboard/Federation's own parallel subscriptions. No request starts merely because a cache observable was constructed. Already-requested reads may finish after their original consumer navigates away, allowing deduplication and reuse. Writes, provider calls/progress, and mutable run retrieval retain their existing semantics. Other clients or in-progress actions can still cause admission rejections; the exact existing GET-only, three-retry `operational_busy` policy remains intact.

Dashboard, baseline warnings aggregation and the selected-facility outlook now use `combineLatest` so cached emissions are rendered before a refresh completes. Warning options load separately and report a catalogue error without deleting valid warning evidence. Dashboard's snapshot label says “SNAPSHOT AVAILABLE”; cached data does not claim a current backend connection. Shared notices identify refresh activity/failure for the current response keys only.

Scenario and optimizer actions leave origin inventory/baseline forecasts immutable, so they do not invalidate baseline snapshots. Their own responses/handles remain uncached. Future inventory-changing endpoints would require explicit cache invalidation. Deployment/model updates may be reflected on the next TTL refresh; a browser reload clears the entire memory cache.

`SelectivePreloading` waits for Angular application stability and another second, then imports Dashboard/common views, facility detail, Forecasts, Warnings, Model Performance and Data Sources. Geospatial (approximately 1.06 MB), Copilot, Emergency, Redistribution and Federation remain on demand. Angular 20.3's installed RouterPreloader handles `loadComponent`; actual browser requests confirmed the six common component/shared chunks loaded before navigation, with no data prefetch. See [Angular preloading configuration](https://angular.dev/api/router/withPreloading) and [RouterPreloader implementation](https://github.com/angular/angular/blob/main/packages/router/src/router_preloader.ts).

Backend data prefetch and sessionStorage were deliberately omitted. Preloading code never constructs a page or starts forecasting, warning preparation, simulation, OR-Tools, federation training or Gemini.

## Measured results

Both builds used the same warmed local backend with `HEALTHNEXUS_LOW_MEMORY=true`, `GEMINI_ENABLED=false`, India national scope and the constrained profile. Baseline production output was copied before edits. Temporary browser-only pointerdown/MutationObserver instrumentation measured **input to valid DOM content**, not compositor paint. Focus emulation was applied identically to matched samples to avoid background-tab timer throttling. Instrumentation and focus emulation were removed afterward. Automation wall time is excluded: exploratory hidden-tab input timeouts and delayed animation frames were not treated as application latency.

These are single matched samples, not a latency percentile/SLA, Render memory measurement, or proof of public deployment speed. The local host is substantially faster than Render Free. New computations and a sleeping Render instance still require an honest initial loader.

Overview was already loaded before the following eight-step sequence:

| Transition | Before DOM ready (ms) | After DOM ready (ms) | API requests before → after |
|---|---:|---:|---:|
| → Network, first visit | 2,182.4 | 58.7 | 3 → 1 |
| → Facilities, first visit | 2,091.8 | 27.6 | 3 → 0 |
| → Supply, first visit | 2,121.7 | 49.7 | 5 → 1 |
| → Overview, revisit | 2,102.2 | 26.8 | 3 → 0 |
| → Network, revisit | 2,127.5 | 24.4 | 3 → 0 |
| → Facilities, revisit | 2,123.7 | 29.0 | 3 → 0 |
| → Supply, revisit | 2,094.3 | 17.1 | 4 → 0 |
| → Overview, revisit | 2,088.9 | 23.8 | 3 → 0 |

Total: **27 → 2 actual API requests**, including admission retries; 25 eliminated in this flow (92.6%). The final four revisits made **13 → 0** requests. Their observed DOM-ready times fell from 2,089–2,128 ms to 17–29 ms. A separate cached four-transition sample was 74–85 ms, also with zero API requests. All matched after-sample HTTP responses were 200; there were no self-induced 429s in that flow.

The after-build broader sidebar flow produced:

| Page | First observed DOM ready (ms) | Revisit (ms) | API requests first / revisit |
|---|---:|---:|---:|
| Forecasts | 122.8 | 47.3 | 2 / 0 |
| Model Performance | 39.9 | 20.3 | 1 / 0 |
| Data Sources | 88.7 | 18.1 | 1 / 0 |
| Federation | 158.2 | 100.9 | 3 / 2 |
| Geospatial network evidence | 210.5 | 59.5 | 1 / 0 |

Map timing is authoritative DOM/list readiness, not completion of third-party basemap tiles. Federation deliberately rechecks two mutable metadata endpoints on revisit. Forecasts, metrics and sources needed no chunk downloads at navigation because their code had already preloaded; Federation and Geospatial downloaded their chunks only when visited.

A separate new-session Overview load, measured including browser automation, was 878 ms before and 1,009 ms after. This is not directly comparable to the DOM table and establishes no cold-start improvement. Its four after-build API responses were 200. The initial production bundle is approximately 396.41 kB raw / 107.29 kB estimated transfer; the large map remains lazy. First-load costs have not been hidden by this change.

Normalized timings, API request counts, HTTP status counts and lazy-chunk request counts are in [navigation-performance.json](evaluation/navigation-performance.json). Temporary transport addresses, generated chunk filenames, raw browser instrumentation, screenshots and build output are excluded from publication.

## Verification and preservation

- Final full ChromeHeadless frontend suite: **49/49 passed** (previous 22 plus 27 meaningful cache/API/navigation/preloading/status tests).
- Strict TypeScript: `tsconfig.app.json` and `tsconfig.spec.json` passed.
- Angular production build passed; lazy component splitting retained.
- Final browser build rendered correctly, switched constrained → redistribution-ready → constrained on Facilities, and returned to cached Overview. No final browser console errors.
- Controlled **local proxy** HTTP 503 refresh test retained the 207-facility snapshot, showed the non-blocking failure notice, and had no blocking loader. The injected failure was removed; it was not a public outage or altered backend result.
- Tests cover same-key dedup, synchronous fresh/stale emission, success/error refresh, explicit bypass, geography/profile/search/pagination/resource/horizon isolation, TTL/cooldown, LRU/UTF-8 size limits, requested-read sequencing, fresh mutable handles, recreated Dashboard routes, warning catalogue independence, selected-key notices, standalone preload timing and existing 429 retry/write exclusions.
- `verify_phase9_preservation.py`: PASS; **346 protected identities**, unchanged accepted engines/artifacts/federation evidence and `.env`; historical Gemini ledger remains **50**; **zero live Gemini requests**.
- No backend source, memory budget, admission control, deployment source configuration, dependency or engine result changed. Backend regression was not rerun for this frontend-only change; the preservation guard verifies exact protected content. Prior accepted 712-test backend result is not represented as a new run.
- Credential-pattern scan of tracked/non-ignored files and production bundles: PASS. `.env` remains ignored/untracked. This is not a penetration test.
- At the prepublication review, `git diff --check` passed. No deployment/environment change, paid resource or production monitoring change was performed. Source publication and frontend deployment are separate steps.

Browser caching reduces Render request pressure; it adds **no backend cache or precomputation**. The existing finite sub-450 MB acceptance evidence remains applicable to unchanged backend code; this task does not claim an absolute production memory guarantee. Real first-load/cold-start delays, other clients' contention, TTL-old snapshots during outages, and on-demand basemap downloads remain practical limits. Refresh notices, key isolation, fresh mutable handles and bounded retention make those limits explicit.

## Changed files and Git review

Modified: `app.config.ts`, `app.routes.ts`, `core/network-api.ts`; pages `brics.ts`, `dashboard.ts/html`, `data-sources.ts`, `facility.ts`, `forecasts.ts/html`, `geospatial.ts/html`, `model-performance.ts`, `warnings.ts`; `shared/predictive-outlook.ts` (all under `frontend/src/app`).

New: `core/read-cache.ts/spec.ts`, `core/network-api.spec.ts`, `core/selective-preloading.ts/spec.ts`, `pages/dashboard-cache.spec.ts`, `pages/warnings-cache.spec.ts`, `shared/read-notice.ts/spec.ts`; this report and `docs/evaluation/navigation-performance.json`.

Publication audit: all three new runtime modules and all six new frontend test files belong to the implementation. The two documentation/evidence files contain normalized measurements and project-relative source references. Temporary artifacts, personal filesystem paths, credentials, environment files, production bundles and screenshots are excluded. The approved publication contains 26 files: 24 frontend source/test/template files and these two documents.
