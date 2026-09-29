# Phase 6 — grounded resilience Copilot

The existing Copilot now includes availability failover in the exact requested order: 3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite. All five are mock/SDK-wire tested. Live automatic failover reached 3.6; the first three models returned HTTP 503 HIGH DEMAND, then the preserved ten-request daily ceiling blocked further sends. No live answer or full live acceptance is claimed. [Measured failover report](phase6-failover-report.md). Local planning outcomes remain unchanged. Phase 7 has not started.

## Integration and execution

- Official `google-genai==2.25.0`, `gemini-3.8-flash` primary with the approved stable Flash-family chain; effective model is explicit. SDK dependency requires `pydantic==2.13.5`.
- Recommended stateful Interactions API, native function calls/results and structured JSON answers; previous interaction ID carries conversation state. Tools/system instruction/config are resubmitted on continuation.
- Medium thinking; maximum 2,400 output tokens, 10 tool calls, 60-second provider timeout, 300-second cooperative workflow deadline, two concurrent workflows. Failover uses one attempt per model for eligible availability failures. Explicit model-quota 429 may advance; auth/application/grounding failures never do.
- System prompt `healthnexus-system-v3`, configuration `copilot-config-v4-failover`. Backend `.env` key stays ignored; no browser key or startup inference. Exact model availability/error status is surfaced.
- Thirteen strict tools call existing repository/forecast/warning/scenario/optimizer services. Geography/profile and snapshot/model identities are checked; new scenario/optimizer creation requires explicit permission. No arbitrary code execution or public web tool is offered to Gemini.
- Answer claims reference fresh tool-result fields. Numeric and selected status checks reject unsupported evidence. This does not prove all semantic claims; authoritative typed results remain inspectable independently. No patient-level clinical validation is claimed.
- Sessions/progress/audit are bounded process-local stores, not durable/authenticated production sessions. Google-side stored Interactions history is separate; clearing local state does not delete provider history.

## Real operational evidence from local tools

India → Maharashtra → Pune, severe dengue, 14 days, seed 42, unchanged `forecast-v1-176a752efab3ae4e` artifact. Aggregates below are inventory-item accounting tallies across distinct units, not interchangeable doses.

| Measured field | Redistribution-ready | Constrained |
|---|---:|---:|
| Target before | 41,763 | 30,230 |
| Safe donor capacity | 17,745 | 0 |
| Transferred tally / lanes | 15,679 / 10 | 0 / 0 |
| Target after | 26,084 | 30,230 |
| Expected unmet before | 27,655.2181 | 17,075.1558 |
| Expected unmet after | 17,378.1980 | 17,075.1558 |
| Critical resource warnings before → after | 7 → 0 | 0 → 0 |
| Maximum conditional 14-day stock-out risk | 100% → 100% | 100% → 100% |
| New donor risks / reserve violations | 0 / 0 | 0 / 0 |
| Solver / greedy comparison | OPTIMAL / tie | OPTIMAL / tie |

The positive plan uses Pune PHC 01 and CHC 02 as actual safe donors for District Hospital 03. Five resources participate. Remaining receiver targets: PCM 22,947 tablets, IVF 2,173 bags, ORS 964 sachets; AMX and IFA zero. IVF/PCM 14-day risk stays 100%; AMX/IFA/ORS improves to zero. Resource conservation is checked independently for each medicine. Actual routes, quantities, distances, reserve minima, warning summaries and solver evidence are saved in [offline verification](evaluation/phase6-offline.json), matching stored engine results exactly. Phase 5.5 data, training models and reserve policies are unchanged.

Actual full workflow sequence:

`get_network_summary → run_emergency_scenario → get_scenario_comparison → get_warnings → get_redistribution_preview → optimize_redistribution`

The offline router chooses this documented workflow. Mocked Gemini chooses scripted native calls to verify orchestration. Neither is evidence that a live model chose those calls. A same-conversation donor follow-up retrieves the actual retained optimizer result; provenance explains that government historical calibration does not constitute live inventory.

## Measured performance

Latest offline four-case verifier, one process, on this workstation. Outer duration includes response validation/serialization and fixture checks; tool time is separately measured. These are not controlled cold/warm national benchmarks. Existing Phase 5.5 planning preparation/cache measurements remain documented in [that report](phase55-report.md).

