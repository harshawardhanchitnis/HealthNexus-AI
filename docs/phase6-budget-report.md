# Phase 6 acceptance under a Free Tier request budget

28 September 2026. Efficiency work verified with **zero live Gemini requests**. Exact model `gemini-3.8-flash`, SDK `google-genai==2.25.0`. Billing, data profiles, forecast artifacts, donor policy and OR-Tools are unchanged. Phase 7 has not started. Live acceptance remains pending; mock PASS does not constitute Google acceptance.

## Why the daily quota was exhausted

The account's reported limits are 5 RPM, 250K TPM and 20 RPD. Each Interactions continuation consumes another provider request, even when it just returns tool results or formats an answer. Diagnostic requests and repeated partial verification attempts shared that daily quota. Google's actual 429 identified **20 requests per day**, rather than a solver or authentication failure. We cannot reconstruct every account-wide request from the application's partial logs.

The old scripted suite required **23 nominal requests before an additional follow-up or reliability check**: risk 4, positive 8, constrained 8, provenance 3. HTTP-level mocks also exposed a hidden retry: SDK 2.25.0's parent normalizes retry attempts 0 to 1, and the Interactions bridge interprets 1 as a retry count. Parent `HttpRetryOptions(attempts=1)` therefore did not actually disable Interactions retries, including 429 retries. Earlier audit counts were `create()` calls and could undercount HTTP sends. The exact account-wide total remains unknown. The actual generated Interactions resource's nullable `sdk_configuration.retry_config` is now explicitly set to `None`; HTTP mocks prove one send on RPD and no send after local budget denial. This is pinned-SDK behavior, not a custom HTTP replacement.

The most advanced earlier live attempt gathered native tools but hit quota before final synthesis. Its successful-response usage was 39,811 input / 235 output / 2,854 thinking tokens; failed-request usage was unavailable. Historical evidence remains in [live acceptance](evaluation/phase6-live-acceptance.json), unchanged.

## New matrix and exact mocked sequence

| Provider request | Input / resulting local operation |
|---|---|
| 1 | Positive Pune severe dengue, 14 days: mocked Gemini selects `run_emergency_scenario` |
| 2 | Scenario function result: selects `get_scenario_comparison`, `get_warnings`, `get_redistribution_preview` in one interaction |
| 3 | Three native results: selects `optimize_redistribution`; actual OR-Tools selects routes/quantities |
| 4 | Optimizer's native function result plus its call ID and previous interaction ID, with answer schema and no tools: structured final |
| 5 | Same conversation donor follow-up, previous final interaction ID, fresh server-read `get_optimization_result`: structured explanation |
| Local setup | Constrained scenario and optimization fixture computed by existing engines, outside Gemini |
| 6 | Constrained question with actual fixture IDs: selects `get_optimization_result` |
| 7 | Saved-plan native function result, previous interaction ID, answer schema and no tools: structured zero-donor interpretation |
| 8 | Provenance plus forecast accuracy: fresh server-read `get_data_provenance` and `get_model_performance`, one schema-only interpretation |

Measured mock total: **8 provider requests, 9 request-local tool executions, plus 2 local fixture tools**. Expected count is 8; the hard maximum is **10 including retries**. A real model may choose another valid order or need more corrections. Completion in eight requests is not guaranteed: the eleventh request is blocked locally with `quota_budget_exhausted_locally`. An alternative valid three-request positive sequence is tested; production code does not contain the mock sequence.

This covers model access, native function calling, multiple tools, structured output and positive grounding through the flagship; zero-donor grounding through the constrained result; provenance/reliability through fresh source/evaluation evidence; and conversation continuity through the follow-up. Provenance and follow-up local reads are explicitly audited as **server-prefetch**, not falsely described as model-selected native calls. The constrained fixture setup is also separate in the report. No standalone access/hello-world call is included.

## Synthesis and context changes

