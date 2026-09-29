# Phase 6 final acceptance - 29 September 2026

**Phase 6 fully live-accepted.**

The four-case live acceptance passed on `gemini-3.5-flash-lite` with exactly six actual provider sends. Final post-live regressions pass. This closes Phase 6; no deployment or later phase was started. Continues the intentionally modified `a62f098` working tree without reset, checkout, stash or repository recreation. All intended Phase 6 changes are included in the completion commit reported in the final handoff.

## The fix

**PROVIDER OUTPUT = semantic frame / selected evidence. SERVER OUTPUT = deterministically rendered user-facing prose.**

Operational and provenance answers now use `grounded-semantic-slots-v2`: a strict named claims object, with current `evidence_refs` as its only values. Gemini performs native orchestration and selects authoritative evidence; it does not author operational sentences, numbers, resource names, durations or qualifiers. Unique named slots prevent duplicate claim kinds structurally. Duplicate JSON keys are rejected rather than silently normalized. The compact positive schema exposes four required operational slots, without optional per-resource/duration claims. Explicit detail/status questions retain their bounded, evidence-backed semantics.

The complete frame is checked before rendering. Unknown/stale fact IDs, duplicate IDs, missing/incompatible evidence, predicates, source/value/unit/object identity drift and country/profile/geography/origin mismatch reject without repair. Missing claims are never inserted. Deterministic decoding uses a fixed semantic order so the donor follow-up retains its remaining-gap section regardless of JSON property order. The public Claim response shape is unchanged. Original exact numeric, source, WAPE, action-state, solver and qualitative guards remain active. General intents retain their guarded legacy text path; offline mode remains explicit.

Safe provider handoff keeps authoritative local scenario/plan handles and evidence while starting a fresh provider interaction without a foreign model interaction ID. All models share the same tools, validation and renderer. There are no model-specific stored answers or hardcoded donor routes/quantities.

## Verification

- Pre-live: **636 backend tests**, zero failures/errors/skips, 139.951 seconds. All previous 627 cases retained, plus nine slot-schema/order/budget regressions.
- Post-live: **636 backend tests**, zero failures/errors/skips, 144.215 seconds. Python compilation, `pip check`, strict TypeScript `--noEmit` and `git diff --check` pass.
- Shared official SDK HTTP mocks pass A/B/C/D on Flash-Lite and 3.6 Flash: six mock sends per model, zero live requests. Native function-call validity is checked against the actual typed registry and engines.
- Both canonical plans, all ten country/profile partitions and the accepted saved federation reload/evaluation pass before and after live acceptance. No retraining or operational data regeneration occurred.
- Preservation checks cover 466 starting file identities plus 110 inherited ignored assets. Existing numeric/context resolution and action/solver guards remain unchanged. Prior failed live traces and reports are frozen.
- Frontend/UI sources and original production bundles are unchanged. Strict TypeScript was rerun successfully; the earlier Angular production build and browser evidence remain preserved. No new Angular build or browser Gemini request is claimed.
- Two captured full-suite processes exited without a pytest result; the isolated SDK budget case passed. Complete pre/post suites with capture disabled passed. No tests were skipped and no production guard was weakened to bypass this runner issue.

Receipts: [preflight](evaluation/phase6-slots-preflight.json), [Lite SDK mocks](evaluation/phase6-slots-gemini-3.5-flash-lite-mock.json), [3.6 SDK mocks](evaluation/phase6-slots-gemini-3.6-flash-mock.json), [post-live canonical/federation](evaluation/phase6-slots-post-canonical.json), [final gate](evaluation/phase6-slots-final.json).

## Live requests

The user confirmed current provider headroom: "Limits are available use." No exact usage figures or reset timestamp were supplied or invented. This was a new independent six-send run after preserving the failed three-send frame run. Only Flash-Lite was authorized for this acceptance; no retries, cross-model failover, replay or seventh request occurred. After case D passed, zero further live calls were made.

| Case / stage | Actual model | HTTP / status | Provider seconds | Input tokens | Output tokens | Thought tokens | Total tokens |
|---|---|---|---:|---:|---:|---:|---:|
| positive / native | gemini-3.5-flash-lite | 200 / requires_action | 4.604549 | 1664 | 73 | 258 | 1995 |
| positive / native | gemini-3.5-flash-lite | 200 / requires_action | 4.862247 | 8924 | 126 | 77 | 9127 |
| positive / synthesis | gemini-3.5-flash-lite | 200 / completed | 6.592479 | 18655 | 389 | 696 | 19740 |
| followup / synthesis | gemini-3.5-flash-lite | 200 / completed | 5.585431 | 22780 | 337 | 0 | 23117 |
| constrained / synthesis | gemini-3.5-flash-lite | 200 / completed | 4.221467 | 3705 | 288 | 0 | 3993 |
| provenance / synthesis | gemini-3.5-flash-lite | 200 / completed | 5.331479 | 7810 | 560 | 0 | 8370 |

