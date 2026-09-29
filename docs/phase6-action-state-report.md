# Phase 6 — advisory action-state grounding — 29 September 2026

Continues `9a16cc5`. Optimization tool outputs now carry an explicit, typed advisory action state. Exact fact-ID/numeric/context validation, operational calculations, OR-Tools, forecasts, warnings, federation, production fallback order and UI remain unchanged.

**Positive live workflow remains pending because: the remaining-gap claim describes advisory transfers as executed and mentions optimal without citing solver status.** Native orchestration is **PASS** from preserved live evidence. Final synthesis and positive workflow acceptance are **FAIL**. Exactly one new Lite synthesis request was sent; no retry, fallback, native provider call or later live case followed.

## Authoritative contract

Both `optimize_redistribution` and `get_optimization_result` use the same thin server adapter to attach:

| Canonical server-owned path | Value |
|---|---|
| `action_state.plan_mode` | `advisory` |
| `action_state.physical_execution` | `false` |
| `action_state.externally_authorized` | `false` |
| `action_state.hospital_contacted` | `false` |
| `action_state.real_world_transfer_status` | `not_executed` |

The immutable Pydantic model (`advisory-action-state-v1`) reflects the actual prototype: no dispatch, external approval or hospital-contact adapter exists. User permission to calculate a plan is distinct from authorizing its physical transfers. Solver success cannot change these fields. Engine result schemas, stored scenario/optimization objects, inventory ledgers and artifact identities are not changed.

These fields, and their concise aggregate, receive current request-local fact IDs. The provider sees labels/values/IDs; canonical paths remain server-owned. Essential action-state, solver status, capacity and before/after/transfer metrics are prioritized within the existing **64-fact** bound. The complete numeric panels remain server-owned. No new alias, field-path repair or model-generated quantity is introduced.

The added synthesis instruction says optimization outputs are advisory simulation recommendations unless current authoritative action evidence confirms otherwise, requires action-state citations, forbids execution/approval wording without evidence, and defines OPTIMAL as mathematical optimization status only. Native planning stays **medium / 2,400**; final synthesis stays **low / 4,096**. Prompt version is `healthnexus-system-v7-action-state`; fact contract stays `healthnexus-facts-v1`.

## Deterministic semantic guard

The production evidence builder now checks operational entities and action predicates, rather than relying on the previous four execution keywords. Its bounded normalization handles case, Unicode compatibility/zero-width formatting, Markdown, hyphens and negative contractions. Inflected execution/movement/delivery/authorization/implementation predicates, nominal action phrases and contrast clauses are checked against server action state. Clause-local negation prevents “no donor violations” from disguising a subsequent execution assertion.

`transfer` remains a valid noun. Recommended/proposed transfers, transfer lanes, exact planned accounting quantities and mathematical optimizer completion are allowed. Explicit action denials need the relevant state facet: physical execution cannot substitute for external authorization, contact, or advisory mode. Unsupported real-world action claims fail closed; unsupported complete-shortage-resolution wording is rejected when target deficit remains positive. Existing scalar OPTIMAL citation and clinical checks remain intact.

The old literal execution check was replaced by this stronger action-aware guard, so the user-required **“have not been physically executed”** can pass with its authoritative false fact. Numeric extraction, exact comparisons, units, source/context validation and fact membership/resolution code remain identical, verified separately by source hashes. Transfer-topic relevance recognizes the new action facts; bed/staff and other unrelated-topic checks remain intact. Deterministic offline summaries and common mock outputs cite the same authoritative state rather than bypassing the guard.

This is a conservative, tested logistics-domain guard, not exhaustive natural-language understanding. Manual factual review remains necessary. The contract deliberately cannot turn a mathematical plan into an external action; future dispatch integration would require a separately defined action contract.

## Exact previous failure

The retained previous response's two complete claims containing **“executing safe transfers”** and **“Despite executing authorized transfers”** are rejected deterministically against the current false action state. This reads the preserved text without a provider call. Equivalent execution, completion, movement, approval, implementation and redistribution forms also fail. Valid advisory wording, scoped negatives, solver wording, exact numeric citations, stale/unknown IDs and facet-specific references are tested. [Preflight evidence and exact reproduction](evaluation/phase6-action-preflight.json).

## Local regression and canonical preservation

Before the live send, **555 backend tests passed in 103.13 seconds**, retaining all 484 previous cases and adding 71 action-state cases. Shared Flash-Lite/3.6 official SDK HTTP mocks pass schema, current fact IDs, unchanged numerical grounding, context, solver and action-state validation. Python compilation and Windows `pip check` pass. [Shared mocks](evaluation/phase6-action-mock.json).

The local canonical verifier checks all ten country/profile partitions and saved five-country federation. The positive plan remains **41,763 target / 17,745 safe capacity / 15,679 planned accounting items / 10 lanes / 26,084 unresolved**, with **zero donor violations and zero new donor risks**. The constrained plan remains **30,230 unresolved, zero safe capacity, transfers and lanes**. No live constrained interpretation was attempted. [Canonical verification](evaluation/phase6-action-canonical.json).

