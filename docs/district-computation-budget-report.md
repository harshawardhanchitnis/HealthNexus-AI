# District computation budget — 2026-10-01

This release applies the approved memory cuts to the explicit
`HEALTHNEXUS_LOW_MEMORY=true` public runtime. Nationwide India browsing,
facilities, inventory and the network map remain available. Live warnings,
simulations, forecast-map preparation and Copilot calculations require a district
or a facility. Redistribution requires a receiver district and either District
or Cross-District scope. The latter covers at most two districts within one
state and twelve facilities, including the accepted Pune/Nagpur example.

State/national live computation is refused before model preparation. The UI
explains the limit and provides a Select Pune link. It does not present missing
calculations as zero risk. The warning and redistribution deep links inherited
from the overview now show this usable selection state. Normal local mode
(`HEALTHNEXUS_LOW_MEMORY=false`) retains unrestricted behavior, including when
server capabilities arrive after the initial page render.

## Memory ownership

- One operational HTTP request runs through complete response serialization.
  Concurrent operational work returns controlled 429 `operational_busy` with
  Retry-After; no work queue is retained. Status, progress and small navigation
  metadata stay responsive. GET reads retry only this explicit rejection, three
  times at most. Writes and provider errors are never automatically retried.
- POST request bodies are bounded to 32 KiB. Oversized requests return 413 before
  application execution.
- One active inventory profile snapshot is retained. Switching profiles reloads
  the unchanged immutable file; both profiles remain available. Existing saved
  scenarios and plans retain their independent validated results.
- One India model bundle is shared by lightweight profile bindings. Prediction
  points retain 128 entries; forecast preparation and baseline projection caches
  retain six facilities each. Optimizer preparation retains one bounded entry.
- Two scenario handles and three plan handles can coexist, enough for district,
  cross-district and constrained examples. New runs return an explicit capacity
  error until a result is discarded; existing handles are not silently replaced.
- Copilot retains four conversations, eight request records and eight audit
  records. Expired conversation IDs return the existing explicit 404. Provider
  orchestration, evidence, semantic slots, grounding and failover order are intact.
- Native numerical threads are limited to one before model imports. Docker starts
  glibc with two allocator arenas. After a serialized request, optional Linux
  `malloc_trim(0)` returns unused allocator pages without freeing live objects or
  evicting application caches.
- Artifact hashes stream all bytes in 64 KiB chunks. In low-memory mode an
  optional Linux `POSIX_FADV_DONTNEED` hint releases already-read immutable file
  pages. This is a file-specific cache hint, not a host-wide cache flush. Hash,
  compatibility and stale-artifact validation remain complete. Unsupported
  platforms/filesystems use ordinary reads.
- The public image contains no PyTorch. Verified five-node federation evidence
  remains available; genuine training is preserved for the opt-in local image.

All 500 sampled demand paths, reserves, forecast/warning/scenario equations,
OR-Tools objectives and constraints remain unchanged. MapLibre/OpenFreeMap,
illustrative geography, optimizer distance inputs and advisory action state stay
intact. No generated data, model, portable bundle or saved federation artifact
was regenerated or retrained.

## Preserved measured outcomes

Mixed medicine totals are accounting sums; actual physical units remain per lane.

| Severe 14-day Pune dengue | Target | Safe capacity | Recommended | Lanes | Remaining |
|---|---:|---:|---:|---:|---:|
| Redistribution-ready, district | 41,763 | 17,745 | 15,679 | 10 | 26,084 |
| Redistribution-ready, Pune receiver / Nagpur donors | 41,763 | 9,307 | 9,307 | 10 | 32,456 |
| Constrained, district | 30,230 | 0 | 0 | 0 | 30,230 |

All cases preserve zero donor violations, zero new donor risks and exact resource
conservation. The canonical verifier checks all ten country/profile model
partitions and genuine saved federation reload locally. The public memory
journey recomputes all three plans and verifies their actual map lanes each cycle;
no saved optimizer answer is substituted.

## Reproduce the capacity gate

```powershell
docker build --no-cache -f backend/Dockerfile -t healthnexus-district-memory .
docker run -d --name healthnexus-budget --memory=450000000 --memory-swap=450000000 `
  --cpus=0.1 -p 127.0.0.1:18715:8000 -e HEALTHNEXUS_LOW_MEMORY=true `
  -e GEMINI_ENABLED=false healthnexus-district-memory
.\.venv\Scripts\python.exe scripts/measure_compute_budget.py `
  --container healthnexus-budget --base http://127.0.0.1:18715 `
  --cycles 2 --stability-seconds 180 --output artifacts/district-memory.json
