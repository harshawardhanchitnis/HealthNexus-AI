# Phase 6 final bounded acceptance — 29 September 2026

Continues **a62f098**, with a verified clean working tree before any change. This run implemented the ordinary-narrative boundary and attempted the authorized fresh native workflow. **Native scenario and optimization orchestration passed; positive final synthesis failed.** The verifier stopped after three actual sends. B/C/D were not attempted. Phase 6 is not fully live-accepted.

## Contract change

Ordinary Gemini operational synthesis now explains pressure, recommendations, projected benefit and remaining gaps. It does not own execution, authorization, hospital contact or mathematical solver-status narration. `operational-narrative-v1` and prompt `healthnexus-system-v8-recommendation-narrative` apply this boundary.

The provider-only view retains recommendation/impact facts and advisory plan mode, while omitting unrequested execution/authorization/contact facets and solver-status facts. Its citation enum contains only current selected fact IDs. The complete server catalogue and operational results retain all authoritative statuses. Explicit status questions expose the relevant current facts and require exact citations. An additional intent-scoped narrative check rejects unsolicited status language; the existing action, solver, exact-number, source, origin, scope, stale-ID and WAPE guards remain intact. This does not globally ban status words from unrelated intents.

The public response schema/UI is unchanged. No model-specific answer branch exists. The existing 64-fact cap remains; a few actual donor reserve/resource/rationale fields are prioritized so follow-ups can cite concrete protection evidence. Provenance tools now expose server-owned interpretation facts for public inputs, fictional operations, derived forecasts, scenarios, advisory optimization, WAPE, experimental federation and absence of government/hospital connections. These are capability/data-layer descriptions, not new operational calculations.

Claims about advisory mode cite plan mode; they do not need physical execution, authorization or hospital-contact citations unless those topics are discussed. Claims need only the numerical/operational facts they discuss; they are not required to recite every canonical metric. Every cited value still passes the unchanged exact validation. Raw provider drafts remain sanitized but otherwise unmodified in audit evidence on success and failure.

Authoritative state remains:

```text
plan_mode = advisory
physical_execution = false
externally_authorized = false
hospital_contacted = false
real_world_transfer_status = not_executed
solver.status = OPTIMAL (mathematical status only)
```

## Local preflight

- **587 backend tests passed in 201.33 seconds**: all 556 previous cases retained plus 31 new narrative/budget/production-audit/failure-stop cases. One existing Starlette/AnyIO deprecation warning remains.
- Shared model-independent **official SDK HTTP mocks** passed all four cases on Flash-Lite and 3.6: three native positive interactions, one same-conversation follow-up, one constrained interpretation and one provenance synthesis per model. **Zero live requests** occurred in mocks.
- The previous phrases “optimal advisory transfers executed,” “executing safe transfers,” and “Despite executing authorized transfers” remain rejected. Requested safe-language examples pass. Explicit false execution answers and scalar solver-status citations remain supported for direct questions.
- Mock 429/503 failures stop after one send; unsafe final synthesis stops after three. No retry, fallback or next case follows. Global six-send accounting, pacing, terminal/replay protection and exact raw draft retention are tested.
- Compilation, `pip check`, credential scan and preservation checks pass. Frontend sources/build are unchanged; the previous successful strict TypeScript/Angular production build is preserved, not claimed as newly rerun.
- Both actual canonical plans, all ten country/profile partitions and saved federation reload/evaluation pass. The original action-state validator, numeric/evidence builder and exact fact resolution/membership/context validation are unchanged.
- Previous **2/2 live grounded smokes** remain preserved with their original source hash; no new smoke was sent.

[Preflight gate](evaluation/phase6-completion-preflight.json), [Lite shared mocks](evaluation/phase6-completion-gemini-3.5-flash-lite-mock.json), [3.6 shared mocks](evaluation/phase6-completion-gemini-3.6-flash-mock.json), [canonical/federation verification](evaluation/phase6-completion-canonical.json).

## Provider accounting

Starting ledger **30**; new actual sends **3**; final ledger **33**. All three requested `gemini-3.5-flash-lite`. Its retained count increased **11 → 14**. The original ledger day and every other historical field/model count remain unchanged.

| Case | Actual sends | Result |
|---|---:|---|
| A — positive native workflow | 3 | Native tools PASS; final synthesis FAIL |
| B — donor follow-up | 0 | Not attempted: A failed |
| C — constrained interpretation | 0 | Not attempted: A failed |
| D — provenance/reliability | 0 | Not attempted: A failed |

There was no fourth send, retry, fallback, replay, extra model, smoke or browser Gemini test. An exclusive terminal journal prevents this authorization from being resumed or replayed; its unused ceiling is not authorization for a new run. Pacing used a minimum 20-second interval between actual send starts. Local accounting is not provider quota; no quota/reset/headroom figure is inferred from it.

## Positive native workflow

The actual clean question was the authorized severe 14-day Pune dengue request, with no canonical answers embedded in it. Geography/profile was **IN / MH / MH-PUNE / redistribution-ready**. All interactions used `store=true`.

1. Send 1 returned `requires_action` for `run_emergency_scenario`. Native arguments passed strict Pydantic and geography/profile checks. Severity was severe, duration 14 and server-default seed 42.
2. Send 2 continued the actual first interaction and returned `requires_action` for `optimize_redistribution`, using the returned scenario ID and district scope. Current snapshot/model/scenario identity passed validation.
3. After the actual optimizer returned, tools were disabled. Send 3 supplied its actual function-result call ID and current fact catalogues, with low/4,096 structured synthesis. It returned completed JSON but failed factual acceptance.

Only `run_emergency_scenario` and `optimize_redistribution` were declared during native acceptance. The engines determined the plan independently:

