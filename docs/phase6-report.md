# Phase 6 — grounded resilience Copilot

**Phase 6 fully live-accepted (29 September 2026).** Four live cases pass on Gemini 3.5 Flash-Lite with six actual sends, no retries/fallback/replay; ledger 36 -> 42. All 636 backend tests pass before and after live acceptance. Operational/provenance answers use named semantic slots and deterministic server prose. [Completed acceptance report](phase6-final-acceptance-report.md). Earlier failures below are historical and superseded, with raw evidence preserved.

## Historical checkpoint — bounded prose acceptance

Ordinary provider synthesis now explains recommendations and remaining gaps while server-owned action/solver statuses stay available for UI, audit, validation and explicit questions. The full authority/public schema remains intact; a provider-only view selects current facts, and an additional intent-scoped guard rejects unrequested status narration. Existing action, exact numeric, source/context and WAPE rules are unchanged.

Preflight passed **587 tests**, shared Lite/3.6 official SDK mocks for all four cases, compilation/dependencies, canonical plans, all ten partitions, federation and security/preservation. Exactly three actual Lite sends proved fresh native `run_emergency_scenario → optimize_redistribution` and returned completed JSON. The final remaining-gap wording **“Despite executing recommended transfers”** failed the unchanged action guard. The raw draft and additional paracetamol/worded-duration citation limitations are preserved. Ledger **30 + 3 = 33**; no retry, fallback or B/C/D live case. No completion commit or deployment followed the failed gate. [Preserved prose-attempt report](evaluation/phase6-completion-report-preserved.md), [original live trace](evaluation/phase6-completion-live.json), [independent review](evaluation/phase6-completion-review.json).

Phase 6 remains pending because: the positive synthesis says “Despite executing recommended transfers,” contradicting authoritative physical_execution=false.

## Historical checkpoint — advisory action-state grounding

Optimization tools now expose server-owned advisory mode, false physical execution/external authorization/hospital contact, and not-executed transfer status through fact IDs. A bounded deterministic predicate/clause/facet guard rejects unsupported operational actions and preserves valid transfer nouns and negated action statements. Exact numerical and source membership/resolution code is unchanged. Native medium/2,400 and synthesis low/4,096, canonical engines, artifacts, UI, federation and fallback order are preserved.

Preflight passed 555 tests; final regression passes **556 tests** (484 retained + 72 new), shared Lite/3.6 SDK mocks, compilation, dependencies and security/preservation. Exactly one Lite send returned HTTP 200/completed JSON: 10,156 input / 516 output / 0 thought / 10,672 total tokens, 12.832 seconds. Its remaining-gap claim still says **“optimal advisory transfers executed”** and lacks the scalar OPTIMAL citation. The production solver check rejects it first; exact saved-output offline replay independently confirms action-state failure, zero unknown IDs and no numeric literals. Ledger 29 + 1 = 30; no retry/fallback or later live case. [Full measured report](phase6-action-state-report.md), [original live trace](evaluation/phase6-action-live.json), [independent review](evaluation/phase6-action-review.json).

Native orchestration: **PASS**. Final synthesis: **FAIL**. Positive workflow acceptance: **FAIL**. Full Phase 6 remains pending.

**Positive live workflow remains pending because: the remaining-gap claim describes advisory transfers as executed and mentions optimal without citing solver status.**

## Historical checkpoint — final synthesis budget fix

Native planning remains medium/2,400; final synthesis uses low/4,096 and normally three to five concise claims. Exactly one new Lite request used deterministically reconstructed authoritative evidence, with no native provider calls, retry or fallback. It returned HTTP 200 / completed, complete four-claim JSON, 470 output tokens, zero thought tokens and 11,027 total tokens in 2.958 seconds. The response describes advisory transfers as executed actions and is not accepted. An unnecessary empty-ID guard in the stateless final-only verifier was corrected locally; the original failed trace is retained and no second live request tested the correction. Ledger 28 + 1 = 29. [Measured report and limits](phase6-synthesis-report.md).

Native orchestration: **PASS** from preserved live evidence. Final synthesis: **FAIL**. Positive workflow acceptance: **FAIL**, completion pending. Exact grounding, engines, canonical results, federation, UI and production fallback order remain unchanged. Local regression/security evidence is in [final verification](evaluation/phase6-synthesis-final.json).

**Positive live workflow remains pending because: the completed synthesis describes advisory transfers as executed actions.** Follow-up, constrained and provenance cases were not run live.

## Historical full live attempt — stopped at synthesis