Provider latency sum: **31.197652 seconds**; provider-reported total tokens: **66342**. Latencies exclude the 20-second request pacer and local review pauses. Native thinking remained medium/2,400; final slots used low/4,096. Low thinking can still consume thought tokens, as the table shows.

Four validated schema outputs, two valid native calls and six successful provider interactions; zero failed attempts, unknown fact IDs, unsupported numeric claims or unsupported execution claims. These quality checks apply to bounded claims, not unrestricted medical truth assessment.

Local tool calls are counted separately: six audited Copilot tool calls (A: scenario + optimizer; B: fresh plan read; C: fresh constrained plan read; D: provenance + performance), plus two deterministic local constrained setup calls. None of those local calls consumes Gemini quota.

Historical ledger preserved: **36 + 6 = 42**. Lite **17 + 6 = 23**; legacy-unattributed 7 and other models remain 3 each. Original ledger day `2026-09-28` remains unchanged; this accounting is not Google quota and was not reset. The independent send journal is terminal and blocks replay.

Production fallback order remains **3.8 Flash -> 3.7 Flash -> 3.6 Flash -> 3.5 Flash -> 3.5 Flash-Lite**. Availability failures alone may trigger fallback; authentication, schema/evidence/tool/scope/clinical/application failures remain visible. Effective model stickiness and safe local handoff remain intact. All five candidates retain deterministic protocol coverage; the shared final workflow mock transports here cover Lite/3.6, and this final live acceptance covers Lite only. Do not describe these answers as live 3.8 answers.

## Canonical operational results

India / Maharashtra / Pune, severe dengue, 14 days, seed 42. Values below come from actual local HealthNexus objects, not expected answers inserted into a provider prompt. Aggregate quantities are inventory-item accounting sums across heterogeneous resources, not interchangeable physical units.

| Profile | Target before | Safe donor capacity | Planned quantity | Lanes | Unresolved after | Donor violations | New donor risks | Solver |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| redistribution-ready | 41763 | 17745 | 15679 | 10 | 26084 | 0 | 0 | OPTIMAL |
| constrained | 30230 | 0 | 0 | 0 | 30230 | 0 | 0 | OPTIMAL |

Positive expected unmet demand: **27655.218070826377 -> 17378.197997959564**. Critical resource warnings: **7 -> 0**. Facilities at risk remain **1**, and maximum stock-out risk remains **1.0**. Relief is partial; no claim that all shortages or risks are eliminated.

Every donor retains its configured protected reserve over the checked paths. Per-resource conservation passes. Plans remain advisory: physical execution=false, external authorization=false, hospital contacted=false, transfer status=not_executed. Baseline snapshots and scenario identities remain immutable.

Actual positive lanes (engine distance values):

| Donor | Receiver | Resource | Quantity | Unit | Distance km | Protected reserve | Protected minimum after |
|---|---|---|---:|---|---:|---:|---:|
| Pune · PHC 01 | Pune · District Hospital 03 | AMX | 798 | capsules | 6.440558977049242 | 333 | 1137.2347601697224 |
| Pune · PHC 01 | Pune · District Hospital 03 | IFA | 610 | tablets | 6.440558977049242 | 428 | 1690.9198681792977 |
| Pune · PHC 01 | Pune · District Hospital 03 | IVF | 463 | bags | 6.440558977049242 | 152 | 152.5452527196078 |
| Pune · PHC 01 | Pune · District Hospital 03 | ORS | 1135 | sachets | 6.440558977049242 | 271 | 271.68694840161334 |
| Pune · PHC 01 | Pune · District Hospital 03 | PCM | 1600 | tablets | 6.440558977049242 | 1100 | 1100.815405792277 |
| Pune · CHC 02 | Pune · District Hospital 03 | AMX | 2478 | capsules | 4.477808726193947 | 558 | 558.5507564132913 |
| Pune · CHC 02 | Pune · District Hospital 03 | IFA | 2880 | tablets | 4.477808726193947 | 722 | 722.520048669237 |
| Pune · CHC 02 | Pune · District Hospital 03 | IVF | 620 | bags | 4.477808726193947 | 257 | 257.09384385829526 |
| Pune · CHC 02 | Pune · District Hospital 03 | ORS | 1556 | sachets | 4.477808726193947 | 454 | 454.87348819061594 |
| Pune · CHC 02 | Pune · District Hospital 03 | PCM | 3539 | tablets | 4.477808726193947 | 1846 | 1846.5090704858321 |

