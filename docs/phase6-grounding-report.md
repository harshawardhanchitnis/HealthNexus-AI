# Phase 6 numeric grounding — 29 September 2026

Continues commit `7cec2c6`. This change tightens the Copilot explanation contract. The Phase 8.5 UI, operational engines, saved forecast/federation artifacts and production model order remain unchanged. There is no deployment or model retraining.

## Historical diagnosis and its limit

The retained [Phase 8.5 matrix](evaluation/phase85-gemini-availability.json) identifies three HTTP-200, schema-valid responses rejected with `unsupported_number`:

| Model | Attempt | Exact unsupported number | Sentence / field | Cause classification |
|---|---:|---|---|---|
| gemini-3.6-flash | 1 | Not retained | Not retained | Undetermined |
| gemini-3.5-flash-lite | 1 | Not retained | Not retained | Undetermined |
| gemini-3.5-flash-lite | 2 | Not retained | Not retained | Undetermined |

Neither the matrix nor the related sanitized traces saved the rejected draft, offending token or cited field paths. The old service audit did not record these either; the verifier's service process has ended. Consequently, these particular failures cannot honestly be classified as fabricated, rounded, recomputed, percentage-derived, count-derived, unit-converted, unrelated-context or validator/path errors. A precise historical root cause is **not recoverable from retained evidence**. This is an evidence-retention limitation, not evidence that the old rejections were wrong.

The [diagnosis record](evaluation/phase6-numeric-diagnosis.json) reconstructs the two authoritative tool reads from unchanged Pune/profile/origin assets. This reconstruction is labelled explicitly; it is not a recovered provider response or exact wire capture. The source summary has three facilities, medicine availability 66.7%, bed utilisation 79.8%, staff availability 92.5%, and 26 warnings including four critical warnings. These are current baseline operational/forecast summaries, not the severe-dengue optimizer results.

Code inspection independently found contract gaps: the former validator automatically admitted rounded numeric representations and converted some risk fractions into percentages; the prompt did not universally forbid derivation; the resilience context contained irrelevant nationwide geography catalogues; and failures omitted exact claim/reference diagnostics. These findings cannot be assigned as the cause of any of the three historical failures.

## Exact changes

- **Prompt:** `healthnexus-system-v4-exact-numeric-evidence` explicitly forbids arithmetic, estimation, rounding and unit conversion. Gemini selects, explains and connects existing facts. Qualitative text with specific scalar citations is preferred; the server already resolves authoritative evidence for display. WAPE must not be converted into accuracy.
- **Schema:** only the existing `Claim.text` description changed. Fields, types, limits, response shape, citation requirements and frontend remain intact.
- **Evidence:** one shared model envelope adds at most 32 exact numeric facts per tool, each with evidence ID, path, value, exact quote, source unit where known, and available origin/model provenance. It copies values without calculating anything. Resilience summaries omit nationwide discovery catalogues; other tool intents retain their discovery data. Complete authoritative objects remain server-owned and are returned unchanged.
- **Validation:** exact decimal-value comparisons replace rounded alternatives and implicit fraction-to-percent conversion. Thousands separators, equivalent trailing zeros and scientific notation do not change values. Signed and leading-decimal values are checked. Percentage claims require an explicitly percentage-valued source. Existing precise-path bounds, solver terminology and safety guards remain. Request country/profile, geography and forecast-origin checks reject incompatible evidence.
- **Diagnostics:** failed numeric claims now retain a bounded, sanitized claim field/text, unsupported tokens and referenced source values/units/context in the private audit and diagnostic verifier. They contain no hidden reasoning, provider headers or secrets. The normal API error stays concise.
- **Server-derived facts:** none added. Existing deterministic summaries already expose the baseline percentages; the optimizer already exposes `percent_deficit_resolved`. Absent derived metrics must be explained qualitatively. Forecast, warning, scenario, OR-Tools and federation logic are unchanged.
- **Mock precision:** the shared scripted verifier copies the original WAPE value rather than formatting it with a precision-losing `:g`. This is not model-specific answer logic.

Production order remains **3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite**. The diagnostic verifier alone selects Flash-Lite. Production failover, stickiness and quality quarantine are unchanged.

## Deterministic verification before live sends

**382 backend tests pass in 62.07 seconds**, preserving all original 340 tests and adding 42 exact-grounding/verifier cases. Coverage includes fabrication, rounding, exact values, source units, absent/present derived facts, specific paths, duplicate values, percentages, precision, zero, signed/leading-decimal/scientific values, WAPE/accuracy conversion, country/profile/geography/origin isolation, diagnostic redaction and cumulative-budget/replay protection. One existing Starlette/AnyIO deprecation warning remains.

Both shared mock flows pass: **gemini-3.5-flash-lite** and **gemini-3.6-flash**. Each uses two fresh authoritative tools, one scripted provider interaction, valid schema/references and zero unsupported numeric claims. Mock success proves the shared software contract, not live model quality.

Python compilation, Windows dependency consistency, strict TypeScript and Angular production build pass. The unchanged initial frontend bundle remains 387.99 kB / estimated 104.69 kB transfer. All 321 protected files outside the five deliberately edited Copilot files match the private pre-change baseline before live verification, including `.env`, the historical ledger, existing tests, UI, operational assets and old evaluation reports.

The zero-provider [canonical verifier](evaluation/phase6-numeric-canonical.json) reproduces:

