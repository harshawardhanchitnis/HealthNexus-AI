# Final Gemini model availability matrix

## Baseline

Feature-frozen commit `3c144e7ac5681ea7b17ee308ab3b8f367022859b`. Live diagnostic started **2026-09-30 09:14:16 UTC / 14:44:16 Asia/Calcutta**. Status: **COMPLETED**. Machine-readable receipt: [final-gemini-model-availability.json](evaluation/final-gemini-model-availability.json).

## Purpose

Test all five configured models independently through the real HealthNexus read-only Copilot path, using exactly:

> Summarize the current resource resilience status in Pune.

Context: `IN / MH / MH-PUNE / redistribution-ready`. The user's later instruction authorized **one attempt per model and one additional attempt after failure**, superseding the earlier one-attempt-only ceiling. Maximum ten actual provider sends across the entire run. Successful models were not retried. No production failover, sticky conversation, previous interaction continuation or hidden SDK retry was used. Each attempt began a fresh application conversation and provider interaction.

The diagnostic used the frozen summary contract rather than changing the product to meet an inaccurate architectural assumption. This exact question routes to `resilience-summary`, which uses **FactDraftAnswer, provider-authored prose, request-local fact IDs and server-side evidence/numeric/qualitative validation**. It does not use named semantic slots or deterministic prose rendering: `semantic_frame_version` is null. The existing semantic-frame architecture for planning and its other supported intents remains unchanged. A passing row below means acceptance by this actual frozen summary contract; it does not claim a semantic-slot or native planning workflow was tested.

## Local preflight

- All `backend/tests/test_ai*.py`: **429 passed**, 96.69 seconds; one upstream Starlette/AnyIO deprecation warning. Covers Copilot integration, semantic frames/slots, fact IDs, grounding, action state and SDK mock faults. Zero live calls.
- New diagnostic tests: **11 passed**, 101.82 seconds. Actual SDK HTTP mock coverage includes independent successful attempts, 503 retries, schema/unknown-ID rejection, authentication/configuration failures, quota stops, global send ceiling, ledger preservation, pacing and single-use authorization.
- Python compilation of AI application/scripts and the diagnostic verifier/tests: **PASS**.
- `pip check`: **PASS**, no broken requirements.
- Pre-live Phase 9 preservation guard: **PASS**, 346 protected identities, environment unchanged, historical ledger still 42.
- Exact-question mock: real local network/warning tools, 100 current facts, zero unknown fact IDs, current semantic/numeric fact validation PASS, unchanged operational snapshot.

These are relevant AI and diagnostic checks, not a rerun of the full Phase 9 backend/frontend/Docker release gates. No product changes required new UI/build checks.

## Provider quota confirmation

Before the live run, the user explicitly confirmed: **"Quota is available for this run"**. No remaining-quota quantity or reset timestamp was inferred. The local ledger records historical verifier sends; it is not Google's provider quota dashboard.

## Matrix

Provider latency is measured around the SDK call, excluding local tool preparation and inter-attempt waits. A dash means unavailable/not reached, not zero.

| Model | Attempt | HTTP / provider status | HealthNexus | Classification | Provider seconds | Total tokens | Error |
|---|---:|---|---|---|---:|---:|---|
| gemini-3.8-flash | 1 | 503 / no interaction result | NOT REACHED | 503_HIGH_DEMAND | 16.277 | — | provider_unavailable |
| gemini-3.8-flash | 2 | 503 / no interaction result | NOT REACHED | 503_HIGH_DEMAND | 1.544 | — | provider_unavailable |
| gemini-3.7-flash | 1 | 503 / no interaction result | NOT REACHED | 503_HIGH_DEMAND | 33.039 | — | provider_unavailable |
| gemini-3.7-flash | 2 | 503 / no interaction result | NOT REACHED | 503_HIGH_DEMAND | 9.754 | — | provider_unavailable |
| gemini-3.6-flash | 1 | 200 / completed | PASS | AVAILABLE_ACCEPTED | 7.088 | 8,329 | — |
| gemini-3.5-flash | 1 | no HTTP response | NOT REACHED | OTHER_PROVIDER_ERROR | 60.114 | — | provider_timeout |
| gemini-3.5-flash | 2 | no HTTP response | NOT REACHED | OTHER_PROVIDER_ERROR | 60.093 | — | provider_timeout |
| gemini-3.5-flash-lite | 1 | 200 / completed | PASS | AVAILABLE_ACCEPTED | 5.929 | 8,201 | — |

## Provider availability

- Provider availability observed: **2 of 5**, `gemini-3.6-flash` and `gemini-3.5-flash-lite`.
- HTTP 503 HIGH DEMAND on both attempts: `gemini-3.8-flash`, `gemini-3.7-flash`.
- No HTTP response before the existing 60-second timeout on both attempts: `gemini-3.5-flash`. A timeout does **not** establish a HIGH DEMAND response.
- Rate limited: none observed.
- Authentication/configuration failures: none observed.
- Provider available but application rejected: none observed.

