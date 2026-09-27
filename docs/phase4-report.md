# Phase 4 — Early Warning Engine and Emergency Digital Twin

Implemented on the existing Angular/FastAPI repository without replacing Phase 1–3. India retains all 36 states/UTs and its 207 fictional facilities; the four representative BRICS nodes remain independent country scopes. No baseline history, generated snapshot, fitted model or evaluation report is modified by a scenario.

## Architecture and files

- `backend/app/scenarios/models.py`, `schemas.py`: validated requests, projections, operational days, receipt changes, comparisons, metadata and presets.
- `scenarios/engine.py`: scope validation, copies of selected facilities, saved forecast reuse, paired projections, warning evaluation and orchestration.
- `scenarios/effects.py`: pure demand adjustments, receipt shifts, inventory, admissions/discharges, workforce and service-capacity propagation.
- `scenarios/comparison.py`: backend-owned totals, resource-specific comparisons, deltas and facility ranking.
- `scenarios/state.py`: locked, bounded process-local store. Twenty completed scenarios maximum; explicit discard, no silent eviction. Restarting the server clears runs. This is a single-worker local prototype, not durable multi-user storage.
- `scenarios/routes.py`: typed scenario and warning endpoints; mutation logic lives outside handlers.
- `backend/app/warnings/models.py`, `engine.py`: controlled identifiers, factual explanation factors, warning rules, stable identities, priority, transitions and geographic aggregation.
- `backend/app/core/risk_config.py`: versioned assumptions and thresholds (`resilience-v1`).
- `backend/app/main.py`: registers services sharing a Phase 3 `ForecastService`; permits GET/POST/DELETE in existing CORS scope; API version 0.4.0.
- `backend/tests/test_scenarios.py`: 32 additional tests/parameter cases.
- `frontend/src/app/core/resilience-models.ts`, `network-api.ts`: typed contracts and requests.
- `pages/emergency.ts`, `emergency.html`: scenario form, before/after KPIs, resource impacts, facility ranking, demand/inventory charts, operational timeline, assumptions and discard.
- `pages/warnings.ts`, `shared/warning-cards.ts`: Early Warning Centre, scenario/baseline selection, severity/category/geography filters, factual expandable details. Large lists initially show 50 cards and can expand; summary counts always cover all matching warnings.
- `shared/scenario-chart.ts`, `frontend/src/resilience.scss`: responsive baseline/scenario charts and conditional bands; accessible labels and daily tables.
- Navigation, routes and About page retain prior features and add the new screens. The original `/api/alerts` and `/alerts` remain available.
- `scripts/smoke_phase4.py`: reproducible live HTTP checks, with its own scenarios discarded after verification.

## Supported scenarios and numeric assumptions

All runs project the next **14 days** from the saved model origin. Duration is 1–14 days. Optional start date defaults to origin + 1 day; the entire event window must fit in those 14 days. Effects end at the event boundary, while depleted inventories and occupancy changes can persist. Geography and explicit facility IDs are validated within one country.

| Scenario | Moderate | Severe | Critical | Effect |
|---|---:|---:|---:|---|
| Dengue surge | 20% | 50% | 90% | Additional fever visits as a fraction of each day's baseline footfall |
| Delivery delay | 3 days | 7 days | 14 days | Shift selected medicine receipts due inside the event window |
| Staff shortage | 20% | 40% | 65% | Fraction of normally present staff unavailable |
| Facility disruption | 25% | 50% | 100% | Reduction of usable beds and service capability |

Delivery delay permits an explicit 1–30-day override and one medicine (IVF default). Staff/capacity fractions permit overrides above zero through 100%. Explicit overrides take precedence over preset values and are recorded in effective parameters. Unknown fields and parameters for the wrong scenario type are rejected.

### Dengue causal chain

1. Read each facility's saved footfall, admission and medicine forecasts. Freeze its recent seven-day syndrome shares.
2. Additional fever visits = baseline daily footfall × selected shock fraction inside the event window. Other syndrome counts stay unchanged. Total visits and fever share therefore rise.
3. Add requests using the **existing operational syndrome/resource mapping**: 3.5 paracetamol tablets, 0.3 IV-fluid bags and 0.1 ORS sachets per extra fever visit. Amoxicillin and iron/folic-acid demand receive no fever increment. These are fictional resource-planning coefficients, not treatment guidance. The small ORS increment inherits the simulator's fever mapping; it does not claim a validated dengue treatment requirement.
4. Add 0.10 requested admissions per extra fever visit, an explicit unvalidated operational assumption.
5. Propagate inventory against known receipts and requested demand; retain unmet demand. Recompute stock reserve crossings, depletion and 500-path stock-out probabilities.
6. Propagate admissions/discharges and workload, then evaluate common warning rules.