The observed endpoint rejected tools plus `response_format` together. That incompatible combination is still avoided. The optimizer/plan result now goes directly into the next **schema-only continuation of the same native chain**, without first asking for a readiness marker. Structured synthesis remains, but its extra readiness round trip is eliminated. General discovery questions can retain the bounded readiness/synthesis path. Server-prefetched read-only cases need just one schema request. Official-SDK HTTP mocks verify serialization of native result IDs, previous interaction ID and schema-only continuation. Google's acceptance of this revised continuation **has not been tested live**.

Every answer still passes strict Pydantic schema, exact fresh-field resolution, numeric grounding, solver terminology and executed-transfer checks. Planning permission, clinical refusal, tool/input limits, country/profile/geography and stale-artifact rejection remain. Numeric tables still use complete server-owned operational objects. Compact provider views preserve returned values and array indices; they omit repeated transfer metadata, duplicated assumptions, model hyperparameters and irrelevant evaluation breakdowns.

Measured compact JSON bytes (not Gemini token counts):

| Context | Before | After |
|---|---:|---:|
| Full / emergency tool schema per native turn | 11,363 | 7,843 (31% smaller) |
| Full / network-risk schema | 11,363 | 4,997 |
| Full / plan-review schema | 11,363 | 1,777 |
| Full / provenance approved schema | 11,363 | 1,265; not sent in server-prefetch synthesis |
| System instruction per request | 2,917 | 2,566 |
| Positive workflow operational payloads sent to model | 67,628 | approximately 35,238 (48% smaller) |
| Fresh follow-up plan payload | 23,299 | approximately 8,391 (64% smaller) |
| Provenance plus performance authoritative / compact payloads | 15,845 | approximately 5,326 (66% smaller) |

Request diagnostics include schema, system, input and complete body bytes; tool diagnostics separate authoritative/model payload bytes. A labelled characters/4 heuristic estimates tokens. These estimates exclude opaque stored-history effects and are **not actual Gemini usage**. IDs/timings can slightly change byte counts. The former 19 tool-bearing turns sent about 215,897 schema bytes; the new matrix's four tool-bearing turns send about 25,306, an 88% reduction across the different acceptance matrices. The flagship still checks resource risks, replacing the separate baseline-risk workflow.

## Budget, errors and resumable evidence

`GEMINI_DAILY_VERIFICATION_BUDGET=10` or `--budget 10` sets the verifier cap; allowed range is 1–10. The transport reserves budget **before each attempt**, including its one allowed 502/503 retry. SDK retries remain disabled. Audit reports provider requests separately from successful interactions and local tools. Other applications and UI requests are outside this verifier ledger; the guard cannot replace Google's account quotas.

The live verifier persists its UTC-day ledger at `artifacts/gemini-verification-budget-live.json`. Repeated selective/resume CLI runs share it. A process lease prevents concurrent CLI runs from racing this ledger. An interrupted process may leave `artifacts/gemini-verifier.lock`; remove that small lock only after confirming no verifier still runs. Do not delete/reset the daily ledger to manufacture quota. UTC ledger rollover does not imply Google's quota has reset; wait for actual reset and explicit authorization.

Live attempts are paced at least 13 seconds apart for the reported 5 RPM tier. HTTP 429 is never automatically retried: RPM/TPM/RPD are classified separately, safe Retry-After/RetryInfo hints retained, and the run stops. RPD exhaustion needs a later authorized run, not repeated waiting/retries. The application suggests retrying later or explicit offline mode; it does not suggest billing.

Each completed case is atomically saved immediately under `artifacts/gemini-acceptance/live/`. Mock/offline records use separate directories and cannot count as live evidence. `--resume` retains compatible PASS cases after failures/quota. Identity includes git commit, implementation hash, exact model, installed SDK, prompt/hash, tool schema hash, profile/config versions, effective configuration, credential fingerprint and both profile snapshot/model hashes. Material changes invalidate evidence. Git commit remains recorded; a docs-only commit with identical implementation/artifacts can reuse evidence.

