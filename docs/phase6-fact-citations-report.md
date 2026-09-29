# Phase 6 — request-local fact citations — 29 September 2026

This checkpoint continues `c526378`. Gemini now selects server-issued fact IDs rather than reconstructing dotted source paths. The public answer/evidence shape stays compatible with the existing UI. Full Phase 6 workflow acceptance remains pending.

## Contract and source ownership

The provider-only `FactDraftAnswer` accepts claims containing `text` and `evidence_refs`. Extra citation paths, values, units and source objects are forbidden. `FactCatalogue` gives each request a fresh server-generated namespace, independent of credentials and caller-provided IDs. Within that namespace, sorted evidence paths produce deterministic IDs preserving evidence-object identity, such as `e1_0123456789abcdef_f003`. Reusing an envelope or handing off within the same request retains its IDs; a new request gets a fresh namespace and rejects previous IDs.

The compact provider catalogue supplies labels, exact values, units and context. Canonical dotted paths stay in the server registry. The schema enumerates current IDs, and server membership validation independently rejects unknown, malformed, stale or duplicate citations. Labels never resolve citations. There is no suffix matching, alias, fuzzy matching or typo repair.

The server resolves each selected ID to its exact evidence object/path/value/unit, verifies the source has not changed, then runs the existing exact numeric, scope/origin, solver terminology and clinical safety checks. Only the server creates the existing public `references` and evidence objects. Catalogue units are copied into those objects; values are not calculated or converted. Two warning-counter metadata units are clarified as facilities and medicine resource types, rather than warnings. Operational calculations remain unchanged.

Qualitative claims retain evidence requirements. Conservative topic checks reject unrelated operational evidence (for example staff evidence for bed pressure), and reject WAPE presented as accuracy. These checks and the existing safety guards are not an exhaustive natural-language truth proof. Numeric literal validation remains exact: no rounding, arithmetic, unit conversions or deriving percentages. A derived value is allowed only when already explicitly supplied by an authoritative tool.

Each tool envelope exposes at most 64 facts. Read-only resilience synthesis receives facts/context without raw operational objects. Native discovery/planning still receives compact objects needed for tool orchestration; handoff carries fact catalogues and local handles within the existing 120 kB bound, without depending on another model's hidden state. Full local evidence remains authoritative. Sanitized diagnostics retain claim index/text, supplied/cited/unknown IDs, resolved facts and context; no keys, headers, hidden reasoning or environment dumps are included.

## Exact latest failure reproduction

The previous live response cited `bed_utilisation`, which did not resolve to the supplied `summary.bed_utilisation`. That rejected response and its report remain unchanged.

The controlled migration uses the actual Pune snapshot and the requested sentence, “Bed utilisation reflects notable operational pressure.” Its citation `e1_0123456789abcdef_f003` resolves internally to `summary.bed_utilisation = 79.8%` and passes. Citing `bed_utilisation` still fails with `unknown_fact_id`. No path repair or replacement of the old live answer occurs. [Migration evidence](evaluation/phase6-facts-migration.json).

## Deterministic verification

**436 backend tests pass in 119.98 seconds**: all 385 previous cases retained, plus 39 fact-contract cases and 12 verifier cases. Existing scripted fixtures were migrated to IDs from their actual supplied catalogues; no existing test was deleted. Coverage includes stale/unknown IDs, duplicate labels and field names, exact/unsupported numbers, unrelated qualitative citations, geography/profile/origin isolation, WAPE misuse, present/absent derived facts, immutable sources, schema restrictions, diagnostic sanitation and exact wire-send accounting. One existing Starlette/AnyIO deprecation warning remains.

Shared mock interpretation passes for **gemini-3.5-flash-lite** and **gemini-3.6-flash**, with valid schemas, resolved IDs, grounded numbers, correct context, zero unknown IDs and zero unsupported numbers. Mocks use one common transport and actual tool facts, with no model-specific canned answers. Official SDK HTTP mocks verify current ID enums on the wire and exactly one send for both HTTP 200 and 503. [Mock evidence](evaluation/phase6-facts-mock.json), [pre-live gates](evaluation/phase6-facts-regression.json).

Python compilation, Windows `pip check`, strict TypeScript and Angular production build pass. The unchanged frontend bundle remains 387.99 kB / estimated 104.69 kB transfer. No UI redesign, deployment, accepted-model retraining or canonical data regeneration occurred. Existing regression fixtures use temporary test artifacts only.

## Operational and federation preservation