This is an externally specified demand shock. There is no transmission model, R0 estimate, infection spread, clinical progression, diagnosis or machine-learned dengue forecast.

### Capacity and conservation

Baseline usable beds = total minus reserved beds. The discharge fraction is recent total discharges divided by recent previous occupied beds, bounded at one (0.20 fallback when unavailable). Each day:

```
discharges = opening_occupied × frozen discharge fraction
admissions = min(requested_admissions, max(0, usable_beds - opening_occupied + discharges))
occupied = opening_occupied + admissions - discharges
unmet_admissions = requested_admissions - admissions
existing_overflow = max(0, occupied - usable_beds)
```

Existing patients are not silently removed by a flood. Occupancy above reduced capacity is explicit overflow, and zero capacity produces a null occupancy ratio rather than infinity. Fractional values are expected operational quantities, not identifiable patients or exact staffed-bed rosters. No spillover/referrals are implemented; same-district movement requires additional assumptions and remains deferred.

Normal service capacity = trailing seven-day mean footfall × 1.25 headroom. Divide by normally present personnel to get visits per staff equivalent. Scale by scenario availability and disruption capacity. Workload = requested visits / service capacity; no capacity gives a null ratio and a critical workload warning. Scheduled staff remains unchanged, available staff never exceeds scheduled, and availability recovers after the event. No role-specific shortage modelling or treatment efficacy effects are inferred. Staff shortage changes outpatient service capacity; it does not independently invent staff-to-bed clinical ratios.

Medicine requests remain demand-side needs even when visits cannot be served. Unserved visits are a pressure indicator, not a queue. Stock fulfillment remains supply constrained:

```
fulfilled = min(requested, opening + receipts)
closing = opening + receipts - fulfilled
unmet = requested - fulfilled
```

No transfers, future unplaced orders or backlog recovery are assumed. Delay scenarios shift only orders placed by origin whose expected arrival is after origin and inside the event window. Historical receipts and unknown future orders are excluded. Shifted arrivals beyond day 14 remain visible in receipt changes but do not enter the projected stock window. A delay may change stock trajectories without causing a stock-out; the engine does not force a red outcome.

## Exactly how Phase 3 is reused

- **Direct forecast:** saved country-local champions predict baseline footfall, requested medicines and requested admissions. Champions may be HGB or a selected baseline. Model weights and calibration residuals are reused; there is no fitting on a scenario request.
- **Scenario adjustment:** add the specified daily fever/resource/admission increments to baseline trajectories. This layer is deterministic and explicitly labelled Scenario Projection. Future shock covariates are not passed into a model that was never trained on outbreaks.
- **Operational propagation:** compute beds, discharge flows, workforce capacity and inventory from those requests and existing operational state.
- **Monte Carlo estimate:** reuse Phase 3 `demand_paths` and `project_stock` with 500 whole 14-day residual vectors. Baseline and scenario share the same sampled residual paths. Seed 42 exactly reproduces Phase 3 baseline stock trajectories; other seeds deterministically resample the same calibration pool for both comparison arms. Scenario increments translate demand paths and daily bands; shock magnitude and receipt timing uncertainty are not estimated.
- **Warning rule:** deterministic, centrally configured thresholds consume these forecasts, conditional risks and propagated state.

Responses preserve model versions and selected target model names, historical forecast provenance, source/calibration metadata, simulation seed, event window, effective effects, config version, creation time and a SHA-256 of the selected baseline facilities plus country/origin. The hash identifies the selected baseline scope, not the whole world network. Warning generation time is distinct from forecast origin. Cached baseline reads retain stable warning objects. Phase 3's empirical coverage is **not** a claim of calibrated emergency coverage.

## Warning rules