| Pune severe dengue / 14 days | Target before | Safe capacity | Transferred | Lanes | Unresolved |
|---|---:|---:|---:|---:|---:|
| Redistribution-ready | 41,763 | 17,745 | 15,679 | 10 | 26,084 |
| Constrained | 30,230 | 0 | 0 | 0 | 30,230 |

Donor violations/new risks remain zero. Critical receiver medicine warnings remain 7 → 0 while maximum stock-out risk remains 100% → 100%. Per-resource conservation, all ten country/profile model partitions and the original saved federation reload/evaluation pass. No claims of new live dengue interpretation are made.

Evidence: [regressions](evaluation/phase6-numeric-regression.json), [mock responses](evaluation/phase6-numeric-mock.json), [canonical engines](evaluation/phase6-numeric-canonical.json).

Final local review added a dotted-identifier numeric regression and two post-smoke ledger-preservation checks. The parser no longer skips numeric segments inside dotted identifiers; post-smoke mock preservation reconstructs and verifies the entire historical ledger, including other model counts. The final full suite passes **385 tests in 53.36 seconds** (45 added cases), and both mocked flows pass again. Compilation remains passing. These local checks sent **zero further live requests** and do not change or accept the rejected live draft. The original pre-live 382-test gate is retained separately from the [final regression record](evaluation/phase6-numeric-final-regression.json).

## Targeted live protocol

The exact question is “Summarize the current resource resilience status in Pune.” Context is IN / MH / MH-PUNE / redistribution-ready. Medium thinking, one independent interaction per attempt, no previous interaction ID, no SDK/same-model retry, no failover and no other live models. The second send is conditional on the first fully passing HTTP/schema/evidence/numeric validation; any failure stops the run.

The verifier preserves the **22 historical requests**, original ledger fields and per-model counts, appending at most two newly authorized Flash-Lite sends. It does not roll over or delete historical accounting. A separate ignored send journal prevents replaying this authorization. Provider latency excludes verifier pacing; outer latency includes local tools, validation and pacing. Quota remaining/reset timestamps are not inferred from this local ledger; Google AI Studio remains authoritative.

```powershell
# Cost-free diagnosis and shared contract verification:
.\.venv\Scripts\python.exe scripts\verify_numeric_grounding.py --diagnose
.\.venv\Scripts\python.exe scripts\verify_numeric_grounding.py --mock
# Single authorized invocation, gated by the regression report and retained journal:
.\.venv\Scripts\python.exe scripts\verify_numeric_grounding.py --live
```

## Actual targeted live result

**Stopped after the first request. No second request or full workflow was sent.** Flash-Lite was provider-available and produced a schema-valid draft, but exact citation validation rejected it with `evidence_invalid`.

| Measure | Actual result |
|---|---|
| Model / thinking | gemini-3.5-flash-lite / medium |
| New actual provider requests | 1; no retries or fallback |
| HTTP / structured schema | 200 / valid |
| Final grounding acceptance | Rejected: `evidence_invalid` |
| Numeric literals in claim text | None; no unsupported numeric literal observed |
| Reference audit | Nine valid paths; one invalid path |
| Provider / local tool / outer latency | 8.551 s / 1.351 s / 10.658 s |
| Input / output / thought / total tokens | 6,625 / 532 / 793 / 7,950 |
| Local tools | get_network_summary and get_warning_summary; both successful |
| Historical accounting | 22 retained + 1 new = 23; other model counts unchanged |

The situation sentence was:

> The Pune network comprises multiple facilities across the district, with a portion currently classified as at risk while others remain healthy. Bed utilisation and overall medicine availability reflect notable operational pressure across the network.

The model cited `e1` with field **`bed_utilisation`**. The source field is **`summary.bed_utilisation`**, value **79.8%**. That exact full path/value/unit had already been supplied in the numeric-fact catalogue. The model omitted the `summary.` prefix. This is a **model citation-path error**, not a missing authoritative value or a validator mapping bug. No alias, automatic path repair, rewritten response or accepted replacement answer was created.

The new response contains no numeric literals in its claim text. Full numeric validation did not finish because citation resolution failed first, so it must not be labelled a grounded/numeric-validation PASS. This new error differs from the old three `unsupported_number` failures; their missing drafts prevent a causal comparison. The original new draft and supplied evidence are retained in [live evidence](evaluation/phase6-numeric-live.json); the cost-free [reference audit](evaluation/phase6-numeric-live-diagnosis.json) records the exact failure without additional provider calls.

Another citation-contract change is needed before more live testing: model citation selection must use the exact fresh supplied paths while retaining strict resolution. The model is **not yet demonstrated suitable** for full Phase 6 acceptance. Two accepted independent smoke responses have not been achieved. No positive dengue workflow, donor follow-up, constrained interpretation or provenance/model-performance live interpretation was attempted. The deterministic results above remain valid local-engine evidence.

## Final preservation and security

[Final security checks](evaluation/phase6-numeric-security.json) pass: all **320 locked files** outside the five deliberately edited Copilot files and the authorized ledger append remain byte-identical. `.env` is ignored/untracked and unchanged; the same key/configured project is used. No key rotation, billing change, Google resource creation, frontend secret, UI modification, production fallback-order change, deployment or saved operational/federation artifact change occurred. Tracked/non-ignored files and the production frontend bundles pass the credential-pattern scan.

The original ledger date and all historical per-model counts remain, with only Flash-Lite advancing from three to four sends and total usage from 22 to 23. The second authorized send was conserved because the first failed. No additional live requests are authorized by this report. Full Phase 6 remains **unaccepted**; the existing deterministic/offline hackathon demo remains available.
