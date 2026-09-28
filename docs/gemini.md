# Resilience Copilot — Phase 6

HealthNexus uses Gemini 3.8 Flash as its primary reasoning model with Gemini Flash-family availability failover. All five candidates pass deterministic protocol/grounding tests; successful live fallback interpretation is still unverified. The latest automatic live chain received three HTTP 503 HIGH DEMAND responses before the retained daily verification ceiling stopped further requests. See [current failover evidence](phase6-failover-report.md).

## Model, SDK and setup

The preferred primary model is `gemini-3.8-flash`, using `google-genai==2.25.0` and `from google import genai`. Google lists this model's function calling, structured output and thinking support on its [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash). The application uses the recommended [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), native function declarations and `previous_interaction_id`. Default thinking is `medium`; `low` is also accepted. Prompt version: `healthnexus-system-v3`; configuration: `copilot-config-v4-failover`.

The SDK requires Pydantic 2.12.5 or newer. Requirements pin `pydantic==2.13.5`; all 156 existing tests pass with that upgrade. No retraining or profile regeneration is required.

Create/manage a key in [Google AI Studio](https://aistudio.google.com/apikey). AI Studio may inspect/test prompts; HealthNexus is an Angular/FastAPI application, not an application built or hosted in AI Studio. All model calls originate from FastAPI.

Install backend requirements and set values in the ignored repository `.env` or backend process environment:

```dotenv
GEMINI_API_KEY=YOUR_SERVER_SIDE_KEY
GEMINI_MODEL=gemini-3.8-flash
GEMINI_MODEL_PRIMARY=gemini-3.8-flash
GEMINI_MODEL_FALLBACKS=gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite
GEMINI_FAILOVER_ENABLED=true
GEMINI_ENABLED=true
GEMINI_THINKING_LEVEL=medium
```

Restart the backend. Never put keys in Angular, browser configuration, URLs or committed files. Status exposes only a configured boolean and safe labels. No startup inference call occurs. Only the five approved stable Flash-family models are accepted. Primary configuration takes precedence over legacy GEMINI_MODEL; absent new settings, the documented five-model chain is used. The actual ignored .env is never edited by the failover implementation. Missing configuration, configured-but-untried and runtime outcomes remain distinct.

## Architecture and tools

`backend/app/ai/` separates config/transport, schemas, whitelist, service adapters, orchestration, evidence, system instruction, deterministic fallback and routes. Tools use the same service objects as existing REST routes. There is no self-HTTP or replacement forecast/solver policy.

| Registered tool | Existing authoritative service |
|---|---|
| `get_network_summary` | Repository, network summarizer, ScenarioEngine baseline warnings; bounded facility/geography IDs |
| `get_facility_status` | Repository inventory/beds/personnel/known receipts and baseline warning summary |
| `get_forecast` | ForecastService saved model, empirical intervals, evaluation and conditional stock trajectory; 1/7/14 days |
| `get_warnings` | Existing baseline/scenario warning results, filters and pagination; rules retain their 14-day horizon |
| `get_warning_summary` | Same filtered warnings and existing summary function |
| `get_scenario_presets` | Existing scenario enum, severity parameters and duration limits |
| `run_emergency_scenario` | ScenarioEngine; immutable externally specified shock and measured comparison |
| `get_scenario_comparison` | ScenarioStore with current source fingerprint/model SHA verification |
| `get_redistribution_preview` | OptimizationService's real deficits, protected donors and lane opportunities |
| `optimize_redistribution` | Actual OR-Tools CP-SAT quantities/routes and measured greedy comparison |
| `get_optimization_result` | Actual stored plan, revalidated preparation identity, paginated rationale/reserves/risks |
| `get_model_performance` | Saved country/profile-bound evaluation on simulated histories |
| `get_data_provenance` | Repository calibration/profile/seed/origin, model identity and attributed public catalogue |

Read tools are automatic. Simulation/optimization requires **Allow non-destructive simulations and optimizer plans**, an explicit administrator request flag. No tool sends orders, contacts hospitals, executes transfers or changes baseline inventory. A facility-only baseline plan requires a matching facility scenario because the existing baseline planner operates on geographic scopes.

Strict Pydantic declarations require country/profile, enums and bounds. Model arguments are untrusted. Server checks selected country, profile and geography, then existing domain validators. Profile comparison needs an explicit request flag and retains separate result metadata. Gemini cannot enable planning/comparison through tool arguments or invoke arbitrary functions/code. Tool-returned labels and imported text are data, never higher-priority instructions.

## Native loop, evidence and state

The bounded question/context and a server-selected intent whitelist go to `client.interactions.create`. Returned `function_call` steps are validated against that subset and executed locally. `function_result` steps preserve call IDs and carry evidence IDs plus compact authoritative data. System instruction/config are resubmitted each turn. Tools and answer schema are never sent together: the observed endpoint rejected that combination. A returned plan immediately continues into schema-only synthesis, avoiding the readiness round trip. Provenance/reliability and donor follow-up prefetch fresh read-only tools, explicitly audited as server executions, for one schema-only request. These revised patterns are SDK/mock-tested; actual endpoint acceptance is pending. See Google's [function calling](https://ai.google.dev/gemini-api/docs/function-calling) and [structured outputs](https://ai.google.dev/gemini-api/docs/structured-output) documentation.

The loop permits ten tool calls, including invalid attempts. SDK automatic execution is not used. Final JSON validates as situation, risks, planning actions and remaining gaps. Every claim references exact dot fields in a **fresh current-request tool result**. The server resolves fields into evidence values and rejects nonexistent/oversized references, unsupported numeric literals, overstated optimality and executed-transfer wording. Typed objects are rendered without parsing arbitrary Markdown or HTML.

The server adds actual operational-result objects, scenario/run IDs, tool statuses/timings, country/profile/geography, timestamp, model versions, prompt/config versions, transport label, interaction ID and returned usage. The UI's plan metrics, quantities and risk/reserve tables read those authoritative objects directly. Mixed-unit totals are labelled accounting tallies, never interchangeable doses. Reference/numeric checks improve grounding; they are not a proof that every qualitative interpretation is correct. Administrators should inspect engine evidence.

No private chain of thought is requested, displayed or audited. Application state keeps opaque provider IDs and active scenario/plan IDs; new factual claims still require fresh tools. Country/profile/geography/mode/origin changes require a new conversation. Same-conversation concurrency is rejected.

Conversations expire after 30 idle minutes and are capped at 20. Request progress and development audit are capped at 100; two workflows can run concurrently. All are process-local. Audit includes operational question/context, IDs, model/mode, trace, latency and returned usage. Common clinical/personal-record requests are refused before provider submission and not audited. Questions containing the configured key are rejected. These guards are limited: never submit patient information or credentials. Production authentication is not implemented.

Interactions use Google's stored history. Provider retention is separate: see [Google's retention documentation](https://ai.google.dev/gemini-api/docs/interactions-overview#data-storage-and-retention). **New conversation / DELETE clears local state/audit/progress only, not Google's stored history.** Provider deletion and retention controls remain an administrator responsibility. Application correctness never depends on opaque model memory.

## Bounds, errors and progress

Messages: 2,000 characters. Model output: 2,400 tokens per interaction. Tools: maximum 28,000 JSON characters, usually smaller. Facilities/candidates, warnings, transfer and receiver-risk detail are explicitly limited/paginated. No 540-day histories, fitted artifacts, 500 paths or complete national projections are sent. Oversized shaped results request a narrower scope.

Provider timeout is 60 seconds. SDK retries are disabled. With failover enabled, each model gets one bounded attempt before an eligible availability failure advances the chain. With failover disabled, the legacy single bounded 502/503 retry remains. Authentication and application/grounding failures never trigger model switching. The 300-second deadline is cooperative between calls/tools: an executing deterministic service is not forcibly terminated. Existing solver time bounds remain. Tool time and provider network time are recorded separately. Usage is copied from provider fields; cost/pricing is not fabricated.

Safe errors cover missing/invalid key, disabled configuration, unavailable model, timeout, quota, malformed calls/arguments, stale scenario/profile, unavailable artifacts, invalid evidence and response schema. Failed Gemini requests remain failures; no automatic offline substitution occurs. The UI polls context-scoped progress every 900 ms and shows actual tool states. Fast requests may finish before the first poll; completed traces remain visible.

## Offline mode and verification

Without credentials the UI opens and shows **Gemini API not configured**. Users explicitly select **Use offline summaries** or offline mode. Such answers remain labelled **OFFLINE / deterministic summary**, with null model/interaction ID and zero provider time.

Offline templates cover baseline risks, provenance, evaluation, donor explanation, profile comparison and the documented dengue workflow. Explicit dengue days/severity are parsed and validated. This is limited template routing, not general AI reasoning; unsupported questions may return baseline summaries. Profile comparison reads independent baseline profiles and does not silently simulate emergencies.

Most tests use scripted Gemini transport: sequential calls, schemas, whitelist, scope/profile, fresh evidence, retries, state, limits, provider failures and clinical refusal. An HTTP mock also exercises the installed official SDK's wire encoding. Positive planning tests execute actual local OR-Tools; only the model is mocked.

```powershell
.\.venv\Scripts\python.exe scripts\verify_gemini.py --mock
.\.venv\Scripts\python.exe scripts\verify_gemini.py --offline
# Future explicit opt-in ONLY after quota reset and user authorization:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --acceptance --resume
```

Default verification uses positive planning, its same-conversation donor follow-up, a locally prepared constrained fixture's interpretation and combined provenance/reliability. Mock expectation is eight provider requests. The persistent live daily ledger caps attempts at ten including retries; `GEMINI_DAILY_VERIFICATION_BUDGET` can lower that cap. `--case positive|constrained|provenance`, `--resume` and versioned per-case PASS evidence avoid rerunning compatible checks. A local budget denial sends no request. The report separates provider requests, local tools and fixture setup. See [full strategy, identity/invalidation, rate handling and commands](phase6-budget-report.md).

281 tests pass: the previous 237 plus 44 failover cases. Compilation, dependency checks, strict TypeScript and production build pass. New [mock](evaluation/phase6-budget-mock.json) and [offline](evaluation/phase6-budget-offline.json) acceptance pass. Mock responses carry `transport: mock`; they are not real Gemini evidence. Earlier [live partial evidence](evaluation/phase6-live-acceptance.json) is preserved; final grounded live answers, revised protocol and complete acceptance remain pending successful live provider availability and verification budget.

The ready Pune tools reproduce 41,763 target, 17,745 safe capacity, 15,679 transferred accounting items / 10 lanes and 26,084 unresolved, with zero donor risks/violations. Constrained remains 30,230 unresolved / zero capacity / zero transfers. OR-Tools and greedy tie. IVF/PCM retain shortage and 100% conditional 14-day risk; AMX/IFA/ORS risk improves to zero. These values come from the unchanged engines and are absent from the system prompt.

See [Phase 6 report](phase6-report.md) for earlier browser/performance evidence and [the efficiency report](phase6-budget-report.md) for current verification. No FedAvg is implemented. Phase 7 remains deferred until Phase 6 acceptance is completed.

## Availability failover

Exact default order: **gemini-3.8-flash → gemini-3.7-flash → gemini-3.6-flash → gemini-3.5-flash → gemini-3.5-flash-lite**. There is no 3.1/2.5/Pro/preview/non-Google fallback. Every candidate uses the same project/key, registry, strict tool schemas, local engines and claim validation. All use medium thinking for acceptance, supported by [official thinking documentation](https://ai.google.dev/gemini-api/docs/thinking). No model-specific answer templates or calculations are introduced.

Eligible triggers are 503/high demand, bounded provider timeout, explicitly unavailable configured model endpoint (404), and a classified RPM/TPM/RPD 429 whose quota violations all explicitly identify the current model. Ambiguous/project-wide 429, missing interaction 404, 401/403, 400, bad schema/evidence, clinical refusal, incompatible geography/profile and local tool failures remain visible failures. All eligible models unavailable returns provider_unavailable_all_models; a local budget refusal retains quota_budget_exhausted_locally. Offline mode is always explicit.

Model switching starts a fresh interaction without foreign previous_interaction_id or function-result call IDs. A bounded (120 kB UTF-8) handoff contains validated context, current scenario/plan IDs and compact current-request evidence. Full local objects stay unchanged. The successful model remains sticky within the conversation. A new conversation normally tries primary again. Known model-specific quota exhaustion is held in a process-local circuit: RPD until next Pacific midnight, RPM/TPM for at least 60 seconds or the supplied delay. This does not claim remaining quota; AI Studio remains authoritative. Google documents [project quotas and model-specific limits](https://ai.google.dev/gemini-api/docs/rate-limits).

Two repeated schema/evidence/grounding failures mark a model UNSUITABLE_FOR_HEALTHNEXUS in this process and exclude it from automatic selection. The failing request is not retried on another model. Status and response metadata expose exclusions. This is a limited process-local quality guard, not live quality certification or a durable production registry.

Answers/progress/audit include requested/effective model, attempted chain, reasons, handoffs, requests/interactions/failures/timings per model. Effective model is null when no interaction succeeded; selected_model separately identifies the candidate. The UI displays the actual answering model, a subtle fallback indicator and provider trace. No hidden reasoning, headers or secrets are exposed. Resilience-status summaries use two audited fresh server-prefetch tools and one schema-only interpretation request; positive planning retains native function calling.

Verifier attempts across all models share the same persistent ten-request ceiling. Old ledger counts remain as legacy-unattributed rather than inventing per-model attribution. Model chain/config/implementation identity participates in PASS invalidation; resumed donor follow-up retains the saved effective model.

```powershell
# First live smoke, only within the retained available budget:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case resilience --resume
# Only after smoke PASS and when budget permits:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --acceptance --resume
```

[Measured failover report](phase6-failover-report.md) distinguishes scripted compatibility from live 503 evidence. Phase 6 remains incompletely accepted; Phase 7 has not started.

### Targeted verifier override

The normal daily verification cap remains ten cumulative sends. Explicit CLI `--budget 14` permits a bounded extension without deleting or resetting the ledger; an environment value above ten is rejected. `--model` selects only a configured candidate for verification, with production order unchanged. `--case model-smoke` requires that selection and uses two fresh authoritative reads plus one structured interpretation attempt per reached model. All attempts share the same ledger.

```powershell
# Targeted command executed under explicit user authorization:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case model-smoke --model gemini-3.5-flash --budget 14 --resume
# Only after compatible smoke PASS, within remaining authorized budget:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live --case positive --model gemini-3.5-flash --budget 14 --resume
```

Compatible smoke PASS restores the actual successful model, keeping even Flash-Lite sticky in later verification. Availability errors can advance only through the remaining configured suffix; schema/grounding failures remain visible. The targeted live attempt sent one request each to 3.5 Flash and Flash-Lite; both returned 503 HIGH DEMAND. There is no successful live model or validated final response. Historical ten sends plus two new sends total **12/14**; the two unused sends were conserved. [Measured evidence and acceptance limits](phase6-failover-report.md#targeted-remaining-model-acceptance--28-september-2026).
