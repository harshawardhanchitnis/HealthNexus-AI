# Phase 6 — bounded full live workflow attempt — 29 September 2026

This checkpoint continues `3f5a7b9`. The accepted request-local fact-ID contract and previous **2/2 grounded Flash-Lite smokes** remain unchanged. This task attempted full workflow acceptance with verifier-selected **gemini-3.5-flash-lite**, medium thinking, the existing 2,400 output-token limit, no retry and no cross-model failover. Production order stays 3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite.

**Phase 6 remains pending because: the positive workflow's final structured synthesis returned `incomplete` with truncated JSON (`response_incomplete`).** No final positive answer was accepted, and the run stopped before any later live case.

## Preflight and provider accounting

Before any live call, **458 backend tests passed in 70.04 s**, retaining all 436 previous cases and adding 22 verifier-only cases. Existing Lite/3.6 fact-ID mocks and all four full-workflow mocks passed. The latter used seven scripted requests, actual local engines and common model-independent mock behavior. Tests cover the eight-send global ceiling, original-ledger preservation, no other model, native declarations/arguments/geography/permissions/identity, fabricated quantities, qualitative acceptance expectations and an explicit local factual-review gate before further live cases.

Python compilation, Windows `pip check`, strict TypeScript and Angular production build passed. The unchanged initial bundle is 387.99 kB / estimated 104.69 kB transfer. Canonical plans, all ten country/profile partitions and original saved federation passed. `.env` was ignored/untracked, and credential-pattern scans passed for tracked/non-ignored source and frontend bundles. [Preflight evidence](evaluation/phase6-workflow-preflight.json), [existing fact mocks](evaluation/phase6-workflow-fact-mock.json), [full workflow mocks](evaluation/phase6-workflow-mock.json), [canonical engines](evaluation/phase6-workflow-canonical.json).

The user independently reported current Google AI Studio Flash-Lite usage **3/15 RPM, 8.5K/250K TPM, 0/500 RPD**, Free tier. This provider-side report established headroom; local accounting was not used to infer quota. No exact reset time was supplied.

The live authorization allowed at most **eight new actual provider sends globally**. Exactly **three** were sent, all to Flash-Lite. All three received HTTP 200: two `requires_action` interactions and one `incomplete` interaction. The official SDK HTTP send hook recorded each actual attempt once; SDK retries, same-model retries and failover were disabled. Fifteen-second start pacing conserves RPM. The retained original ledger and day were preserved: **25 historical + 3 new = 28**; Lite **6 historical + 3 = 9**. Other models received zero new calls. Five unused sends were conserved; the failed authorization cannot be replayed by resetting a journal or changing the day.

## Actual native orchestration

Gemini independently selected:

1. `run_emergency_scenario` — IN / redistribution-ready / MH / MH-PUNE, severe `DENGUE_SURGE`, 14 days. The registered schema supplied its normal seed default, 42.
2. `optimize_redistribution` — the actual returned scenario ID, district donor scope, registered PCM/IVF/ORS/AMX/IFA resources. Omitted state was inherited from the validated context by the unchanged existing tool validator.

Both calls were declared, Pydantic-valid, permission-valid and context/identity-valid. Both local tools succeeded. No tool order, donor edge, quantity or operational result was injected into the prompt. The scenario tool itself supplies resource impacts/warnings, and optimization supplies actual plan impacts. Separate comparison/warnings/preview calls were not selected; the instructions permitted a different valid sequence.

Scenario ID: **`e0aca1d9-9770-47de-a11c-8f97f17ff6f8`**. Optimization ID: **`6551b897-f19d-4eaf-b308-e3c3f4b4fb47`**. The authoritative local solver returned **`OPTIMAL`**:

| Engine measurement | Actual native result |
|---|---:|
| Target before | 41,763 |
| Safe donor capacity | 17,745 |
| Transferred accounting items | 15,679 |
| Transfer lanes | 10 |
| Unresolved target | 26,084 |
| Donor violations / new donor risks | 0 / 0 |

