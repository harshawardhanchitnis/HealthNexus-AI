# Resilience Copilot — Phase 6

Implemented in the existing repository on 28 September 2026. Official SDK integration, typed tools, bounded orchestration and the UI are implemented. **Live Gemini verification is pending: no server-side `GEMINI_API_KEY` is configured here.** Mocked orchestration and explicitly labelled offline workflows are verified separately.

## Model, SDK and setup

The exact model is `gemini-3.8-flash`, using `google-genai==2.25.0` and `from google import genai`. Google lists this model's function calling, structured output and thinking support on its [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash). The application uses the recommended [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), native function declarations and `previous_interaction_id`. Default thinking is `medium`; `low` is also accepted. Prompt version: `healthnexus-system-v1`; configuration: `copilot-config-v1`.

The SDK requires Pydantic 2.12.5 or newer. Requirements pin `pydantic==2.13.5`; all 156 existing tests pass with that upgrade. No retraining or profile regeneration is required.

Create/manage a key in [Google AI Studio](https://aistudio.google.com/apikey). AI Studio may inspect/test prompts; HealthNexus is an Angular/FastAPI application, not an application built or hosted in AI Studio. All model calls originate from FastAPI.

Install backend requirements and set values in the ignored repository `.env` or backend process environment:

```dotenv
GEMINI_API_KEY=YOUR_SERVER_SIDE_KEY
GEMINI_MODEL=gemini-3.8-flash
GEMINI_ENABLED=true
GEMINI_THINKING_LEVEL=medium
```

Restart the backend. Never put keys in Angular, browser configuration, URLs or committed files. Status exposes only a configured boolean and safe labels. No startup inference call occurs. Any other configured model is rejected; runtime 404 becomes `model_unavailable`, without substitution. Missing configuration, configured-but-untried and runtime outcomes remain distinct.

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

The bounded question/context and whitelist go to `client.interactions.create`. Returned `function_call` steps are validated and executed locally. `function_result` steps preserve each call ID and carry an evidence ID plus shaped authoritative data. Previous interaction ID, system instruction, tools, thinking and response schema are supplied each turn. See Google's [function calling](https://ai.google.dev/gemini-api/docs/function-calling) and [structured outputs](https://ai.google.dev/gemini-api/docs/structured-output) documentation.

The loop permits ten tool calls, including invalid attempts. SDK automatic execution is not used. Final JSON validates as situation, risks, planning actions and remaining gaps. Every claim references exact dot fields in a **fresh current-request tool result**. The server resolves fields into evidence values and rejects nonexistent/oversized references, unsupported numeric literals, overstated optimality and executed-transfer wording. Typed objects are rendered without parsing arbitrary Markdown or HTML.

The server adds actual operational-result objects, scenario/run IDs, tool statuses/timings, country/profile/geography, timestamp, model versions, prompt/config versions, transport label, interaction ID and returned usage. The UI's plan metrics, quantities and risk/reserve tables read those authoritative objects directly. Mixed-unit totals are labelled accounting tallies, never interchangeable doses. Reference/numeric checks improve grounding; they are not a proof that every qualitative interpretation is correct. Administrators should inspect engine evidence.

No private chain of thought is requested, displayed or audited. Application state keeps opaque provider IDs and active scenario/plan IDs; new factual claims still require fresh tools. Country/profile/geography/mode/origin changes require a new conversation. Same-conversation concurrency is rejected.

Conversations expire after 30 idle minutes and are capped at 20. Request progress and development audit are capped at 100; two workflows can run concurrently. All are process-local. Audit includes operational question/context, IDs, model/mode, trace, latency and returned usage. Common clinical/personal-record requests are refused before provider submission and not audited. Questions containing the configured key are rejected. These guards are limited: never submit patient information or credentials. Production authentication is not implemented.

Interactions use Google's stored history. Provider retention is separate: see [Google's retention documentation](https://ai.google.dev/gemini-api/docs/interactions-overview#data-storage-and-retention). **New conversation / DELETE clears local state/audit/progress only, not Google's stored history.** Provider deletion and retention controls remain an administrator responsibility. Application correctness never depends on opaque model memory.

## Bounds, errors and progress

Messages: 2,000 characters. Model output: 2,400 tokens per interaction. Tools: maximum 28,000 JSON characters, usually smaller. Facilities/candidates, warnings, transfer and receiver-risk detail are explicitly limited/paginated. No 540-day histories, fitted artifacts, 500 paths or complete national projections are sent. Oversized shaped results request a narrower scope.

Provider timeout is 25 seconds. SDK retries are disabled; the application permits one retry after 250 ms for 502/503 only. Auth, invalid configuration, quota, malformed responses and other errors are not retried. The 120-second deadline is cooperative between calls/tools: an executing deterministic service is not forcibly terminated. Existing solver time bounds remain. Tool time and provider network time are recorded separately. Usage is copied from provider fields; cost/pricing is not fabricated.

Safe errors cover missing/invalid key, disabled configuration, unavailable model, timeout, quota, malformed calls/arguments, stale scenario/profile, unavailable artifacts, invalid evidence and response schema. Failed Gemini requests remain failures; no automatic offline substitution occurs. The UI polls context-scoped progress every 900 ms and shows actual tool states. Fast requests may finish before the first poll; completed traces remain visible.

## Offline mode and verification

Without credentials the UI opens and shows **Gemini API not configured**. Users explicitly select **Use offline summaries** or offline mode. Such answers remain labelled **OFFLINE / deterministic summary**, with null model/interaction ID and zero provider time.

Offline templates cover baseline risks, provenance, evaluation, donor explanation, profile comparison and the documented dengue workflow. Explicit dengue days/severity are parsed and validated. This is limited template routing, not general AI reasoning; unsupported questions may return baseline summaries. Profile comparison reads independent baseline profiles and does not silently simulate emergencies.

Most tests use scripted Gemini transport: sequential calls, schemas, whitelist, scope/profile, fresh evidence, retries, state, limits, provider failures and clinical refusal. An HTTP mock also exercises the installed official SDK's wire encoding. Positive planning tests execute actual local OR-Tools; only the model is mocked.

```powershell
.\.venv\Scripts\python.exe scripts\verify_gemini.py --mock
.\.venv\Scripts\python.exe scripts\verify_gemini.py --offline
# Explicit opt-in after server key configuration:
.\.venv\Scripts\python.exe scripts\verify_gemini.py --live
```

Live verification makes four bounded workflows: Pune risks, ready severe dengue/redistribution, constrained equivalent, and inventory provenance. It saves sanitized model/tool evidence and checks exact solver/impact/capacity/transfer/context fields against stored engines. It fails on errors rather than hiding them. With no key it writes `not_run` before network access. Preserve failed evidence and do not claim success until it passes.

207 tests pass: existing 156 plus 51 Copilot cases. Compilation, dependency checks, strict TypeScript and production build pass. Four-case [mock](evaluation/phase6-mock.json) and [offline](evaluation/phase6-offline.json) verification pass. Mock responses carry `transport: mock`; they are not real Gemini evidence. Live availability, model behaviour, inference latency and token consumption remain **unverified because credentials are absent**.

The ready Pune tools reproduce 41,763 target, 17,745 safe capacity, 15,679 transferred accounting items / 10 lanes and 26,084 unresolved, with zero donor risks/violations. Constrained remains 30,230 unresolved / zero capacity / zero transfers. OR-Tools and greedy tie. IVF/PCM retain shortage and 100% conditional 14-day risk; AMX/IFA/ORS risk improves to zero. These values come from the unchanged engines and are absent from the system prompt.

See [Phase 6 report](phase6-report.md) for final browser/performance evidence. No FedAvg is implemented. The software boundary is ready for Phase 7 country-node development; live Copilot acceptance still requires credentialed verification.
