# Phase 3 demo — forecasting with evidence

1. Open **Data Sources**. Show the two real integrations, historical dates and simulated operational distinction. These aggregates calibrate the prototype; they are not live facility feeds.
2. Open **Forecasts**. Select India → Maharashtra → Pune → Pune PHC 01 → IV fluids. Show the preceding 28 daily observations, future 1/7/14-day forecasts and empirical 80%/95% intervals. The full training history contains 540 days.
3. Show expected demand, changes from the recent week and the model/version. Explain that medicine targets retain requested demand even when stock limits fulfilled consumption.
4. Show stock intelligence: current reserve, incoming scheduled receipt, point reserve-breach date, conditional depletion date, 3/7/14-day model-based risks and daily projected inventory. A zero risk means none of the sampled residual paths depleted in this specific scenario; it is not a guarantee.
5. Open **Model Performance**. Show the chronological training, selection, calibration and test windows; all four model comparisons; actual interval coverage. India ML improves aggregate error; Russia admissions selects seasonal naive. Brazil and China admissions have a baseline with lower test WAPE than their previously selected ML champion—keep this visible.
6. Open the existing Pune facility detail and its **Predictive Outlook**. Then switch to another country to show local facility scope and separate model evaluation. BRICS federation remains future work; local forecasting training is real.
7. Explain reproducibility: regenerate history → build temporal tables → train → independently evaluate/reload. Restarting FastAPI does not retrain. Missing/stale artifacts show an explicit unavailable state.

The historical Phase 3 milestone did not include dengue controls, optimization, Gemini or FedAvg. The Phase 4 and Phase 5 demonstrations below now connect its typed outputs to warnings, scenarios and domestic planning.

## Phase 4 emergency demo

Use **Emergency Simulator → Load Pune demo → Dengue surge → Severe → 14 days → Run Simulation**. Compare the computed before/after KPIs and resource impacts. Select the district hospital and IV fluids: baseline reserve lasts longer; scenario depletion occurs within the horizon. Inspect bed unmet admissions and personnel pressure. Open scenario warnings, filter severity/category and expand factual explanations. Return to comparison and discard the scenario; baseline endpoints are unchanged.

Additional demos: Medicine delivery delay with Critical (14 days) for IV fluids; Staff shortage with Severe (40% unavailable); Facility/flood disruption with Severe (50% reduced usable beds/service). See [Phase 4 report](phase4-report.md) for exact values, assumptions and full steps. These are operational projections on simulated data, not disease-spread or clinically validated predictions.

## Phase 5 redistribution demo

1. Open Emergency Simulator; load India → Maharashtra → Pune, Severe Dengue, 14 days, and Run Simulation.
2. Select **Optimize Redistribution** on that saved scenario. Receiver scope remains Pune; donor scope defaults to national within India.
3. Inspect target deficits, expected unmet demand, warning severity, depletion and risk. Inspect the safe donor pool **before** solving.
4. Click **Optimize Redistribution**. Read actual CP-SAT status, stage evidence, before/after balances and unresolved targets.
5. With the existing 2026-09-27 snapshot, demonstrate the **insufficient-network** result: 30,230 target units, zero safe donor units, zero transfers, 17,075.1558 expected unmet units. An OPTIMAL constrained result does not mean the shortage disappeared.
6. Inspect calculated OR-Tools/greedy outcomes: both tie with zero transfer distance and zero donor violations. Inspect a PCM or IVF trajectory and its 3/7/14-day risks.
7. **Discard optimization plan**; the scenario remains selected and its baseline/forecast values are unchanged. District/state searches and baseline planning are also available.

A positive-transfer Pune showcase cannot honestly be demonstrated from this snapshot under full donor reserve protection. Nonzero solver and impact behavior is verified with explicit test fixtures; do not present those fixtures as Pune results. See [Phase 5 report](phase5-report.md) for measured results and the replenished-data prerequisite.