```

450 MB means **450,000,000 bytes**, not 450 MiB. The collector reads cgroup v2
current/peak memory, including charged file cache and container processes, plus
the server's RSS and high-water RSS. It never starts a second scientific Python
process inside the constrained container. Docker may charge shared mapped library
pages to another cgroup: the release gate therefore also adds the largest sampled
server file RSS once again as a conservative allowance. That allowance is an
estimate, not another measured peak, and deliberately counts already-charged
mapped files again. Both the measured peak and this allowance must fit below
450 MB, with zero forced limit-reclamation events, OOMs and restarts.

The journey includes an eight-request concurrent cold forecast burst, explicit
national computation rejections, seven resources across both profiles, district
warnings and maps, all three real optimizations, full stores, explicit offline
Copilot tool calls, profile switching and saved federation. Two initial cycles
are followed by at least three minutes of repeated complete journeys in the same
unrestarted container. The plateau check compares retained server RSS and
per-cycle minimum cgroup usage across the final three cycles, within 10 MB.
Healthcheck subprocess allocations still count in the peak.

Earlier attempts and failed plateau receipts remain retained as diagnostics.
A cold attempt approached 450 MB with forced reclamation despite no OOM and
was rejected for release headroom. Streaming alone did not solve that overhead;
allocator cleanup and one active inventory snapshot were also needed. A host
restart interrupted another attempt before it produced a report; Docker recorded
no OOM for that interruption, and no PASS is claimed for it.

## Actual final measurements

The final no-cache backend image is
`sha256:78b3e3ddc20def074eff52a430a207e968af4c64b3bb4f33ce0af3058abe86b5`.
Two initial cycles plus four stability cycles ran in the same container with a
450,000,000-byte memory/swap limit and 0.1 CPU. The measured cgroup peak was
**336,113,664 bytes (336.1 MB)**; maximum sampled server RSS was 347.3 MB,
and server high-water RSS was 396.1 MB. These are different measures and are not
interchangeable. All memory-limit, OOM and restart counters remained zero.
The retained-memory plateau passed.

The largest sampled server file RSS was 80,019,456 bytes. Adding that allowance
to the measured peak yields **416,133,120 bytes (416.1 MB)**, 33.9 MB below
the target. The raw run used the earlier collector before this allowance was
added; the independent release receipt calculates it from that unchanged raw
record. The current reproduction command applies both checks directly.

| First complete journey stage | Server RSS, MB | Charged cgroup memory, MB |
|---|---:|---:|
| Startup | 198.6 | 151.5 |
| Readiness | 202.1 | 144.0 |
| Ready forecasts | 303.9 | 242.2 |
| Constrained forecasts | 275.7 | 213.2 |
| Ready scenario | 281.2 | 219.2 |
| District optimizer | 294.7 | 224.9 |
| Cross-district optimizer | 301.9 | 231.9 |
| Saved federation | 302.3 | 231.9 |

The preceding release's cold RSS-only receipt reached approximately 420.9 MB.
That historical RSS figure cannot be compared as total cgroup memory. Returning
unused allocator pages, releasing already-read artifact pages and retaining only
one inventory snapshot reduced resident overhead in this run. Startup reached
liveness in 43.1 seconds and readiness in 47.1 seconds at 0.1 CPU. First-cycle
district, cross-district and constrained planning took 2.52, 3.91 and 2.39 seconds.

**710 backend / 22 frontend tests pass**, together with strict TypeScript,
Angular production build, compileall, host/container dependency checks and npm
audit (zero vulnerabilities). The canonical and cross-district verifiers,
fourteen unchanged forecast hashes and saved federation reload pass. Desktop
and 390-pixel mobile review uses actual scenario/optimizer results, with clean
captured consoles, ten cross-district lanes and zero constrained lanes. National
warning/planner links show a district-selection notice; the map retains all 207
fictional facilities. [Actual captures](screenshots/district-budget/README.md).

Receipts: [independent release gate](evaluation/district-budget-release.json),
[raw final cold run](evaluation/district-memory-cold.json),
[canonical demo](evaluation/district-budget-demo.json),
[cross-district verifier](evaluation/district-budget-cross.json),
[rejected cold attempt](evaluation/district-memory-rejected-cold.json),
[rejected plateau attempt](evaluation/district-memory-rejected-plateau.json).

## Rollout and limits

The only required Render environment setting remains
`HEALTHNEXUS_LOW_MEMORY=true`. API key/project, Gemini settings, storage and CORS
must retain their existing values. `GEMINI_ENABLED=false` above is a local
zero-provider test setting, not a requested production change. Pushing the
verified commit to the existing `origin/main` triggers its configured Render
auto-deploy. No new service or billing is needed.

The production Angular build retains
`https://healthnexus-api-aizt.onrender.com` in its public runtime configuration.
**Firebase redeployment is required and was not performed by Codex.** The UI
changes will not appear on the public site until that build is published.

Local finite testing cannot guarantee arbitrary traffic stays below 450 MB or
prove that Render's cloud failure is fixed. Cloud memory and the public journey
must be checked after the existing service redeploys. This task makes zero live
Gemini calls; `.env`, the key and the historical 50-request ledger are unchanged.
