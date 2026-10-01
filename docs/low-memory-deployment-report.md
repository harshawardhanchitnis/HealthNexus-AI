# India-only public deployment memory gate — 2026-09-30

This report is historical. The [district computation budget report](district-computation-budget-report.md)
records the subsequent approved cuts and the stricter total-container 450 MB gate.

This report covers the explicit `HEALTHNEXUS_LOW_MEMORY=true` runtime. Local
capacity verification is separate from the existing Render service's deployment
and cloud health. No Firebase deployment or live Gemini call was performed.

## Architecture

Public operations cover India only, including both operational profiles, forecast
and warning engines, emergencies, district/cross-district redistribution,
Geospatial Command and Copilot. Foreign operational query/body requests return
422 with an India-only explanation; they are never silently remapped. Repository
and forecasting entry points enforce the same policy beneath the HTTP layer.
Foreign datasets/models remain available for local development when the flag is
false; no operational dataset or model artifact was regenerated or retrained.

The public image defaults to `INSTALL_FEDERATION_TRAINING=0` and contains no
PyTorch. Federation shows the verified accepted five-node saved report. Status
distinguishes `saved_evidence_available=true` from `live_training_available=false`.
Live training starts return controlled 409. Full genuine training remains in the
repository and the local Compose build explicitly opts into CPU PyTorch.

Saved evidence stays on the existing backend endpoint: its report and small
parameter artifact are independently validated on load, without foreign training
tables or operational forecast bundles. The measured evidence/status/node reads
have negligible incremental RSS after warning preparation. Duplicating an export
in Firebase would introduce another copy and integrity lifecycle without a useful
memory saving. The UI shows the verified run/checksum, five experimental nodes,
zero raw records shared, and hides public retraining/foreign operational links.

MapLibre, OpenFreeMap, corrected illustrative coordinates, optimizer distances,
CORS, Firebase configuration, Gemini source/prompts/tools/grounding/action state,
and the primary/fallback order remain unchanged. Phase 6 status now accurately
states live grounded acceptance on Flash-Lite; it does not claim 3.8 passed.

## Allocation changes and bounds

- Low-memory readiness streams trusted India file hashes and checks runtime/profile
  compatibility and saved federation integrity. It does not unpickle models,
  predict, import PyTorch or call Gemini. Its existing 30-second response cache stays.
- The legacy snapshot loads lazily; normal public profile requests never retain
  that third snapshot. Simultaneous first profile requests share one locked load.
- One India model bundle is retained. Two lightweight profile bindings share its
  immutable models, series and residuals instead of duplicating them.
- Prediction points use a 512-entry LRU. Measured retained Python object graph:
  326,736 bytes. Facility forecasts and baseline projections each retain at most
  24 entries: measured 5,387,255 and 3,330,903 bytes respectively. These graph
  estimates can count shared objects twice; they are not whole-process RSS.
- National warning responses process twelve facilities at a time, discarding the
  unused batch outcome. Every warning identity, severity, number and explanation
  matches normal mode exactly; request-time timestamps naturally differ.
- Prepared optimizer retention allows one entry with at most 8 MiB of demand-path
  arrays. Larger preparations stay request-local. Scenario and plan stores each
  allow four handles in this mode, returning existing controlled limit errors
  until a result is explicitly discarded. Handles are never silently evicted.
- Low-memory mode skips whole-country optional preparation deserialization.
  Existing frozen preparation files remain unchanged. Source identity changes
  cause correct cache misses in normal mode; trusted forecasts recompute without
  retraining or weakening stale-cache validation.

All 500 paths, residual intervals, warning rules, scenario equations, integer
optimization objectives, reserves and donor protections remain intact. LRU limits
change retention, not calculation inputs or accepted decisions.

## Repeatable verification

```powershell
docker build -f backend/Dockerfile -t healthnexus-low-memory .
docker run -d --name healthnexus-memory-after --memory=512m --memory-swap=512m `
  -p 127.0.0.1:18700:8000 -e HEALTHNEXUS_LOW_MEMORY=true `
  -e GEMINI_ENABLED=false healthnexus-low-memory
.\.venv\Scripts\python.exe scripts/measure_deployment_memory.py `
  --container healthnexus-memory-after --cycles 2 --stability-seconds 180 `
  --output artifacts/low-memory-after.json
```

The tool reads Linux server `/proc/1/status` RSS/HWM after each HTTP stage. Startup
is measured once liveness is reachable. The old image runs uncapped so its failure
footprint can be measured; the new container has a real 512 MiB hard limit and no
additional swap. It exercises all seven resource forecasts across both profiles,
national overview/warnings/network map, severe Pune scenarios, actual district and
cross-district plans/maps, constrained planning, saved federation and Copilot
status. It verifies exact canonical totals, conservation and donor protection on
every cycle; scenario/plan handles are explicitly discarded afterward.