| Workflow / profile | Outer seconds | Tool seconds | Provider seconds | Actual tools |
|---|---:|---:|---:|---:|
| risk / redistribution-ready | 1.687 | 1.625 | 0 | 2 |
| positive / redistribution-ready | 0.398 | 0.343 | 0 | 6 |
| constrained / constrained | 1.933 | 1.860 | 0 | 6 |
| provenance / constrained | 0.067 | 0.004 | 0 | 1 |

Historical mock transport durations are recorded in [mock evidence](evaluation/phase6-mock.json), explicitly labelled `transport: mock`; mock network time is not Gemini latency. Its usage arrays are empty. Separate partial live runs reported actual successful-response usage, but did not finish final acceptance. District baseline preparation dominates the initial risk call; later ready planning reuses immutable local preparations. No model retraining occurs during Copilot requests. Current byte/request diagnostics are in [budget evidence](evaluation/phase6-budget-mock.json).

## Verification and remaining acceptance

281 backend tests pass, preserving the previous 237 and adding 44 failover cases. These cover budget/retry counts, subset enforcement, fresh one-request provenance/follow-up, minimal constrained continuation, alternate valid positive ordering and PASS identity/invalidation. Earlier validation of evidence, scope, clinical refusal, actual donor safety and immutable data remains passing. Python compilation, dependency consistency, strict TypeScript and Angular production build pass. New acceptance matrices pass offline and with a mocked model.

Strict TypeScript and production build: 366.12 kB initial / 100.24 kB estimated transfer; Copilot lazy chunk 21.32 kB / 6.06 kB. All five original snapshot hashes match the committed Phase 5.5 report; see [preservation evidence](evaluation/phase6-preservation.json).

Desktop/mobile browser checks and screenshots are recorded separately in [browser evidence](evaluation/phase6-browser.json). Tested browser mode is explicitly OFFLINE. This verifies UI/engine integration, not Google reasoning. Final UI displays real transfer/reserve tables and remaining resource risks, supports same-conversation follow-ups and context-scoped optimizer links, and resets conversation on profile changes.

[Historical live status](evaluation/phase6-live.json) records the daily-quota failure. Future live verification is authorized only after actual quota reset and explicit user approval; use `scripts/verify_gemini.py --live --acceptance --resume`. The current verifier writes separate budget reports and retains compatible per-case PASS evidence. Final structured/native protocol acceptance remains pending. No Phase 7 or federated aggregation work was added.

## Current numeric grounding work

The [29 September grounding report](phase6-grounding-report.md) supersedes the older live-status notes below for the narrow numeric-contract task. The final full suite passes 385 backend tests, preserving the original 340 cases. Both shared mock model flows and canonical engines pass. Earlier HTTP-200 unsupported-number drafts were not retained, so their exact claims cannot be reconstructed honestly. The new Flash-Lite request returned HTTP 200 / valid schema without numeric literals, but failed one exact citation path. The verifier stopped after one send, retaining the new draft and preserving 22 historical requests (23 cumulative). Full Phase 6 acceptance remains pending; the Phase 8.5 UI/domain engines and strict validator are preserved.

## Current failover validation

See [failover policy, exact live attempt trace, model matrix and limitations](phase6-failover-report.md). Same key/project; no billing change. The latest live smoke sent three provider requests and executed two fresh local reads. There were zero successful interactions or token-usage reports. Positive/constrained Gemini interpretation was not attempted after smoke failed. Both local plans pass mocked and explicit offline acceptance. Provider-stage measurements include verifier pacing. Neither successful live fallback reasoning nor hackathon readiness is asserted yet.

The subsequently authorized targeted smoke tested only 3.5 Flash and Flash-Lite, one request each. Both returned HTTP 503 HIGH DEMAND; no structured answer or successful effective model exists. The existing ten requests were retained and the explicit verifier ceiling extended to 14: final cumulative count **12**, with two unused sends. Schema/evidence/numeric live acceptance, the positive/constrained live workflows and live UI remain pending. [New evidence](evaluation/phase6-targeted-live-smoke.json), [fresh zero-provider offline acceptance](evaluation/phase6-targeted-offline.json). Production order, key, ignored `.env`, engines and model artifacts remain unchanged; Phase 7 remains deferred.

Latest regressions: **289 backend tests pass in 45.88 s**, retaining all 281 previous tests. Python compilation, dependency checks, strict TypeScript and Angular production build pass. [Consolidated targeted verification](evaluation/phase6-targeted-verification.json) separates provider availability, live acceptance gaps and successful local-engine results.