Measured OR-Tools/greedy comparison from the same actual plan:

| Metric | OR-Tools | Greedy |
|---|---:|---:|
| Transferred accounting items | 15679 | 15679 |
| Lanes | 10 | 10 |
| Lane distance km | 54.591838516215944 | 54.591838516215944 |
| Distance x units | 79247.99067343438 | 79247.99067343438 |
| Donor violations | 0 | 0 |
| New donor risks | 0 | 0 |
| Unresolved target | 26084 | 26084 |
| Expected unmet demand | 17378.197997959564 | 17378.197997959564 |
| Critical resource warnings | 0 | 0 |

## Actual provider frames and server rendering

[The complete live trace](evaluation/phase6-slots-live.json) preserves unchanged raw provider strings, submitted schemas, current request-local catalogues, native arguments/results, interaction continuity, usage, full authoritative engine objects, resolved evidence and separate server-rendered responses. The prose below is authored by the HealthNexus renderer, not Gemini.

### positive - PASS

Question: Simulate a severe 14-day dengue surge in Pune, identify the most serious resource risks, and find the safest redistribution plan. Profile: `redistribution-ready`.

Raw provider frame:

```json
{
  "claims": {
    "NETWORK_PRESSURE": {
      "evidence_refs": [
        "e2_818c70b90c0b4f65_f011"
      ]
    },
    "ADVISORY_REDISTRIBUTION": {
      "evidence_refs": [
        "e2_818c70b90c0b4f65_f005",
        "e2_818c70b90c0b4f65_f015",
        "e2_818c70b90c0b4f65_f014"
      ]
    },
    "PARTIAL_RELIEF": {
      "evidence_refs": [
        "e2_818c70b90c0b4f65_f005",
        "e2_818c70b90c0b4f65_f011",
        "e2_818c70b90c0b4f65_f009"
      ]
    },
    "REMAINING_SHORTAGE": {
      "evidence_refs": [
        "e2_818c70b90c0b4f65_f005",
        "e2_818c70b90c0b4f65_f009",
        "e2_818c70b90c0b4f65_f008"
      ]
    }
  }
}
```

Server-rendered response:

- **situation:** Current projections indicate resource pressure: 41763 inventory-item accounting units are needed to meet the selected network's target. Sources: `e2/impact.before.target_deficit`.
- **key_risks:** The proposed advisory plan provides partial relief: target deficit would fall from 41763 to 26084 inventory-item accounting units. Sources: `e2/action_state.plan_mode, e2/impact.before.target_deficit, e2/impact.after.target_deficit`.
- **recommended_actions:** HealthNexus recommends an advisory redistribution plan of 15679 inventory-item accounting units across 10 transfer lanes. Sources: `e2/action_state.plan_mode, e2/impact.transferred_units, e2/impact.transfer_count`.
- **remaining_gaps:** Substantial shortages remain under the advisory plan: 26084 target inventory-item accounting units remain unresolved, with expected unmet demand of 17378.197997959564 accounting units. Sources: `e2/action_state.plan_mode, e2/impact.after.target_deficit, e2/impact.after.expected_unmet`.

Resolved source values:

| Evidence / field | Tool | Exact value | Unit |
|---|---|---|---|
| e2/impact.before.target_deficit | optimize_redistribution | 41763 | accounting items |
| e2/action_state.plan_mode | optimize_redistribution | "advisory" |  |
| e2/impact.after.target_deficit | optimize_redistribution | 26084 | accounting items |
| e2/impact.transferred_units | optimize_redistribution | 15679 | accounting items |
| e2/impact.transfer_count | optimize_redistribution | 10 |  |
| e2/impact.after.expected_unmet | optimize_redistribution | 17378.197997959564 |  |

### followup - PASS

Question: Why were these donors selected, and what shortages remain? Profile: `redistribution-ready`.

Raw provider frame:

