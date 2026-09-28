# Phase 6 — grounded resilience Copilot

The official Gemini integration, registered tools, structured evidence, conversation state and Copilot UI are implemented. **Live acceptance remains pending: no server API key is configured.** No Google inference was performed and no inference latency/token usage is invented. Both real local planning outcomes remain unchanged. No FedAvg is implemented.

## Integration and execution

- Official `google-genai==2.25.0`, exact `gemini-3.8-flash`; no substitute model. SDK dependency requires `pydantic==2.13.5`.
- Recommended stateful Interactions API, native function calls/results and structured JSON answers; previous interaction ID carries conversation state. Tools/system instruction/config are resubmitted on continuation.
- Medium thinking; maximum 2,400 output tokens, 10 tool calls, 25-second provider timeout, 120-second workflow deadline, two concurrent workflows. Only transient 502/503 receive one bounded retry. Quota/authentication failures are not retried.
- System prompt `healthnexus-system-v1`, configuration `copilot-config-v1`. Backend `.env` key stays ignored; no browser key or startup inference. Exact model availability/error status is surfaced.
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

Mock transport durations are recorded in [mock evidence](evaluation/phase6-mock.json), explicitly labelled `transport: mock`; mock network time is not Gemini latency. Usage arrays are empty because no real provider reported tokens. Live inference time, token cost and real model behaviour remain unknown. District baseline preparation dominates the initial risk call; later ready planning reuses immutable local preparations. No model retraining occurs during Copilot requests.

## Verification and remaining acceptance

207 backend tests pass (156 preserved plus 51 Copilot cases), final full run 27.23 seconds. The new cases exercise native SDK wire format without network, sequential tools, invalid arguments/evidence, provider failures/retries, configuration, workflow limits, session state, profile/geography isolation, stale scenarios, API contracts, clinical refusal, real donor safety/conservation and unchanged constrained results. Python compilation, dependency consistency, strict TypeScript and Angular production build pass. Four actual-engine workflows pass both offline and mocked-model verification.

Strict TypeScript and production build: 366.12 kB initial / 100.24 kB estimated transfer; Copilot lazy chunk 21.32 kB / 6.06 kB. All five original snapshot hashes match the committed Phase 5.5 report; see [preservation evidence](evaluation/phase6-preservation.json).

Desktop/mobile browser checks and screenshots are recorded separately in [browser evidence](evaluation/phase6-browser.json). Tested browser mode is explicitly OFFLINE. This verifies UI/engine integration, not Google reasoning. Final UI displays real transfer/reserve tables and remaining resource risks, supports same-conversation follow-ups and context-scoped optimizer links, and resets conversation on profile changes.

[Live status](evaluation/phase6-live.json): not run, missing server key, zero provider requests. To complete live acceptance, configure the ignored backend key, restart the service and run `scripts/verify_gemini.py --live`. The verifier fails visibly on exact-model/provider/evidence errors and writes sanitized results. Do not declare live completion until those checks pass. Code boundaries are prepared for future Phase 7 country nodes; no federated aggregation was added.
