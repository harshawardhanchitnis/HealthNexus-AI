# Phase 6 — final synthesis budget fix — 29 September 2026

Continues `4abf8bd`. Native planning retains **medium / 2,400 generation tokens**. Final structured synthesis now uses **low / 4,096**, with approximately three to five concise claims. The final stage explains current server facts; numeric panels, canonical field paths, exact values, units and provenance remain server-owned. The production fallback order and all fact-ID/numeric/scope/semantic validators are unchanged.

**Positive live workflow remains pending because: the completed synthesis describes advisory transfers as executed actions.** Native orchestration is **PASS** from the preserved previous live run; positive final synthesis is **FAIL**, and positive workflow acceptance is **FAIL**. No additional live request or later acceptance case was attempted.

## Mitigation and compatibility

The previous final request used medium / 2,400, returned `incomplete` and truncated JSON, and reported 2,303 thought tokens versus 80 output tokens. Generation-budget exhaustion remains an **inference**, because the provider gave no separate definitive stop reason.

Configuration version is `copilot-config-v5-stage-generation`; prompt version is `healthnexus-system-v6-compact-synthesis`. `GEMINI_THINKING_LEVEL=medium` retains native planning behavior; the new example-only `GEMINI_SYNTHESIS_THINKING_LEVEL=low` controls synthesis. The failover wrapper respects the server-selected stage, including after safe model handoff. Diagnostics record actual stage configuration and system instruction size. Cached verifier evidence identities now include synthesis configuration and the complete synthesis instruction.

The installed official `google-genai==2.25.0` defines `low` in its Interactions thinking type. SDK HTTP mocks for Flash-Lite and 3.6 accept the exact wire configuration and produce valid grounded compact outputs through the shared unchanged validators. The single live Lite request also accepted low / 4,096 and completed generation. This proves this request's transport/configuration compatibility, **not** acceptance of its interpretation, or live compatibility of other models. Lower untested thinking settings were not used.

## Evidence reuse — path B

Process-local objects from the prior native run were unavailable. The final-only verifier reconstructed and revalidated the actual scenario and optimization using the **exact previously validated native inputs**, including the registered default seed 42 and original resource order. The optimizer independently recalculated the plan. It compared forecast/profile/origin/snapshot identities, complete impacts, and all saved transfer quantities, distances, donor reserves and risks against the preserved live envelopes. Conservation and immutability checks pass.

This is **deterministic reconstructed authoritative evidence**, not the original in-memory scenario or plan. The new live synthesis source IDs were `abca928e-d3f6-41a7-a5d9-708de3f561a6` and `e2ea4b73-446b-4909-900b-08f80042f821`. The original native IDs, source report checksum and model/snapshot identities are retained separately in the [new live trace](evaluation/phase6-synthesis-live.json). The provider received fresh request-local fact catalogues, without stored Gemini narrative, predetermined answer, native tools or a previous provider interaction ID.

| Authoritative engine measurement | Reproduced positive |
|---|---:|
| Target before | 41,763 |
| Safe donor capacity | 17,745 |
| Transferred accounting items | 15,679 |
| Transfer lanes | 10 |
| Unresolved target | 26,084 |
| Donor violations / new donor risks | 0 / 0 |
| Solver status | OPTIMAL |

The **local regression** constrained case remains 30,230 target/unresolved, zero safe capacity, transfers and lanes. All ten country/profile partitions and saved five-country federation pass. No live constrained interpretation was run. [Canonical verification](evaluation/phase6-synthesis-canonical.json).

## The single live request

| Measurement | Actual result |
|---|---|
| Model | gemini-3.5-flash-lite |
| HTTP / provider status | 200 / completed |
| Synthesis configuration | low / 4,096 tokens |
| Input / output / thought tokens | 10,557 / 470 / 0 |
| Total tokens | 11,027 |
| Provider latency | 2.958 seconds |
| Output length | 1,220 characters, complete JSON |
| Claims | 4 |
| Structured schema | PASS — exact saved text independently parsed locally |
| Qualitative factual review | FAIL — unsafe execution wording |
| Retries / fallback / native provider requests | 0 / 0 / 0 |
| Actual new sends / retained ledger | 1 / 28 + 1 = 29 |