```json
{
  "claims": {
    "REMAINING_SHORTAGE": {
      "evidence_refs": [
        "e1_b673f88034a34870_f005",
        "e1_b673f88034a34870_f009",
        "e1_b673f88034a34870_f008"
      ]
    },
    "DONOR_PROTECTION": {
      "evidence_refs": [
        "e1_b673f88034a34870_f005",
        "e1_b673f88034a34870_f019",
        "e1_b673f88034a34870_f018",
        "e1_b673f88034a34870_f012"
      ]
    },
    "ELIGIBLE_CAPACITY": {
      "evidence_refs": [
        "e1_b673f88034a34870_f005",
        "e1_b673f88034a34870_f016"
      ]
    }
  }
}
```

Server-rendered response:

- **situation:** Recommended donor selections retain configured reserves. The cited donor retains a projected minimum of 1137.2347601697224 capsules against a protected reserve of 333 capsules; the plan has 0 donor protection violations. Sources: `e1/action_state.plan_mode, e1/transfers.0.donor_protected_reserve, e1/transfers.0.donor_protected_minimum_after, e1/impact.donor_safety_violations`.
- **recommended_actions:** Eligible safe donor capacity for this advisory plan is 17745 inventory-item accounting units under the configured protection policy. Sources: `e1/action_state.plan_mode, e1/safe_capacity`.
- **remaining_gaps:** Substantial shortages remain under the advisory plan: 26084 target inventory-item accounting units remain unresolved, with expected unmet demand of 17378.197997959564 accounting units. Sources: `e1/action_state.plan_mode, e1/impact.after.target_deficit, e1/impact.after.expected_unmet`.

Resolved source values:

| Evidence / field | Tool | Exact value | Unit |
|---|---|---|---|
| e1/action_state.plan_mode | get_optimization_result | "advisory" |  |
| e1/transfers.0.donor_protected_reserve | get_optimization_result | 333 | capsules |
| e1/transfers.0.donor_protected_minimum_after | get_optimization_result | 1137.2347601697224 | capsules |
| e1/impact.donor_safety_violations | get_optimization_result | 0 |  |
| e1/safe_capacity | get_optimization_result | 17745 | accounting items |
| e1/impact.after.target_deficit | get_optimization_result | 26084 | accounting items |
| e1/impact.after.expected_unmet | get_optimization_result | 17378.197997959564 |  |

### constrained - PASS

Question: Explain why HealthNexus recommends no redistribution in this scenario. Profile: `constrained`.

Raw provider frame:

```json
{
  "claims": {
    "REMAINING_SHORTAGE": {
      "evidence_refs": [
        "e1_843e387a18e4499d_f005",
        "e1_843e387a18e4499d_f009",
        "e1_843e387a18e4499d_f008"
      ]
    },
    "NO_SAFE_DONOR_CAPACITY": {
      "evidence_refs": [
        "e1_843e387a18e4499d_f016"
      ]
    },
    "NO_RECOMMENDED_REDISTRIBUTION": {
      "evidence_refs": [
        "e1_843e387a18e4499d_f005",
        "e1_843e387a18e4499d_f015",
        "e1_843e387a18e4499d_f014"
      ]
    }
  }
}
```

Server-rendered response:

- **situation:** Configured reserve constraints leave 0 safe donor inventory-item accounting units in this network. Sources: `e1/safe_capacity`.
- **recommended_actions:** HealthNexus recommends no redistribution: the advisory plan contains 0 planned inventory-item accounting units and 0 transfer lanes. Sources: `e1/action_state.plan_mode, e1/impact.transferred_units, e1/impact.transfer_count`.
- **remaining_gaps:** Substantial shortages remain under the advisory plan: 30230 target inventory-item accounting units remain unresolved, with expected unmet demand of 17075.155797617244 accounting units. Sources: `e1/action_state.plan_mode, e1/impact.after.target_deficit, e1/impact.after.expected_unmet`.

Resolved source values:

| Evidence / field | Tool | Exact value | Unit |
|---|---|---|---|
| e1/safe_capacity | get_optimization_result | 0 | accounting items |
| e1/action_state.plan_mode | get_optimization_result | "advisory" |  |
| e1/impact.transferred_units | get_optimization_result | 0 | accounting items |
| e1/impact.transfer_count | get_optimization_result | 0 |  |
| e1/impact.after.target_deficit | get_optimization_result | 30230 | accounting items |
| e1/impact.after.expected_unmet | get_optimization_result | 17075.155797617244 |  |

### provenance - PASS

Question: Is this live government inventory, and how should I interpret the forecast performance? Profile: `redistribution-ready`.

Raw provider frame:

