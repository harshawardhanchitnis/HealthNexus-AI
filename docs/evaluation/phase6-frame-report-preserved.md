# Phase 6 final semantic-frame acceptance — 29 September 2026

**Phase 6 remains pending because: the positive live semantic frame repeated `RESOURCE_PRESSURE`, violating the duplicate-kind rule.**

Continues HEAD `a62f098` from the intentionally modified working tree. All previous changes and failed-run evidence were preserved. No reset, stash, checkout or completion commit was made.

## Provider output and server output

**Provider output = semantic frame / selected evidence. Server output = deterministically rendered user-facing prose.** Gemini does not author operational sentences in emergency planning, donor follow-up, plan review or provenance flows. Its provider-only `GroundedResponseFrame` contains only controlled `kind` and current `evidence_refs`. No prose, numeric, resource-name, duration or unrestricted qualifier field exists.

HealthNexus validates the entire frame before rendering any claim. Each kind requires an exact, compatible fact combination and semantic predicates. Duplicate kinds, unknown/stale IDs, incomplete or unrelated evidence, changed object identity/units and country/profile/geography/origin mismatches fail without repair. The deterministic renderer maps accepted frames into the existing public Claim shape. Existing exact numeric, evidence, WAPE, advisory action-state, solver and qualitative validators remain active. General/legacy intents retain their guarded text path.

Ordinary operational frames exclude execution/authorization/contact and solver-status kinds. Explicit status questions can cite authoritative false action state or exact mathematical solver status. Resource labels, units, decimal values and scenario duration come from selected authoritative facts. There is no model-specific answer branch. Handoffs carry the semantic contract and actual local scenario/plan handles, with no foreign provider interaction ID.

## Local gate

- **627 backend tests passed in 191.92 seconds**: all previous 587 cases retained, plus 40 semantic-frame/renderer/budget/handoff cases. Legacy production fixture assertions now distinguish provider frames from server wording; unsafe legacy text remains rejected.
- All four original execution phrases remain rejected in the legacy validation path. The prior unsupported paracetamol citation and uncited worded duration remain frozen regression evidence; provider frame schemas cannot contain those narrative fields.
- Common official SDK HTTP mocks passed A/B/C/D on both `gemini-3.5-flash-lite` and `gemini-3.6-flash`, using actual local operational engines. Each model had six mock HTTP sends and zero live provider requests.
- Python compilation and `pip check` passed. Canonical verification passed both profiles, all ten country/profile partitions and accepted federation reload; checksum `d971711083cef53d8b4416eebdf4c76b35d20b94ce62752a3bd4240e4cb42fc8` is unchanged.
- The isolated full suite passed after fixing semantic handoff. An earlier overlapping local run timed out in a federation test; federation code was not altered. The final local gate was rerun against the final implementation.
- Existing 2/2 live smoke evidence was preserved; it was not replayed.
- Frontend/UI files and prior build output remain unchanged. Prior strict TypeScript and Angular production build evidence is retained; no new frontend build or browser Gemini test was run.
- Preservation covers 454 current file identities plus 110 inherited ignored assets, including model/history/planning files and frontend output. Original numeric/context resolution and action/solver guards remain unchanged.

Local receipts: [preflight](evaluation/phase6-frame-preflight.json), [Flash-Lite SDK mocks](evaluation/phase6-frame-gemini-3.5-flash-lite-mock.json), [3.6 SDK mocks](evaluation/phase6-frame-gemini-3.6-flash-mock.json), [canonical/federation](evaluation/phase6-frame-canonical.json).

## Bounded live run

Current provider headroom was explicitly confirmed by the user: “Limits are available use.” No new usage figures or exact quota-reset timestamp were supplied or fabricated. Provider quota remains separate from the retained local ledger.

Only `gemini-3.5-flash-lite` was called. The configured production order remains 3.8 Flash → 3.7 Flash → 3.6 Flash → 3.5 Flash → 3.5 Flash-Lite. The verifier used an isolated six-send ceiling with one attempt per stage, no retry, fallback, replay or smoke.

**Actual new provider sends: 3/6. Ledger: 33 → 36. Flash-Lite historical count: 14 → 17.** Other model counts and the original ledger day `2026-09-28` were retained. The independent journal is terminal, so this authorization cannot be replayed.

| Send | Stage | HTTP/status | Thinking/output ceiling | Seconds | Input | Output | Thoughts | Total |
|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | native | 200 / requires_action | medium/2400 | 5.760849 | 1664 | 73 | 354 | 2091 |
| 2 | native | 200 / requires_action | medium/2400 | 4.697722 | 8824 | 125 | 59 | 9008 |
| 3 | synthesis | 200 / completed | low/4096 | 9.695901 | 18883 | 895 | 1241 | 21019 |

Provider total: 20.154471 seconds; 32118 reported tokens across three sends. Low thinking still consumed reported thought tokens. The two actual local native tools were `run_emergency_scenario` and `optimize_redistribution`.

| Case | Result |
|---|---|
| A: fresh positive native workflow | Scenario PASS; optimizer PASS; HTTP/complete JSON/provider frame schema PASS; whole semantic frame FAIL (`duplicate_kind`) |
| B: same-conversation follow-up | NOT ATTEMPTED after A failed |
| C: constrained explanation | NOT ATTEMPTED live; local canonical and SDK mock checks PASS |
| D: provenance/performance | NOT ATTEMPTED live; SDK mock checks PASS |

## Exact provider frame and rejection

The unchanged provider frame contains nine claims, including two `RESOURCE_PRESSURE` claims selecting different current resource rows. Each selected ID was known and each individual evidence combination matched its kind. The complete frame is nevertheless invalid because a kind may occur only once. Required positive semantics were also present; no missing claims were inserted or bad claims removed.