The collector requires peak server RSS below 430 MiB and less than 10 MiB range
between completed cycles after cycle 1, plus no OOM/restart or endpoint failure.
If allocator warm-up fails that conservative plateau check, retain the failure
receipt and extend the same container run; do not reset it or relabel the failure.
An intermediate candidate peaked above 512 MiB and was rejected. A later image
settled at 414.6 MiB after initial allocator growth; another three minutes in the
same container proved a plateau. Both cold and extended receipts remain published.

The final machine receipt and RSS table are linked below. Capacity tests are
sequential; they do not establish arbitrary concurrent-load capacity, Render
latency, cloud availability, or real government inventory coverage.

## Preservation and release instructions

The trusted bundle remains 77 files, 72,340,666 bytes, SHA-256
`966f452b95d7bacff92ccfdbb0fce8ba1beb4593ad0bcb8064d6c0d03397f7dd`.
Every restored container asset was checked against its manifest. Saved federation
parameter checksum remains
`d971711083cef53d8b4416eebdf4c76b35d20b94ce62752a3bd4240e4cb42fc8`.
The local API key/.env and historical 50-request ledger are unchanged; provider
requests for this task are zero. Seven explicitly authorized deployment source
changes have new exact preservation pins; all other protected identities retain
their historical pins. This does not weaken model, data or Gemini validation.

Add only `HEALTHNEXUS_LOW_MEMORY=true` to the existing Render service. Keep all
other key, model, fallback, storage and CORS environment values unchanged. The
default Docker build needs no additional Render build setting. After Render
redeploys, verify cloud readiness and the public journey separately.

Angular was rebuilt with production runtime API origin
`https://healthnexus-api-aizt.onrender.com`. A new Firebase deployment is required
for the India-only/saved-evidence UI, but Codex did not deploy Firebase. The user's
existing analytics-off setting is retained; local Firebase cache files are ignored.

## Measured receipts

[Final gate](evaluation/low-memory-deployment.json) ·
[Before](evaluation/low-memory-before.json) ·
[Cold allocator diagnostic](evaluation/low-memory-cold-after.json) ·
[Extended plateau](evaluation/low-memory-after.json) ·
[Cache sizes](evaluation/low-memory-caches.json) ·
[Preservation pins](evaluation/low-memory-preservation.json).


## Final measurements and quality

Current RSS and process high-water RSS are in MiB. After values are the first cold journey in the final image.

| Stage | Before RSS | Before peak | After RSS | After peak |
|---|---:|---:|---:|---:|
| Startup | 296.2 | 328.8 | 188.4 | 188.4 |
| Readiness | 403.4 | 540.2 | 191.6 | 195.6 |
| Forecasts | 473.6 | 540.2 | 362.6 | 379.5 |
| Severe dengue scenario | 478.4 | 540.2 | 368.1 | 379.5 |
| District optimizer | 489.1 | 540.2 | 376.0 | 379.5 |
| Cross-district optimizer | 492.0 | 540.2 | 379.6 | 379.6 |
| Saved federation evidence | 679.5 | 679.5 | 400.9 | 400.9 |

Before maximum current RSS: **679.7 MiB**; peak **714.9 MiB**. Final maximum current/peak RSS: **401.4 MiB**. Final hard-limited container: **9 full cycles**, including two initial cycles and **180 seconds** of additional repeated journeys, all in the same unrestarted container. No OOM, restart, 502 or unexpected endpoint failure. The final cold gate passed both the unchanged 430 MiB ceiling and plateau check.

| Canonical case | Target | Safe capacity | Recommended | Lanes | Unresolved |
|---|---:|---:|---:|---:|---:|
| District ready | 41,763 | 17,745 | 15,679 | 10 | 26,084 |
| Constrained | 30,230 | 0 | 0 | 0 | 30,230 |
| Cross-district Pune ? Nagpur | 41,763 | 9,307 | 9,307 | 10 | 32,456 |

All cases retain zero donor violations/new risks and exact resource conservation. Fourteen complete forecast response hashes match the old Linux image exactly across both profiles. All ten local country/profile model partitions and the genuine saved federation reload/evaluation pass; no accepted artifacts were retrained.

**Quality:** 690 backend tests, 16 ChromeHeadless frontend tests, strict app/spec TypeScript, Angular production build, Python compileall, host/container pip check, Docker build/no-Torch runtime and npm audit (0 vulnerabilities) pass. The one backend warning is an upstream Starlette/AnyIO deprecation. Publication scans find no credentials; actual .env/key, all protected datasets/models and the 50-request ledger remain unchanged. Provider requests: **0**.