If positive PASS survives but follow-up is pending across processes/days, the verifier rebuilds current **real local** fixtures, restores only the opaque previous provider interaction ID, and sends fresh plan evidence. It never assumes old model memory contains current numbers. Provider history must still be retained by Google; an expired provider ID fails visibly and requires renewed positive evidence. Local evidence contains no key, headers, patient data or private reasoning. Existing general session expiry remains unchanged.

The mock budget-stop experiment retained positive after four requests, then blocked the follow-up before sending it. A separate resumed process reused positive and finished the remaining cases in **four requests**. See [stop](evaluation/phase6-budget-stop-mock.json) and [resume](evaluation/phase6-budget-resume-mock.json). Full [mock](evaluation/phase6-budget-mock.json), [offline](evaluation/phase6-budget-offline.json) and selective positive/constrained/provenance reports remain distinct from historical live evidence.

## Commands

Safe checks now:

```powershell
.\.venv\Scripts\python.exe scripts\verify_gemini.py --mock --acceptance
.\.venv\Scripts\python.exe scripts\verify_gemini.py --offline --acceptance
```

**Future commands only after actual quota reset and explicit user authorization:**

```powershell
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --acceptance --resume
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case positive --resume
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case constrained --resume
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case provenance --resume
```

Default new report is `docs/evaluation/phase6-budget-live.json`; old live reports are preserved. `--output` and `--evidence-dir` are available. No live command above was executed during this efficiency work.

## Validation and preserved engine outcomes

**237 backend tests pass**, including the original 210 and 27 added cost-free quota/protocol cases. Python compilation, dependency checks, strict TypeScript and Angular production build pass. Initial bundle remains 366.12 kB / estimated 100.24 kB transfer; Copilot lazy chunk 21.32 kB / 6.06 kB. No frontend implementation changed. One upstream Starlette/AnyIO deprecation warning remains.

The ready severe Pune scenario remains 41,763 target / 17,745 safe capacity / 15,679 transferred inventory items over 10 lanes / 26,084 unresolved. Expected unmet demand falls from 27,655.2181 to 17,378.1980; donor risks/violations remain zero. Critical resource warnings fall from 7 to 0, but maximum conditional stock-out risk remains 100%. OR-Tools and greedy tie. Constrained remains **30,230 unresolved, zero safe capacity and zero transfers**, correctly OPTIMAL under the constraints. Baseline/profile data remains immutable.

Phase 6 revised live acceptance is ready for the next authorized quota window, not yet passed. Phase 7 remains deferred.

## Failover extension — 28 September 2026

The preceding measurements describe the historical efficiency change. Current configuration v4 adds the five-model chain and model-aware ledger while keeping the same global ten-request daily ceiling. Three new live attempts (3.8, 3.7, 3.6; one each) returned 503 and exhausted the remaining local allowance. No reset/key/billing change occurred. Completed PASS still requires material identity compatibility including chain/config and credentials. The current resilience smoke is one schema interpretation after two fresh audited local reads. [Current failover report](phase6-failover-report.md).

## Explicit targeted extension — 28 September 2026

The user authorized a bounded verifier-only extension to 14 cumulative sends. Default/environment limits remain 1–10; explicit CLI `--budget 14` permits up to 14 while retaining the same daily ledger. `--case model-smoke --model gemini-3.5-flash` skips previously tested models without changing the production order, and reaches Lite only on an eligible availability failure. Model selection is included in PASS identity. Compatible smoke PASS restores the actual effective model for subsequent sticky positive verification.

The targeted live smoke consumed **two** sends: 3.5 Flash and Flash-Lite each returned HTTP 503 HIGH DEMAND. History remains **10 + 2 = 12/14**, with two unused sends. No positive/provenance/constrained live interpretation or browser call followed the failed smoke. [New exact trace](evaluation/phase6-targeted-live-smoke.json). Historical 503 evidence remains unchanged. This extension does not estimate or alter Google quota, change keys/projects, enable billing or reset the ledger.