Per-resource conservation holds. These values were read from the actual optimizer tool envelope, not Gemini's narrative or a stored answer. Native execution passed these checks; the complete positive case still **failed** because no valid final answer followed.

## Final synthesis failure and performance

The third request continued on the same model with the correct previous interaction and native optimization result. It returned status **`incomplete`** and only a partial JSON prefix. The server correctly raised `response_incomplete` before schema/ID/numeric/qualitative validation could complete. There is no accepted final answer, no grounded-value claim result, and no measured zero count for unknown IDs or unsupported numbers. Those validation/count fields are **not reached**, rather than reported as PASS or zero.

| Provider attempt | Stage / status | HTTP | Provider seconds excluding pacing | Input / output / thought tokens | Total tokens |
|---|---|---:|---:|---|---:|
| 1 | Select scenario / requires_action | 200 | 5.453 | 3,332 / 73 / 273 | 3,678 |
| 2 | Select optimizer / requires_action | 200 | 5.857 | 10,778 / 111 / 269 | 11,158 |
| 3 | Final synthesis / incomplete | 200 | 11.284 | 1,268 / 80 / 2,303 | 3,651 |

Provider time excluding pacing totals **22.594 s**. Application provider time including pacing is **37.983 s**. Actual local tools total **4.177 s** (scenario 3.332 s; optimizer 0.845 s). Overall case time is **42.816 s**. Total provider-reported usage is **18,487 tokens**; thought counts are retained, never thought content.

The incomplete status, truncated final output and 2,303 reported thought tokens with only 80 output tokens are consistent with exhausting the configured response budget. This is an inference; no separate provider stop reason was supplied. No thinking/output settings were changed to retry the case. [Sanitized live trace](evaluation/phase6-workflow-live.json), [precise diagnosis and measured native plan](evaluation/phase6-workflow-diagnosis.json).

## Later cases and acceptance scope

| Required case | Live result |
|---|---|
| Positive native planning | Tools succeeded; whole case FAIL at final synthesis |
| Grounded positive final answer | NOT ACCEPTED |
| Same-conversation donor follow-up | NOT RUN — stop condition |
| Constrained zero-donor interpretation | NOT RUN — stop condition |
| Provenance / forecast reliability | NOT RUN — stop condition |

The prior 2/2 smoke evidence remains accepted and byte-identical. It does not complete this larger acceptance. All four cases pass local mocks, but mocks are not live acceptance. The constrained **local** case still measures 30,230 unresolved, zero safe capacity/transfers/lanes, and zero donor violations/new risks. Original federation evidence remains unchanged: run `fdbaaedb-773d-4b67-be50-ad406b130950`, five rounds, zero raw records shared, 4.8010934 seconds and 614,235 exchanged bytes. No new live constrained/provenance interpretation is claimed.

## Security and final local verification

All original fact-ID, numeric validation, operational/forecasting/warning/scenario/OR-Tools/federation and UI files retain their original identities. Accepted generated data, models, weights and historical evaluation reports are unchanged. The only original-file exceptions are current documentation and the validated ledger append. The existing key/project/billing and production fallback order are unchanged. No deployment, canonical data regeneration or accepted-model retraining occurred; existing regression fixtures use temporary test artifacts only.

After the stopped attempt, verifier logging was tightened to omit opaque provider signatures and internal metadata from acceptance evidence. This affects only logging, not transport content, model behavior or grounding. The original provider statuses, usage, calls, values and truncation remain recorded; one deterministic sanitation test was added. No additional live call was made. Final local verification is recorded separately in [final regression/security evidence](evaluation/phase6-workflow-final.json).

**Final backend regression: 459 tests pass in 111.96 s**, retaining the original 436 and adding 23 verifier-only cases. Compilation and dependency checks pass; the unchanged frontend's strict TypeScript and production build pass. One existing Starlette/AnyIO warning remains. All 481 protected original identities outside the four updated documentation files and validated ledger append remain unchanged; final credential-pattern scanning passes. `.env`, API key, project and billing remain unchanged. No full live case is marked PASS.

**Phase 6 remains pending because: the positive workflow's final structured synthesis returned `incomplete` with truncated JSON (`response_incomplete`).**
