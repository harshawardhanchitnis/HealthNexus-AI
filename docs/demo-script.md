# Phase 7 Federated Intelligence — current entry point

1. Open **Federated Intelligence**. Show India, Brazil, Russia, China and South Africa; India has 139,524 local training examples and each representative foreign node 4,046, drawn from existing 540-day simulated histories.
2. Show **Raw operational records shared: 0**. The diagram's arrows represent parameters, not patient data or medicine transfers.
3. Leave **5 rounds**, **1 local epoch**, **Standard FedAvg · sample weighted**, seed 42. Click **Run Federated Training**. No Gemini call is made.
4. Observe actual backend local training/progress. Expand training events to show each client, update byte count, aggregation and global distribution. Fast stages may complete between polls; recorded events remain available.
5. Inspect rounds 0–5 and measured global validation WAPE. The initial untrained model measures 100%; final validation is about 9.3282%. These are measured errors, not classification accuracy.
6. Read the country held-out comparison. Show India's slight degradation, 8.9496% local-only → 8.9511% global, and four foreign-node improvements. Initial-global is 100% on each. Foreign nodes have only six representative facilities; shared simulator patterns limit generalization.
7. Show total serialized logical boundary bytes and raw count zero. The measured CLI run uses 614,235 bytes and 4.80 seconds; UI timings/metadata bytes can differ slightly. Only parameters/aggregate metadata cross client boundaries. Global MAE/WAPE are computed from aggregate errors, not averaged accuracy scores.
8. Explain that the experimental global MLP is separate from authoritative operational HGB forecasts. Redistribution stays domestic. No differential privacy, secure aggregation, production sovereignty or guaranteed privacy is claimed.
9. Optional: select **Balanced country · equal weights** for an explicitly different demonstration policy. Do not describe it as sample-weighted FedAvg or expect identical metrics.

See [measured Phase 7 report](phase7-report.md) and [reproducible CLI](federated-learning.md). Gemini remains **Implementation complete; live provider acceptance pending due to Gemini service availability**; do not send live Gemini requests during Phase 7.

# Phase 6 Copilot demo — deterministic operational showcase

1. Open **Resilience Copilot**. Select India → Maharashtra → Pune and **Redistribution-ready simulation**. Inspect the profile notice and administrative-only scope.
2. Choose **Use offline summaries** explicitly while Gemini service availability blocks live acceptance. The page and every response must say OFFLINE; these steps verify local engines, not Gemini reasoning. All five configured models returned 503 HIGH DEMAND in retained evidence. Do not make live calls during Phase 7 or claim live success from mock/offline evidence.
3. Select **Simulate dengue & plan redistribution**. Inspect the populated severe 14-day question and explicit planning checkbox, then submit. The six actual tools summarize the network, run the scenario, compare it, inspect warnings, preview donors and optimize.
4. Read the real result: 41,763 → 26,084 target deficit, 17,745 safe capacity, 15,679 transferred item tally, 10 lanes, zero new donor risks/reserve violations. Inspect individual resource units/reserves. IVF and PCM retain 100% conditional 14-day stock-out risk; some other resources improve. No physical transfer is executed.
5. Ask **Explain selected donors** in the same conversation. Expand evidence and tool activity. Open **Open actual optimizer result** to inspect the saved authoritative plan and greedy comparison; profile and scenario IDs remain scoped.
6. Switch to **Network-insufficient simulation**. The conversation resets. Repeat the authorized severe dengue workflow. Read 30,230 unresolved, zero safe capacity, zero transfers and OPTIMAL constrained status. An optimal constrained plan can leave a shortage unresolved.
7. Ask **Is this live government inventory?**. Show actual calibration/source metadata and the explicit false live-inventory field. Public historical aggregates and simulated facility operations must remain distinct. Review forecast reliability separately from real-world clinical accuracy.
8. Profile comparison requires its explicit checkbox and keeps independent profile-labelled results. Individual diagnosis or prescribing requests receive a refusal before model/tool calls. New conversation clears local session records; it does not delete Google-side history.

See [measured Phase 6 report](phase6-report.md). The following sections document earlier milestones and retain their historical conditions.

# Historical Phase 3 demo — forecasting with evidence

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