This is a point-in-time diagnostic, not a guarantee of future model availability.

## HealthNexus acceptance

**2 of 5 models completed the existing frozen read-only summary contract.** Both successes used actual local `get_network_summary` and `get_warning_summary` evidence. No emergency scenario, redistribution optimization, federation training or native planning was executed.

| Accepted model | Schema | Fact IDs | Numeric / qualitative grounding | Action-state validation | Unknown IDs | Unsupported numbers | Resolved references |
|---|---|---|---|---|---:|---:|---:|
| gemini-3.6-flash | PASS | PASS | PASS | PASS | 0 | 0 | 12 |
| gemini-3.5-flash-lite | PASS | PASS | PASS | PASS | 0 | 0 | 16 |

Both responses used a 100-fact catalogue. Current context/geography/profile and evidence compatibility checks passed. Unsupported execution claims were zero. The operational snapshot remained unchanged and the optimizer created no results.

For the six failed attempts, schema, fact IDs and grounding were **NOT REACHED**; unknown-ID and unsupported-number counts are unavailable. They are not recorded as fabricated zero counts. Named semantic-slot validation is **not applicable** to this frozen summary intent for any model.

## Errors

Both 3.8 attempts returned the provider message:

> gemini-3.8-flash is currently experiencing high demand, spikes in demand are usually temporary. Please try again later.

Both 3.7 attempts returned the equivalent model-specific message. Each 503 supplied `Retry-After: 30`; it was honored before the next request. Their application error code was `provider_unavailable`.

Both 3.5 attempts ended with `provider_timeout`, without an HTTP status or usage object. No additional attempts were made. No schema, grounding, authorization or quota defect was hidden by fallback.

## Token / latency measurements

All attempts retained the existing synthesis configuration: **low thinking**, **4,096 maximum output tokens**, **60-second provider timeout**. No per-model configuration adjustment was introduced.

| Accepted model | Input tokens | Output tokens | Reported thought tokens | Total tokens | Provider seconds | Local tool seconds | Application seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.6-flash | 7,795 | 534 | 0 | 8,329 | 7.088 | 0.0268 | 8.016 |
| gemini-3.5-flash-lite | 7,595 | 606 | 0 | 8,201 | 5.929 | 0.0326 | 6.731 |

Usage is provider-reported. Failed attempts supplied no usage; their token counts are unknown. Provider/model-specific input totals are retained as reported, not normalized to an invented identical number. No hidden thought content, credentials, raw headers or raw provider error bodies were retained.

## Request accounting

- Historical ledger before: **42**.
- Actual new SDK HTTP sends: **8** (one per attempt).
- Ledger after: **50**.
- Per-model new sends: **3.8 = 2; 3.7 = 2; 3.6 = 1; 3.5 = 2; 3.5 Flash-Lite = 1**.
- Global authorized maximum: **10**, at most two per model. The two unused sends were not consumed.
- All previous counts and the ledger's historical `day: 2026-09-28` were preserved. Eight timestamped entries were appended; no reset, rollover, deletion or invented accounting day.
- Conservative minimum 20-second spacing and supplied Retry-After delays were enforced. No simultaneous requests or cross-model failover inside an attempt.
- Single-use local journal is terminal; rerunning the live verifier under this authorization is prohibited. **All Gemini calls stopped after the matrix.**

The eight attempts each used local read-only tool preparation. Local tool execution is separate from provider-send accounting.

## Security / preservation

Post-live byte-identity guard: **PASS**, **678 frozen tracked/ignored file identities**, excluding the explicitly authorized ledger updates. `.env`, production models, operational data, planning/federation artifacts and Phase 6/9 evidence remained unchanged. The existing API key/project were used; no cloud account, project, key or billing administration was performed. No secrets were printed or stored in this report. Publication secret scan: **PASS**.

Production fallback is unchanged:

`gemini-3.8-flash → gemini-3.7-flash → gemini-3.6-flash → gemini-3.5-flash → gemini-3.5-flash-lite`.

No product, UI, prompt, contract, runtime setting, optimizer or federation changes. No deployment. Changes are limited to a diagnostic verifier, its tests and sanitized diagnostic evidence.

## Conclusion

**Gemini 3.8 Flash still returned HIGH DEMAND on both authorized attempts.** Gemini 3.7 Flash did likewise. Gemini 3.5 Flash timed out twice. **Gemini 3.6 Flash and 3.5 Flash-Lite each completed the real HealthNexus read-only summary and passed its grounding contract on the first attempt.** Production behavior remains frozen; this evidence does not reorder fallback or claim a fresh full planning workflow acceptance.