| Identifier | Trigger and severity |
|---|---|
| LOW_STOCK | Demand-based cover below 7 days: WARNING; below 3: CRITICAL |
| SAFETY_STOCK_BREACH | Point stock reaches reserve within 14 days: WATCH; within 7 days or already breached: WARNING |
| PREDICTED_STOCKOUT | Point depletion within 14 days: WARNING; within 3 days or already empty: CRITICAL |
| HIGH_STOCKOUT_RISK | 14-day risk ≥20%: WATCH; 7-day risk ≥50%: WARNING; 3-day risk ≥80%: CRITICAL |
| DELIVERY_DELAY | At least one eligible receipt shifted: INFO; projected reserve breach: WARNING |
| PATIENT_SURGE | 14-day mean vs observed 7-day mean growth ≥15% WATCH, ≥35% WARNING, ≥70% CRITICAL. Event date is first rolling 7-day mean crossing 15%; regular single-day weekday peaks do not establish the date |
| ABNORMAL_FOOTFALL | Latest observation exceeds previous 27-day mean + 3 standard deviations: WATCH; descriptive, not a disease signal |
| HIGH_BED_OCCUPANCY | Peak occupied/usable beds ≥85% WATCH; ≥95% WARNING |
| PREDICTED_BED_CAPACITY_BREACH | Unmet requested admissions or explicit existing overflow: WARNING; first failure within 3 days: CRITICAL |
| STAFF_SHORTAGE | Available/scheduled below 85% WATCH, below 70% WARNING, below 50% CRITICAL |
| HIGH_WORKLOAD | Demand/service capacity above 1 WARNING; ≥1.4 or zero service capacity CRITICAL |
| FACILITY_DISRUPTION | Specified reduction: WARNING; zero service capacity: CRITICAL |
| EMERGENCY_ESCALATION | Scenario has critical warnings in at least two distinct operational domains: CRITICAL |

These thresholds are prototype policy assumptions, not clinical standards. The baseline can already contain risks; those are retained. Each warning has type/category, severity, country/region/district/facility, optional resource, origin, generation time, horizon, current/threshold/projected values, event date, applicable probability, factors, provenance, model version and a review-only next-step placeholder.

Identity = first 24 hex characters of SHA-256(country, facility, type, resource, scenario-or-baseline, origin). Repeated reads never append duplicates. Separate warning types remain separate because they describe distinct thresholds. Scenario warnings compare against the same facility/resource/type baseline warning and label **new**, **unchanged**, **worsened** or **improved** severity. This is a paired baseline comparison, not a persistent acknowledgement/escalation history across successive real-world origins.

Priority is deterministic:

```
100 × severity_rank
+ 20 × (1 - min(14, days_until_event)/14)
+ 20 × applicable_stockout_probability
+ 10 × min(1, projected_14_day_visits/10000)
+ 5 × is_hospital
```

Ranks are INFO=0, WATCH=1, WARNING=2, CRITICAL=3. Unknown event dates use 14 days. Past/already-occurring events use zero. Hospital is the existing facility-type label containing `Hospital`. This is not an AI score. Severity dominates the bounded tie-break components. Summaries count actual matching active objects at country, region, district and facility levels.

## Measured Pune example

Origin **2026-09-27**, severe dengue, 14 days, seed 42, all three fictional Pune facilities. Values below are computed, not hardcoded UI examples.

| Metric | Baseline | Scenario |
|---|---:|---:|
| Requested patient visits | 14,015.40 | 21,023.10 |
| Requested admissions | 796.10 | 1,496.87 |
| Unmet admissions | 21.62 | 615.96 |
| IV-fluid demand, bags | 2,748.58 | 4,850.89 |
| Paracetamol demand, tablets | 19,827.32 | 44,354.27 |
| Peak workload ratio | 0.9813 | 1.4719 |
| Maximum facility/resource 14-day stock-out estimate | 0% | 100% |
| Critical facilities | 2 | 3 |

Resource increases are approximately IV fluids **76.49%**, paracetamol **123.70%**, ORS **14.33%**, amoxicillin/IFA **0%**. Exact unrounded resource values are in `docs/evaluation/phase4-smoke.json`; this table rounds expected quantities. The 100% estimate means all 500 sampled paths depleted under these fixed assumptions, not a real-world certainty.

The district's maximum bed occupancy is already 100% at baseline and stays capped at 100% under dengue; pressure is visible through additional unmet admissions. The district hospital's first projected day rises from approximately 207.8 to 238 occupied beds. Scenario warnings: **9 CRITICAL, 18 WARNING, 19 WATCH**. Existing baseline warnings are included with transitions.