The answer described the optimizer as **“executing safe transfers”**, and said **“Despite executing authorized transfers”**. These are advisory simulation recommendations; no supplies were physically moved or transfers authorized. The user explicitly disallowed execution claims. The response was therefore not accepted, despite complete JSON and successful generation. No stored replacement answer or edited model narrative was substituted.

There was also a verifier defect: the initial final-only check unnecessarily required a nonempty interaction ID. This request used `store=False`; the pinned SDK defines `Interaction.id` as optional with an empty-string default, and the completed live response had an empty ID. The initial trace therefore records `response_incomplete` even though **the actual provider status was completed and JSON was not truncated**. The original trace is retained unchanged. The final-only verifier now accepts completed stateless responses with optional IDs; production stored conversation-ID checks remain unchanged. SDK mocks cover both populated and empty IDs. Additional acceptance tests reject execution wording without changing production grounding or operational engines.

The initial live verifier stopped before fact-ID resolution, exact numeric validation and solver terminology validation. Those stages and their unknown-ID/unsupported-number counts are **not reached / not established**, not fabricated PASS or zero. Local schema parsing and manual factual review suffice to reject the actual output. The [separate review](evaluation/phase6-synthesis-review.json) clearly distinguishes the initial verifier defect from the unacceptable interpretation. No second live request tested the local correction.

## Regression and preservation

Before the live send, **479 backend tests passed in 71.00 seconds**, retaining all 459 previous cases plus 20 synthesis/verifier tests. Shared Lite/3.6 SDK mocks, Python compilation, Windows `pip check`, canonical results, saved federation and credential-pattern/preservation gates passed. [Preflight](evaluation/phase6-synthesis-preflight.json).

After the stopped attempt, five local cases were added for optional stateless IDs and execution wording. Final regression passes **484 tests in 120.78 seconds**, retaining all 459 previous cases plus 25 new cases; compilation, dependencies and security/preservation pass. Measurements are recorded in [final local verification](evaluation/phase6-synthesis-final.json). The [shared SDK mocks](evaluation/phase6-synthesis-mock.json) remain cost-free. Frontend files were not changed, so the prior successful strict TypeScript and Angular production build were preserved; no new frontend build is claimed. One existing Starlette/AnyIO deprecation warning remains.

All protected original operational/forecasting/OR-Tools/federation files, accepted data/model artifacts, UI and historical reports remain unchanged. `.env` is unchanged, ignored and untracked; the same key/project and billing state were retained. Production order remains 3.8 → 3.7 → 3.6 → 3.5 → 3.5 Flash-Lite. The ledger preserves its original day, every historical field and per-model counts, appending only this Lite wire attempt (Lite 9 → 10). The authorization is consumed permanently; changing dates or restoring an old ledger cannot replay it. No deployment or later phase was started.

## Reproducible local commands and stop condition

```powershell
.\.venv\Scripts\python.exe -m pytest backend -q --junitxml=artifacts/phase6-synthesis-pytest.xml
.\.venv\Scripts\python.exe scripts/verify_positive_final.py --mock --case positive-final
.\.venv\Scripts\python.exe -m compileall -q backend scripts
.\.venv\Scripts\python.exe -m pip check
```

The dedicated `--preflight` gate and `--live --case positive-final` verifier were used for this task's one authorization. Live mode requires the original private preservation baseline, passing local gate, historical ledger and exclusive lease, and refuses replay after the one-send journal is created. Do **not** delete journals or reset accounting to reuse it. Additional live acceptance requires a new explicit user authorization.

Same-conversation donor follow-up, constrained interpretation and provenance/forecast reliability remain untested live in this task. Positive synthesis acceptance also remains pending. We stop here for the next decision, rather than increasing the ceiling or retrying.

**Positive live workflow remains pending because: the completed synthesis describes advisory transfers as executed actions.**
