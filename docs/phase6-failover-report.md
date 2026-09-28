# Phase 6 Gemini availability failover

28 September 2026. Implementation and deterministic verification pass. **Successful live fallback interpretation and full Phase 6 acceptance remain unverified.** No billing, project, key, operational engine, inventory profile, donor protection or OR-Tools changes. Phase 7 has not started.

## Exact configured order

1. `gemini-3.8-flash`
2. `gemini-3.7-flash`
3. `gemini-3.6-flash`
4. `gemini-3.5-flash`
5. `gemini-3.5-flash-lite`

SDK: official `google-genai==2.25.0`, Interactions API. All candidates use **medium** thinking, supported by [Google's thinking documentation](https://ai.google.dev/gemini-api/docs/thinking). No 3.1/2.5/preview/Pro/non-Google fallback is selected. `.env.example` adds primary/fallback/enable settings; the actual ignored `.env` stays untouched. `GEMINI_MODEL_PRIMARY` overrides legacy `GEMINI_MODEL`; default fallbacks follow the exact list above. All models share the 13 existing tools, validation, evidence and deterministic engines.

## Policy, handoff and audit

- One bounded request attempt per model when failover is enabled; hidden SDK retries remain disabled. Switch after 503/high demand, bounded provider timeout, explicit model-endpoint 404, or RPM/TPM/RPD 429 whose violations all explicitly identify the current model. Ambiguous/project-wide quota errors remain failures.
- Authentication/permission (401/403), invalid configuration (400), malformed calls, schema/evidence/grounding failures, context mismatch, local tool failure and clinical refusal do not trigger model switching. All eligible models unavailable returns `provider_unavailable_all_models`; local budget denial keeps its distinct code. Offline selection is explicit.
- New model interactions omit foreign previous IDs and native function-result IDs. The validated handoff includes original question/context, current scenario/optimization IDs and compact request-local tool evidence, bounded to 120 kB UTF-8. No hidden reasoning is transferred. Completed local engines/results remain available; no stored model answer is substituted.
- Successful model is sticky for the conversation; a new conversation normally tries primary. Known model quota exhaustion is skipped through a process-local circuit: daily exhaustion until next Pacific midnight, minute exhaustion for at least 60 seconds or provider delay. This is not an estimate of remaining quota. [AI Studio remains authoritative](https://ai.google.dev/gemini-api/docs/rate-limits).
- Repeated output/schema/evidence safety failures (two) mark a candidate `UNSUITABLE_FOR_HEALTHNEXUS` in that process and exclude it from automatic selection. The failing request stays failed. Health and conversation state are process-local, not durable production infrastructure.
- Metadata distinguishes requested, selected and successful effective model; records chain attempts, handoff reasons, requests, successful interactions, failures and stage timings per model. UI shows the actual answering model, fallback indicator and provider availability trace, including failures. No provider headers, key or hidden reasoning are shown.

## Live smoke: automatic chain, no successful answer

Question: “Summarize the current resource resilience status in Pune.” Context: IN → MH → MH-PUNE, redistribution-ready. Two **fresh server-prefetch** reads (`get_network_summary`, `get_warning_summary`) succeeded before the schema-only interpretation attempt. They are not model-selected native calls.

| Model | Actual sends | Successful interactions | Result | Provider stage seconds |
|---|---:|---:|---|---:|
| 3.8 Flash | 1 | 0 | 503 HIGH DEMAND | 9.0084 |
| 3.7 Flash | 1 | 0 | 503 HIGH DEMAND | 6.0152 |
| 3.6 Flash | 1 | 0 | 503 HIGH DEMAND | 19.8510 |
| 3.5 Flash | 0 | 0 | Blocked locally before sending | — |
| 3.5 Flash-Lite | 0 | 0 | Not reached | — |

Three actual requests across all models; seven prior requests retained, daily ledger **10/10**. No reset or additional live browser call. Automatic transitions 3.8 → 3.7 → 3.6 are observed. Advancing to 3.5 was blocked by `quota_budget_exhausted_locally`, not by a Google response. The final two models' live behavior remains unknown.

Provider stage: **35.7325 s**, local tools **1.2895 s**, case total **37.3162 s**. Provider stages include conservative verifier pacing and transport overhead; these are not isolated HTTP timings. All returned `Retry-After: 30`. Token usage was **not reported**. No scenario/optimization was created by this smoke; no model served an answer. Live schema and grounding were not exercised. No positive/constrained live interpretation followed the failed smoke.

[Raw live evidence](evaluation/phase6-failover-live-smoke.json) preserves its original implementation identity. Its historical `effective_model` denoted the selected candidate (3.5) before any success; that field is **not evidence that 3.5 answered**. Current metadata separates selected candidate from successful model. [Consolidated measured evidence](evaluation/phase6-failover-verification.json) explicitly records no answering model.

## Deterministic compatibility and unchanged local plans

All five candidates pass SDK HTTP-mock encoding checks for native declarations/results, same-model continuation, medium thinking and structured response format. Shared real-engine positive tests, handoff at final synthesis, fresh same-conversation donor follow-up, primary retry on new conversation, global budget and failure exclusions pass. These checks validate application protocol behavior; they do **not** prove live endpoint compatibility or model reasoning quality.

[Five-model scripted smoke metrics](evaluation/phase6-failover-candidates-mock.json) record one simulated provider interaction and two fresh local reads per candidate; structured/evidence validation passes, with zero invalid tool calls and unsupported numeric claims. Scripted latency is not live inference latency. [Full mock acceptance](evaluation/phase6-failover-mock.json) uses eight simulated provider requests; [offline acceptance](evaluation/phase6-failover-offline.json) uses zero actual provider requests. Complete engine objects and IDs are in those files.

| Pune severe dengue, 14 days | Target before | Safe capacity | Transferred tally | Lanes | Target after | Donor risks / reserve violations |
|---|---:|---:|---:|---:|---:|---|
| Redistribution-ready | 41,763 | 17,745 | 15,679 | 10 | 26,084 | 0 / 0 |
| Constrained | 30,230 | 0 | 0 | 0 | 30,230 | 0 / 0 |

Actual local OR-Tools status is OPTIMAL, with the preserved greedy tie. Ready expected unmet demand is 27,655.2181 → 17,378.1980; critical resource warnings 7 → 0. Remaining PCM 22,947 tablets, IVF 2,173 bags, ORS 964 sachets; AMX/IFA zero. Maximum and IVF/PCM conditional 14-day stock-out risk remain 100%. All donors retain required reserves; medicine conservation holds independently. The constrained case cannot manufacture safe donors. These are simulated operations and advisory plans, never live government stock or executed transfers. Snapshot and model hashes match the pre-failover evidence exactly; models were not retrained.

## Verification and readiness

- **281 full backend tests pass**, including all previous 237 and 44 new failover tests; final full run 83.56 s. One upstream Starlette/AnyIO deprecation warning remains.
- Python compilation, `pip check`, strict TypeScript and Angular production build pass. Initial bundle 366.12 kB / estimated 100.26 kB transfer; Copilot lazy chunk 22.89 kB / 6.35 kB.
- Desktop and 390×844 mobile UI verified using explicit offline mode. Mobile document width 375 within viewport 390; no console errors/warnings. [Desktop screenshot](screenshots/phase6-failover-desktop-offline.png), [mobile screenshot](screenshots/phase6-failover-mobile-offline.png). Successful live fallback UI rendering has not been observed.
- Key is ignored/untracked, matches loaded configuration, and absent from scanned tracked source, reports, frontend bundles and diff. Same key/project; no billing change or quota-ledger reset.

Successful fallback native orchestration, grounded final answers, full positive/constrained acceptance and hackathon live readiness are still pending. Explicit deterministic demos remain available. **Phase 6 is not fully accepted; Phase 7 remains deferred.**

## Targeted remaining-model acceptance — 28 September 2026

The user explicitly authorized a verifier-only cumulative ceiling of 14 and targeted testing of the previously unsent models. The existing ten sends were retained. Production configuration and its five-model order were unchanged; no 3.8/3.7/3.6 request was repeated. Command:

```powershell
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case model-smoke --model gemini-3.5-flash --budget 14 --resume --output docs/evaluation/phase6-targeted-live-smoke.json
```

The same Pune redistribution-ready resilience question executed two fresh authoritative read-only tools, `get_network_summary` and `get_warning_summary`. Schema-only interpretation first attempted 3.5 Flash; its eligible 503 automatically advanced to Flash-Lite, starting a fresh interaction without any foreign provider ID.

| Model | Actual new sends | Successful interactions | Google result | Provider stage seconds |
|---|---:|---:|---|---:|
| 3.5 Flash | 1 | 0 | HTTP 503 HIGH DEMAND | 5.1946 |
| 3.5 Flash-Lite | 1 | 0 | HTTP 503 HIGH DEMAND | 12.9826 |

Both responses supplied `Retry-After: 30`. Neither returned an interaction or token usage. Aggregate provider stage was 18.4401 s, local tools 1.3407 s and failed workflow latency 20.0682 s. Provider stages include verifier pacing/transport overhead. [Exact new trace](evaluation/phase6-targeted-live-smoke.json) preserves the responses, handoff, timings and original implementation identity; `effective_model` is null, with no answering model. The clean error is `provider_unavailable_all_models` for the selected remaining chain.

Budget: **10 historical sends + 2 new sends = 12 cumulative sends against the explicitly authorized ceiling of 14**. Per-model history is seven legacy-unattributed sends plus one each for all five configured models. Two authorized sends remain unused. The ledger was not reset, and no repeated live attempt, browser request or model-list request followed this outage. This was a provider failure, not local budget rejection; no quota exhaustion or remaining Google quota is inferred.

Live structured schema, evidence and numeric grounding are **unverified**, because no provider answer arrived. The positive, constrained and provenance live interpretations were not attempted: smoke PASS is their prerequisite. Live UI verification was also deferred as instructed. No candidate is marked unsuitable for a quality failure: an availability error supplies no quality evidence.

The normal verifier cap remains 1–10. Only an explicit CLI `--budget` may authorize an extension up to 14; environment settings cannot silently extend the cap. `--model` must be an already configured candidate and seeds verifier-local sticky state without changing production configuration. A compatible successful `model-smoke` PASS can restore its actual effective model for subsequent `--model gemini-3.5-flash --resume` positive acceptance, even when Flash-Lite answered. Saved evidence binds the verifier selection, configuration, implementation, artifacts and credentials privately. Failed results never become resumable PASS evidence.

New deterministic checks cover preserved cumulative history, bounded overrides, allowed CLI models, targeted stickiness, availability-only transition to Lite and schema failure exclusion. Targeted [mock smoke](evaluation/phase6-targeted-mock-smoke.json) and [mock positive](evaluation/phase6-targeted-mock-positive.json) pass; these are scripted provider responses, not live reasoning. [Fresh offline acceptance](evaluation/phase6-targeted-offline.json) reproduces both real local plans, donor protection and immutable snapshots with zero provider requests. The ready result remains **41,763 / 17,745 / 15,679 / 10 / 26,084**, zero new donor risks/violations; constrained remains **30,230 unresolved / zero capacity / zero transfers**. OR-Tools remains OPTIMAL and ties greedy. These engine results do not count as Gemini live acceptance.

The automatic failover path has now been observed across all five candidates in two retained live sessions. All five returned 503. **Phase 6 remains blocked on provider availability and cannot be declared live-accepted or ready as a reliable live Gemini demo.** Explicit deterministic operational demos remain available; Phase 7 has not started.

Current regression: **289 backend tests passed in 45.88 s**, including all previous 281 plus eight targeted-verifier cases. Python compilation, `pip check`, strict TypeScript and Angular production build pass (366.12 kB initial / 100.26 kB estimated transfer). One upstream Starlette/AnyIO deprecation warning remains. No browser test was run during targeted acceptance because the required live smoke did not pass. `.env` remains ignored and untracked; the loaded key matches the unchanged local file and no key or credential fingerprint was found in public source, reports, frontend bundles or Git diff. [Consolidated targeted verification](evaluation/phase6-targeted-verification.json).