```json
{
  "claims": {
    "PUBLIC_AGGREGATE_INPUT": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f009"
      ]
    },
    "SIMULATED_FACILITY_OPERATIONS": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f005",
        "e1_b8b8d1a4673e4adc_f001"
      ]
    },
    "MODEL_BASED_FORECAST": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f007"
      ]
    },
    "SCENARIO_PROJECTION": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f010"
      ]
    },
    "ADVISORY_OPTIMIZATION": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f008"
      ]
    },
    "WAPE_ERROR_METRIC": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f011",
        "e2_b8b8d1a4673e4adc_f003"
      ]
    },
    "NOT_CLINICALLY_VALIDATED": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f007"
      ]
    },
    "NO_LIVE_GOVERNMENT_CONNECTION": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f002",
        "e1_b8b8d1a4673e4adc_f004"
      ]
    },
    "EXPERIMENTAL_FEDERATION": {
      "evidence_refs": [
        "e1_b8b8d1a4673e4adc_f006"
      ]
    }
  }
}
```

Server-rendered response:

- **situation:** Official public aggregate source inputs inform HealthNexus calibration. Sources: `e1/interpretation.public_inputs`.
- **key_risks:** Facility operations and inventory are fictional calibrated simulated data. Sources: `e1/interpretation.facility_operations, e1/data_type`.
- **key_risks:** Forecasts are derived model-based outputs using simulated operational histories. Sources: `e1/interpretation.forecast`.
- **key_risks:** Scenarios are simulated stress-test projections, specified externally. Sources: `e1/interpretation.scenario`.
- **key_risks:** The cited forecast test WAPE is 0.030798650603591108. WAPE is an error metric, not accuracy; lower error is better. Sources: `e1/interpretation.wape, e2/targets.medicine.models.hist_gradient_boosting.test.wape`.
- **recommended_actions:** Optimization outputs are advisory recommendations for resource planning. Sources: `e1/interpretation.optimization`.
- **remaining_gaps:** These forecasts are not clinically validated. Sources: `e1/interpretation.forecast`.
- **remaining_gaps:** Inventory is not live government inventory; no real government systems or hospitals are connected. Sources: `e1/live_government_inventory, e1/interpretation.connections`.
- **remaining_gaps:** Federated-learning metrics remain experimental. Sources: `e1/interpretation.federation`.

Resolved source values:

| Evidence / field | Tool | Exact value | Unit |
|---|---|---|---|
| e1/interpretation.public_inputs | get_data_provenance | "official public aggregate source inputs" |  |
| e1/interpretation.facility_operations | get_data_provenance | "fictional calibrated simulated facility operations" |  |
| e1/data_type | get_data_provenance | "calibrated simulated operations" |  |
| e1/interpretation.forecast | get_data_provenance | "derived model-based output; not clinically validated" |  |
| e1/interpretation.scenario | get_data_provenance | "externally specified simulated stress-test projection" |  |
| e1/interpretation.wape | get_data_provenance | "forecast error metric, not accuracy" | WAPE fraction |
| e2/targets.medicine.models.hist_gradient_boosting.test.wape | get_model_performance | 0.030798650603591108 | WAPE fraction |
| e1/interpretation.optimization | get_data_provenance | "advisory optimization recommendation" |  |
| e1/live_government_inventory | get_data_provenance | false |  |
| e1/interpretation.connections | get_data_provenance | "no government systems or hospitals connected" |  |
| e1/interpretation.federation | get_data_provenance | "experimental federated-learning metrics" |  |

## Preservation and security

`.env` and the API key were neither changed nor exposed. Same key/project; billing unchanged; no new project or account. Credential-pattern scan passes, `.env` remains ignored/untracked and original frontend bundles contain no provider credential. This is a source/bundle credential check, not penetration testing. Model artifacts, forecasts, profiles, OR-Tools/scenario/warning engines, UI, caches and federation assets retain original identities.

Previous failed traces remain available: [free-prose failure](evaluation/phase6-completion-live.json), [preserved free-prose report](evaluation/phase6-completion-report-preserved.md), [duplicate-kind failure](evaluation/phase6-frame-live.json), [preserved frame report](evaluation/phase6-frame-report-preserved.md). Their failures are historical and are not reclassified as successful.

## Verdict

**Phase 6 fully live-accepted.** Positive native orchestration, same-conversation donor follow-up, honest constrained zero-donor reporting and provenance/performance explanation all pass. The deterministic operational tools remain authoritative and available during provider outages. Provider availability and Free Tier quota still vary; no remaining quota or reset time is fabricated. No deployment, cross-district work, maps, deck, video or later phase was started.