A 14-day IV-fluid receipt delay changes maximum 14-day risk from 0% to 100% and leaves patient demand unchanged. A severe staff shortage leaves scheduled staff unchanged and increases peak workload by 66.67%. A severe disruption halves usable capacity and increases unmet admissions; existing overflow can put occupancy above 100% of reduced capacity. None of these changes affect baseline endpoints.

## Demo and run commands

Existing saved model artifacts are sufficient; Phase 4 needs no new training.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm start
```

1. Open `http://127.0.0.1:4200/overview`, select India → Maharashtra → Pune. Show current operations.
2. Open Forecasts and inspect normal footfall or IV-fluid demand.
3. Open Emergency Simulator. **Load Pune demo** sets India/Maharashtra/Pune and the severe 14-day dengue preset.
4. Confirm Dengue surge → Severe → 14 days → All facilities in scope. Click **Run Simulation** (keyboard activation also supported).
5. Compare KPIs and resource impacts. Select the district hospital, then **IV fluids** to see baseline versus scenario depletion and 3/7/14-day risks. Inspect the operational timeline for beds and staffing pressure.
6. Open **scenario warnings**, filter severity/category, expand a warning to inspect facts and model provenance. Use **Compare scenario** to return.
7. Click **Discard / reset scenario**. The result disappears; baseline network and forecasts remain unchanged. Reset does not regenerate data.
8. Run Medicine delivery delay with Critical (14-day delay), Staff shortage with Severe (40% unavailable), and Facility/flood disruption with Severe (50% capacity reduction). Inspect changed receipts, attendance and explicit overflow respectively.

For fresh installations, follow README dependency/data/model setup. API rejects missing/stale bundles with an explicit unavailable response rather than fitting or inventing forecasts.

## Verification and limits

- **105 backend tests pass:** all original 73 plus 32 Phase 4 cases. Repeatability, non-mutation, geography, severity/duration, validation, stock/bed/staff conservation, medicine mapping, receipt shifts, ignored historical/future-unknown orders, zero capacity, recovery, warning metadata/thresholds/identity/priority/aggregation, delayed surge event timing, independent cache copies, country-scoped store/discard and typed API lifecycle are covered.
- Python compilation passes. Actual saved artifact loading and inference exercised for all five countries by live smoke tests.
- Angular strict TypeScript and production build pass. Initial production bundle **357.22 kB raw / 98.40 kB estimated transfer**.
- Live HTTP: all four scenarios across five countries (20 runs), comparisons, warning list/detail/summary, filter validation, cross-country 404, discard 404 and unchanged baseline records/forecasts. Saved results: `docs/evaluation/phase4-smoke.json`.
- Scenario HTTP timings in the recorded run were approximately 0.08–1.32 seconds with bundles already loaded; initial library/model loading may add latency. First national India warning evaluation took 19.88 seconds. A subsequent cached summary read measured about 1.72 seconds. The UI shows loading explicitly; national cold evaluation is slower than district demos.
- Keyboard-driven desktop browser checks: Pune severe dengue results, resource chart switching, inventory risks, warning navigation/filter/details and reset. Mobile at 390×844: forms, three additional scenarios, warning details, responsive curves and contained table scrolling. No document horizontal overflow in measured mobile views; console checks showed no errors. Saved-scenario reloads also preserve blank optional preset overrides and keep the form valid. These are interactive keyboard-driven checks, not a committed browser automation suite.
- One existing upstream Starlette/AnyIO deprecation warning remains. Docker, cloud and production concurrency were not verified.

Operational data remains simulated and aggregate calibrated, not live government or facility feeds. Emergency assumptions, discharge/service rules and staffing effects are unvalidated. Conditional intervals omit shock uncertainty; capacity projections have no probabilistic bed/staff model. No patient spillover, transmission model, clinical validation, role-specific staffing effects, combined scenarios, persistent scenario database or authenticated multi-user workflow is claimed.

**Phase 5 readiness:** the API now exposes where/when demand, stock, bed and workforce risks arise, resource-specific unmet quantities, existing receipts, immutable baseline identity and structured explanations. These can feed domestic OR-Tools redistribution/logistics next. Donor selection, transfers, optimization, Gemini and federated training are intentionally deferred.