```json
{
  "claims": [
    {
      "kind": "SCENARIO_DURATION",
      "evidence_refs": [
        "e1_2bb1bc4525af4d03_f036"
      ]
    },
    {
      "kind": "RESOURCE_PRESSURE",
      "evidence_refs": [
        "e1_2bb1bc4525af4d03_f032",
        "e1_2bb1bc4525af4d03_f031",
        "e1_2bb1bc4525af4d03_f033",
        "e1_2bb1bc4525af4d03_f034"
      ]
    },
    {
      "kind": "RESOURCE_PRESSURE",
      "evidence_refs": [
        "e1_2bb1bc4525af4d03_f018",
        "e1_2bb1bc4525af4d03_f017",
        "e1_2bb1bc4525af4d03_f019",
        "e1_2bb1bc4525af4d03_f020"
      ]
    },
    {
      "kind": "NETWORK_PRESSURE",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f011"
      ]
    },
    {
      "kind": "ADVISORY_REDISTRIBUTION",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f005",
        "e2_2bb1bc4525af4d03_f015",
        "e2_2bb1bc4525af4d03_f014"
      ]
    },
    {
      "kind": "PARTIAL_RELIEF",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f005",
        "e2_2bb1bc4525af4d03_f011",
        "e2_2bb1bc4525af4d03_f009"
      ]
    },
    {
      "kind": "REMAINING_SHORTAGE",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f005",
        "e2_2bb1bc4525af4d03_f009",
        "e2_2bb1bc4525af4d03_f008"
      ]
    },
    {
      "kind": "DONOR_PROTECTION",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f005",
        "e2_2bb1bc4525af4d03_f019",
        "e2_2bb1bc4525af4d03_f018",
        "e2_2bb1bc4525af4d03_f012"
      ]
    },
    {
      "kind": "ELIGIBLE_CAPACITY",
      "evidence_refs": [
        "e2_2bb1bc4525af4d03_f005",
        "e2_2bb1bc4525af4d03_f016"
      ]
    }
  ]
}
```

Cost-free reconstruction from the saved actual ScenarioResult/PlanResult reproduced the exact supplied catalogue. Unknown fact IDs = 0; no provider free-text fields were present. This independent per-claim review does **not** upgrade the rejected frame into an accepted answer.

**Server-rendered live response: NOT ISSUED.** The renderer was not run after duplicate-kind rejection, and no public Copilot answer was returned. Post-render numeric/action/qualitative checks therefore did not run for this rejected live frame. Existing canonical engine checks did pass independently.

All raw provider frames, request schemas, native call arguments/results, IDs, authoritative engine objects, timings and token usage are retained in [the live trace](evaluation/phase6-frame-live.json). [The independent review](evaluation/phase6-frame-review.json) resolves selected IDs to exact values, labels, units, source tools and context; it confirms the duplicate-kind failure. The previous free-text failure remains in [the original live trace](evaluation/phase6-completion-live.json) and [preserved report](evaluation/phase6-completion-report-preserved.md).

## Canonical operational results

These are actual local engine results, not quantities generated by Gemini.

| Metric | Redistribution-ready (fresh live native tools) | Constrained (local reproduction) |
|---|---:|---:|
| Target before | 41763 | 30230 |
| Safe donor capacity | 17745 | 0 |
| Planned inventory-item accounting units | 15679 | 0 |
| Lanes | 10 | 0 |
| Unresolved target | 26084 | 30230 |
| Donor protection violations | 0 | 0 |
| New donor risks | 0 | 0 |
| Solver status | OPTIMAL | OPTIMAL |
| Resource conservation | PASS | PASS |

Fresh scenario ID: `227d6cda-f85d-4f56-9623-e7adf7f0a3d4`. Fresh optimization ID: `d804185d-0806-4679-b112-999b4ac3fe0f`. Donor reserve checks passed and baseline/scenario data remained immutable. The full actual plan, including quantities, routes, reserve and impact values, is audit-only evidence; expected canonical answers were not embedded in the user prompt.

## Renderer demonstration (mock evidence, not a live accepted answer)

For a valid common SDK mock frame, HealthNexus produced the following public prose. Gemini did not write these sentences:

- Current projections indicate resource pressure: 41763 inventory-item accounting units are needed to meet the selected network's target.
- The proposed advisory plan provides partial relief: target deficit would fall from 41763 to 26084 inventory-item accounting units.
- HealthNexus recommends an advisory redistribution plan of 15679 inventory-item accounting units across 10 transfer lanes.
- Recommended donor selections retain configured reserves. The cited donor retains a projected minimum of 1137.2347601697224 capsules against a protected reserve of 333 capsules; the plan has 0 donor protection violations.
- Eligible safe donor capacity for this advisory plan is 17745 inventory-item accounting units under the configured protection policy.
- Substantial shortages remain under the advisory plan: 26084 target inventory-item accounting units remain unresolved, with expected unmet demand of 17378.197997959564 accounting units.

## Security, preservation and verdict

The existing ignored `.env`, API key, project and production model order remain unchanged. Credentials were neither exposed nor rotated; billing was not enabled. Engines, forecasting, OR-Tools, donor policy, federation, UI and canonical artifacts were preserved. No deployment or later-phase work was started.

No successful six-send path exists for this run. There were no live B/C/D calls and no completion commit. The intended changes remain reviewable in the working tree.

**Phase 6 remains pending because: the positive live semantic frame repeated RESOURCE_PRESSURE, violating the duplicate-kind rule.**