After the stopped request, one further deterministic test independently rejects its exact execution phrase, without changing the guard or weakening solver/numeric checks. Final regression passes **556 tests in 114.61 seconds** (484 retained + 72 new). Compilation/dependencies and security/preservation pass; measurements are recorded in [final local evidence](evaluation/phase6-action-final.json). Frontend sources and the previous successful strict TypeScript/Angular production build are preserved; no new frontend build is claimed. One existing Starlette/AnyIO deprecation warning remains.

## One live request — rejected

The request used **deterministic reconstructed authoritative evidence (path B)**, with the exact previously validated native inputs and actual unchanged engines. It did not rerun Gemini native planning or use a stored narrative. New process-local IDs were `cf793526-7c3a-49bf-99a2-2ce960577600` and `6e13ed9b-9081-4b00-965c-33002491d55e`; these are explicitly distinguished from the previous live objects. Canonical impacts, transfer rows, reserves, risks, source fingerprints, profile/origin and model identity are revalidated before sending.

| Live measurement | Result |
|---|---|
| Model | gemini-3.5-flash-lite |
| HTTP / provider status | 200 / completed |
| Configuration | low / 4,096 generation tokens |
| Input / output / thought tokens | 10,156 / 516 / 0 |
| Total tokens | 10,672 |
| Provider latency | 12.832 seconds |
| JSON / claims / output length | Complete / 4 / 1,346 characters |
| Schema | PASS |
| Primary runtime rejection | `solver_terminology` |
| New provider sends | 1 |
| Retained ledger | 29 + 1 = 30; Lite 10 → 11 |
| Native provider calls / retries / fallback | 0 / 0 / 0 |

The exact remaining-gap claim is:

> Even with optimal advisory transfers executed, a substantial target deficit and expected unmet demand persist across the district facilities.

It cites after expected unmet demand, after target deficit and planned transferred units, **not** the scalar `solver.status=OPTIMAL`. The unchanged solver check rejects that same-claim citation defect first. Independently, its unqualified **“advisory transfers executed”** contradicts `physical_execution=false` and `real_world_transfer_status=not_executed`. Calling transfers advisory does not make execution true.

The exact sanitized draft, actual server payloads and original fact catalogues are preserved in the [live trace](evaluation/phase6-action-live.json). No answer, fact ID or source value was rewritten. Offline review reconstructs that **exact saved catalogue**, asserts equality, resolves all original IDs against the original saved payloads, and checks each original claim separately. The first three claims pass the existing production checks; the remaining-gap claim fails solver terminology and, independently, action-state validation. These offline checks are distinct from the failed original live pipeline; they are not a second live acceptance.

| Exact saved-output review | Result |
|---|---|
| Schema / fact membership | PASS / PASS |
| Unknown fact IDs | 0 |
| Exact-number review | PASS; no numeric literals in any claim |
| Unsupported numbers | 0 |
| Source context/origin | PASS |
| Action-state / qualitative grounding | FAIL |
| Unsupported execution claims | 1 |
| Solver terminology | FAIL |

[Independent review with exact resolved facts and failure diagnostics](evaluation/phase6-action-review.json). The original live citation diagnostic identifies the first audit row generically when solver validation raises; the separate per-claim replay locates the actual error in `remaining_gaps.0.text`. The original trace remains unchanged.

## Security, accounting and stop condition

The original 29-request ledger, its original day and every historical field/per-model count were preserved. The official SDK wire hook appends only the real Lite attempt; a separate exclusive one-send journal prevents replay even if an old ledger is restored. SDK/same-model retries and cross-model fallback are disabled for this verifier. Earlier journals and accepted evidence remain unchanged. Quota headroom is not inferred from local accounting.

`.env` remains unchanged, ignored and untracked. The same key/project and billing state were retained. Production fallback remains 3.8 → 3.7 → 3.6 → 3.5 → 3.5 Flash-Lite. Protected operational/forecasting/OR-Tools/federation files, generated artifacts, UI and historical reports retain their identities. No deployment, later phase or later live case was started.

Cost-free checks are reproducible with `python -m pytest backend -q`, `python scripts/verify_advisory_final.py --mock`, compilation and `pip check`. The one live authorization has been consumed. Do not delete journals, reset accounting or rerun live mode. Same-conversation donor follow-up, constrained interpretation and provenance/reliability require further authorization; positive synthesis acceptance is still pending.

Native orchestration: **PASS**. Final synthesis: **FAIL**. Positive workflow acceptance: **FAIL**. Full Phase 6: **not accepted**.

**Positive live workflow remains pending because: the remaining-gap claim describes advisory transfers as executed and mentions optimal without citing solver status.**
