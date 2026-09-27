# Phase 3 demo — forecasting with evidence

1. Open **Data Sources**. Show the two real integrations, historical dates and simulated operational distinction. These aggregates calibrate the prototype; they are not live facility feeds.
2. Open **Forecasts**. Select India → Maharashtra → Pune → Pune PHC 01 → IV fluids. Show the preceding 28 daily observations, future 1/7/14-day forecasts and empirical 80%/95% intervals. The full training history contains 540 days.
3. Show expected demand, changes from the recent week and the model/version. Explain that medicine targets retain requested demand even when stock limits fulfilled consumption.
4. Show stock intelligence: current reserve, incoming scheduled receipt, point reserve-breach date, conditional depletion date, 3/7/14-day model-based risks and daily projected inventory. A zero risk means none of the sampled residual paths depleted in this specific scenario; it is not a guarantee.
5. Open **Model Performance**. Show the chronological training, selection, calibration and test windows; all four model comparisons; actual interval coverage. India ML improves aggregate error; Russia admissions selects seasonal naive. Brazil and China admissions have a baseline with lower test WAPE than their previously selected ML champion—keep this visible.
6. Open the existing Pune facility detail and its **Predictive Outlook**. Then switch to another country to show local facility scope and separate model evaluation. BRICS federation remains future work; local forecasting training is real.
7. Explain reproducibility: regenerate history → build temporal tables → train → independently evaluate/reload. Restarting FastAPI does not retrain. Missing/stale artifacts show an explicit unavailable state.

Phase 4 will connect these typed outputs to predictive warning workflows and an emergency digital twin. No dengue controls, optimizer, Gemini response or FedAvg run is claimed in this milestone.