| Severe 14-day Pune dengue | Redistribution-ready | Constrained |
|---|---:|---:|
| Target deficit before | 41,763 | 30,230 |
| Safe donor capacity | 17,745 | 0 |
| Transferred accounting items | 15,679 | 0 |
| Lanes | 10 | 0 |
| Unresolved target | 26,084 | 30,230 |
| Donor violations / new donor risks | 0 / 0 | 0 / 0 |

These are unchanged local engine measurements, not model calculations. Both solver statuses remain `OPTIMAL`; resource conservation holds. Ready receiver critical medicine warnings remain 7 → 0; maximum conditional stock-out risk remains 100% → 100%, with unresolved shortages retained. All ten country/profile partitions validate. Original saved federation run `fdbaaedb-773d-4b67-be50-ad406b130950`, weights, evaluation and evidence remain unchanged: five rounds, zero raw records shared, 4.8010934 seconds and 614,235 exchanged bytes. [Canonical verification](evaluation/phase6-facts-canonical.json).

Production fallback order is unchanged: 3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite. No operational or federation engine files changed. Pre-live checks preserve 328 of 336 locked original file identities; the eight exceptions are intentional Copilot contract/metadata and scripted-test fixture changes. Original reports remain intact.

## Authorized live smoke scope

The new verifier uses the existing key/project and medium thinking. Its exact question is “Summarize the current resource resilience status in Pune.” Context is IN / MH / MH-PUNE / redistribution-ready. It permits one independent Flash-Lite request first, with no retry, fallback or previous interaction ID. Only a complete HTTP/schema/ID/semantic/numeric/context PASS authorizes a second independent request. Any failure stops the run; two passes also stop it. No full dengue live workflow is authorized.

The official SDK HTTP send hook appends actual sends to the preserved **23-request historical ledger**. Preflight itself does not append. The local two-send ceiling applies across the run and cannot be reset/replayed or rolled over to a new day. This local ledger is not a provider quota measurement. Raw original ledger fields and per-model history are preserved; no API key, project or billing changes occur. `scripts/verify_fact_citations.py --mock` is reproducible without Google calls. `--live` is bounded by this explicit authorization and recorded pre-live gates, not a general invitation to repeat calls.

## Measured live results

Both independent requests were served by **gemini-3.5-flash-lite**, with medium thinking, using the official SDK and the existing key/project. Each made exactly one actual HTTP send and two fresh local evidence reads (`get_network_summary` and `get_warning_summary`). Neither used native function calling in this read-only smoke; the broader native planning workflow is mock-tested and remains pending live acceptance.

| Acceptance / measurement | Smoke 1 | Smoke 2 |
|---|---:|---:|
| HTTP | 200 | 200 |
| Schema / fact-ID resolution | PASS / PASS | PASS / PASS |
| Qualitative topic/safety grounding / exact numeric grounding | PASS / PASS | PASS / PASS |
| Country/profile/geography/origin validation | PASS | PASS |
| Unknown IDs / unsupported numeric claims | 0 / 0 | 0 / 0 |
| Actual HTTP sends | 1 | 1 |
| Provider seconds, excluding pacing | 9.329 | 9.091 |
| Local tool seconds | 3.099 | 0.047 |
| Input tokens | 7,445 | 7,645 |
| Output tokens | 327 | 430 |
| Provider-reported thought token count (no content retained) | 774 | 1,229 |
| Total tokens | 8,546 | 9,304 |

Both drafts contain no numeric literals. Both select the current request's bed fact ID and resolve exactly to `summary.bed_utilisation = 79.8%`; their fresh namespaces differ. No field path is generated in provider citations. Source references, complete sanitized drafts, facts and actual usage are retained in [live evidence](evaluation/phase6-facts-live.json).

The qualitative descriptions pass the configured relevance/safety guards. Wording such as “high”, “stable” or “driven by” remains model interpretation; aggregate evidence does not prove temporal stability or causation. This limited smoke result is not exhaustive semantic validation or full workflow acceptance. Authoritative numeric panels remain server-owned.

The verifier stopped after exactly **two** authorized sends. The original **23** historical requests, original day and all per-model history remain intact; total local accounting is **25**, with Lite history **4 + 2 = 6**. All other models received zero new sends. No remaining provider quota or reset time is inferred. Final preservation checks retain 327 original file identities; the additional ninth exception is the strictly validated append to the historical ledger. `.env`, key, project, billing, UI, accepted data/model/federation assets and production fallback order are unchanged. Credential-pattern scanning passes for tracked/non-ignored source and frontend bundles; this is not penetration testing. [Final security and accounting](evaluation/phase6-facts-security.json).

**Live grounded smoke acceptance: PASS 2/2. Full Phase 6 workflow acceptance remains pending.**