Verifier-selected Flash-Lite performed actual native `run_emergency_scenario → optimize_redistribution`, producing the exact 41,763 / 17,745 / 15,679 / 10 / 26,084 plan with zero donor violations/new risks. The third interaction returned HTTP 200 / `incomplete`, with truncated final JSON; no grounded final answer was accepted. Exactly three sends appended to 25 historical requests (28 total), with no retry, failover or later live case. Accepted fact/numeric grounding, production order, engines, UI, federation and key/project/billing remain unchanged. [Actual evidence and diagnosis](phase6-full-live-report.md).

**Phase 6 remains pending because: the positive workflow's final structured synthesis returned `incomplete` with truncated JSON (`response_incomplete`).**

## Current checkpoint — request-local fact IDs

Gemini now cites request-local fact IDs; the server owns canonical paths, values, units and provenance and runs the unchanged exact numeric checks. **436 backend tests pass**, including all previous 385 cases and 51 new fact/verifier cases. Lite and 3.6 shared mocks, Python/dependency checks, strict TypeScript and production build pass. Operational results, saved federation, UI, `.env` and production fallback order are preserved. Only the conditional, two-send maximum independent Lite smoke is authorized; full Phase 6 workflow acceptance remains pending. [Current report and live results](phase6-fact-citations-report.md).

The earlier integration/failover measurements below are retained history.

**Live grounded smoke acceptance: PASS 2/2. Full Phase 6 workflow acceptance remains pending.** Both fresh Flash-Lite smokes returned HTTP 200 and passed schema, fact IDs, configured qualitative/numeric grounding and context checks, with zero unknown IDs or unsupported numeric claims. Exactly two sends appended to the historical 23 (25 total), with no retry/fallback. [Measured live evidence](evaluation/phase6-facts-live.json), [preservation/security](evaluation/phase6-facts-security.json).

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


## Historical list-frame checkpoint (superseded by named slots)

Operational planning, donor follow-up, plan review and provenance synthesis use `GroundedResponseFrame`. Gemini selects permitted claim kinds and exact request-local fact IDs; it cannot supply operational prose, numbers, names, durations or arbitrary qualifiers. HealthNexus validates the whole frame before its deterministic renderer creates the existing public Claim objects. Invalid kinds, incomplete evidence, stale IDs, changed source identities and incompatible context fail visibly without repair or fallback to prose.

Required fact combinations and predicates cover advisory recommendations, partial relief, residual shortages, protected donors, zero-capacity networks and provenance distinctions. Execution and solver status are available only for explicit status questions. All existing exact-number, action-state, solver, WAPE, source and context validators still run after rendering; legacy/general intents retain their guarded text contract. The public UI and operational engines are unchanged.

Audit separates the exact `provider_semantic_frame` from `server_rendered_claims`, and response metadata identifies the prose author as the HealthNexus deterministic renderer. Rendered wording is not verbatim Gemini wording. Shared SDK mocks use the same protocol on Flash-Lite and 3.6; live acceptance remains pending until all four fresh cases pass. The previous three-send failed free-text run and its citation-gap review remain historical evidence.

The new verifier is `python scripts/verify_phase6_frames.py --mock` / `--preflight` / `--live`. Live mode requires a matching completed local gate, current user-confirmed provider headroom, the preserved 33-request ledger and an unused independent journal. It allows six actual Flash-Lite sends total (3 + 1 + 1 + 1), with no retry, fallback or replay, and stops on the first failure. It never resets the ledger or infers provider quota from it. See [final acceptance report](phase6-final-acceptance-report.md) for the measured verdict.

Historical list-frame live outcome: three actual Flash-Lite sends; native scenario/optimizer and frame schema passed, but repeated `RESOURCE_PRESSURE` caused `duplicate_kind` rejection before rendering. B/C/D were not attempted. Ledger 33 → 36; no retry, fallback, replay or commit. Phase 6 remains pending. See [the preserved frame report](evaluation/phase6-frame-report-preserved.md).


## Current named-slot contract and closed acceptance

`GroundedResponseSlots` accepts a strict named claims object containing only current evidence IDs. `grounded-semantic-slots-v2` replaces the provider list; the internal list is used only after structural decoding. Whole-frame validation precedes deterministic rendering. Duplicate JSON properties are errors, not normalized selections. Positive planning exposes four required slots; donor follow-up and constrained explanations expose their three required slots; provenance exposes nine. Raw provider output and rendered prose remain separate audit objects.

`scripts/verify_phase6_slots.py` supplied the new independent six-send acceptance, preserving the prior failed journals and 36 historical requests. Its completed live journal is terminal at six sends; the cumulative ledger is 42. This authorization cannot be replayed. All A/B/C/D cases and final regressions pass; no additional provider calls occurred after D. The final live model was Gemini 3.5 Flash-Lite; primary/fallback production configuration remains unchanged. [Final receipt](evaluation/phase6-slots-final.json).