| Authoritative positive result | Measured |
|---|---:|
| Target before | 41,763 |
| Safe donor capacity | 17,745 |
| Planned accounting items | 15,679 |
| Transfer lanes | 10 |
| Unresolved target | 26,084 |
| Donor violations / new donor risks | 0 / 0 |
| Mathematical solver status | OPTIMAL |
| Conservation / protected donor minima | PASS / PASS |

Scenario ID: `ea1812dc-a7a5-42de-8a5d-672a00489f85`. Optimization ID: `b97442e8-7210-40af-835c-b6a701897f55`. These are fresh objects created by the real native workflow, not reconstructed prior IDs or a stored answer. Full engine objects are preserved as audit-only evidence and were not inserted into the provider narrative.

## Positive synthesis

HTTP **200**; provider **completed**; complete four-claim JSON; Pydantic schema **PASS**. The exact remaining-gap claim was:

> Despite executing recommended transfers, a significant target deficit and expected unmet demand persist across the district, highlighting ongoing operational vulnerability.

The unchanged production action guard rejected **“executing recommended transfers”** in `remaining_gaps.0.text` with `unsafe_claim / unsupported_execution_or_authorization`. It contradicts `physical_execution=false` and `real_world_transfer_status=not_executed`. “Recommended” does not make execution true. The draft was not repaired, reinterpreted as hypothetical, replaced or retried.

Independent **offline** review reconstructs the exact original catalogue, provider view and schema from the saved engine objects and original nonce. It resolves every original ID against the original source values. This review adds no provider sends and does not turn the rejected response into an accepted answer.

| Check | Result |
|---|---|
| Schema / current fact membership | PASS / PASS |
| Unknown fact IDs | 0 |
| Source country/profile/scope/origin | PASS |
| Existing digit-based exact-number check | PASS; no digit numeric literals |
| Unsupported digit numeric literals | 0 |
| Action-state semantics / qualitative acceptance | FAIL / FAIL |
| Unsupported execution claims | 1 |
| Solver terminology | No solver/optimal narration; no solver terminology failure |

Manual citation review also found that the first two claims name **paracetamol**, while their specific resource references are to IVF/ORS and aggregate warnings, not the paracetamol row. The underlying scenario does contain paracetamol, but that does not satisfy same-claim citation coverage. The situation claim's worded **“fourteen-day”** matches the actual engine input but lacks its duration fact citation; the digit-only numeric matcher does not certify spelled-out numbers. These limitations are disclosed rather than labelled fully grounded. The recommendation's claim about several critical deficits is supported by its cited `critical_deficits_resolved=2`; it is not treated as complete shortage resolution.

The original generic citation diagnostic associates the action error with the first audit row; the specific action diagnostic identifies the actual remaining-gap field. The original trace is unchanged. [Raw live evidence](evaluation/phase6-completion-live.json), [separate exact saved-output review](evaluation/phase6-completion-review.json).

## Same-conversation follow-up

**Not attempted live.** Case A did not produce an accepted final answer, so no send 4 was authorized by the gate. Shared SDK mocks passed actual previous-interaction continuity, a fresh local `get_optimization_result` read, fresh fact IDs, donor protection evidence and remaining-gap explanation. This is mock evidence only.

The implementation repeats interaction-scoped settings and retains stored interactions for continuity, following [Google's Interactions documentation](https://ai.google.dev/gemini-api/docs/interactions-overview). No provider history was blindly substituted for current local evidence.

## Constrained

**Not attempted live.** Local canonical verification reproduces **30,230 target/unresolved; zero safe capacity, planned transfers and lanes; zero donor violations/new risks**. Both shared mock models correctly explain reserve-protected network insufficiency. No live interpretation or invented donor is claimed.

## Provenance

**Not attempted live.** Both shared SDK mocks pass the requested public-input versus fictional-operation, forecast, scenario and advisory-plan distinctions, non-clinical validation, WAPE-as-error, experimental federation and no connected government/hospital systems. These authoritative interpretation facts are available to the existing tools. This does not establish live model acceptance of Case D.

## Performance

Actual provider-reported usage is retained, including nonzero thought tokens at low thinking. No thought content is exposed.

| Send | Stage/configuration | HTTP/status | Provider seconds | Input | Output | Thought | Total |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | Native medium/2,400 | 200/requires_action | 4.799 | 1,664 | 73 | 328 | 2,065 |
| 2 | Native medium/2,400 | 200/requires_action | 4.500 | 9,168 | 95 | 89 | 9,352 |
| 3 | Synthesis low/4,096 | 200/completed | 8.398 | 18,464 | 589 | 105 | 19,158 |

## Security and preservation

`.env` remains ignored, untracked and byte-identical. No key/project change, new project, billing action, credential output, deployment or later phase occurred. Source/report/bundle credential scanning passes. Production fallback remains **3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite**; this verifier alone disables fallback/retries. Operational quantities, donor policy, forecasts, warnings, snapshots, model artifacts, UI, saved federation and historical evidence remain unchanged.

The full post-success regression sequence was not triggered because the live run failed. Preflight passed 587 tests; post-stop compilation/dependencies and preservation/security are recorded in [final local receipt](evaluation/phase6-completion-final.json). There are zero further provider sends.

## Commit and working tree

HEAD remains **a62f098**. No completion commit was made: the instruction conditioned it on all live acceptance and regression gates passing. Implementation, tests and reports remain reviewable as local changes. The working tree is modified; no push or deployment occurred.

## Phase 6 verdict

Phase 6 remains pending because: the positive synthesis says “Despite executing recommended transfers,” contradicting authoritative physical_execution=false.
