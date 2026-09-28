# Final demo script

Use the locally verified Docker app. No live Gemini request is part of either script. Run `scripts/prepare_demo.py` beforehand. Start **Guided demo · Pune** in Command Centre. Select the redistribution-ready simulation, then keep the guide's links so geography/profile/scenario identity follow the journey. Severe dengue / 14 days / seed 42 are inputs, not preloaded answers.

## 90-second version

| Time | Screen / action | Narration |
|---|---|---|
| 0–12 s | Command Centre; point to scope, medicine/beds/workforce and data notice | “Public healthcare networks often discover shortages too late. This national-scale prototype uses public health context and clearly labelled simulated facility operations.” |
| 12–23 s | Guided demo → Forecast | “HealthNexus forecasts resource stress before failure, with visible uncertainty and model-based stock-out estimates.” |
| 23–37 s | Dengue → Run Simulation | “Now Pune experiences a severe 14-day demand shock. These are specified emergency assumptions, not a predicted outbreak.” |
| 37–46 s | Warnings | “Warnings explain which resources and facilities need review. Prediction is not enough.” |
| 46–64 s | Redistribute → Optimize Redistribution | “Google OR-Tools searches safe donor capacity without endangering donors. This run moves 15,679 accounting items over 10 lanes, leaves 26,084 unresolved, and adds zero donor risks. The items have different medicine units.” |
| 64–75 s | Network insufficient → dengue → run → planner | “Sometimes redistribution cannot solve a systemic shortage: zero safe donors, zero transfers, 30,230 unresolved. HealthNexus refuses unsafe recommendations.” |
| 75–86 s | Federation; show saved round table and comparison | “Across five logical BRICS nodes, raw training records stay local. Only model parameters and aggregate metadata are exchanged. India slightly degrades; federation does not guarantee every node improves.” |
| 86–90 s | Finish | “HealthNexus predicts shortages before they become crises, coordinates resources when possible, and shares intelligence without centralising raw operational data.” |

The last sentence describes this prototype's intended role; forecasts are not clinically validated. If the short schedule is tight, prepare both **freshly calculated** scenario/plan browser tabs before presenting and label the saved federation report. Never substitute manually entered results.

## 3-minute version

| Time | Action | Message |
|---|---|---|
| 0–25 s | Command Centre, national scope, data notice | India includes 36 states/UTs and 207 fictional facilities. Public national statistics calibrate operations; no live government inventory feed is claimed. Show medicine availability, bed pressure, staff and current vs projected signals. |
| 25–50 s | Guided Pune Forecast | Describe 540-day histories, baseline demand, 80%/95% empirical daily bands and conditional stock-out estimates. Show a facility/resource rather than implying every hospital behaves identically. |
| 50–75 s | Severe dengue / 14 days → Run Simulation | Compare the immutable Baseline Forecast and Scenario Projection. Demand shock propagates into medicine, admissions and staff pressure. No outbreak prediction or treatment claim. |
| 75–95 s | Early Warnings | Explain a medicine warning, event date, rule factors and provenance. Baseline risks remain visible. |
| 95–125 s | Donor preview → OR-Tools | Safe capacity 17,745; target 41,763. Engine-selected 15,679 across 10 lanes; 26,084 unresolved. Donor violations/new risks 0. Critical receiver medicine warnings 7→0, but maximum individual risk still 100%. Greedy ties this district case; no artificial victory claim. |
| 125–145 s | Constrained scenario/plan | Same severe Pune shock, under-resourced preserved profile: 30,230 target, capacity 0, transfers 0. Safe redistribution cannot create missing supplies. |
| 145–170 s | Federated Intelligence | Show the accepted saved run or execute five rounds. 417 parameters, actual FedAvg, sample weighting, raw rows shared 0. Validation WAPE 100→15.95→9.97→9.51→9.37→9.33%. Test WAPE is separate. India slightly degrades; model updates can leak, no secure aggregation/DP. |
| 170–180 s | Copilot offline status; finish | “Gemini's five-model engineering is implemented; live acceptance awaits provider availability. Explicit offline summaries use the same local tools, so the core demonstration keeps working.” Finish with the 90-second closing line. |

## End-to-end checklist

- [ ] Run `prepare_demo.py`: PASS; no training, regeneration or provider call.
- [ ] Command Centre: country/profile/data notice, actual current KPIs and projected warnings.
- [ ] India → Maharashtra → Pune; redistribution-ready, severe dengue, 14 days, seed 42.
- [ ] Forecast renders actual values/uncertainty and source model.
- [ ] Scenario executes; warnings use that exact scenario ID.
- [ ] Planner previews and independently computes the positive plan; record actual remaining shortage and donor reserves.
- [ ] Constrained plan preserves zero donor capacity/transfers and unresolved 30,230.
- [ ] Federation shows saved seed-42 report or actual run; includes all five countries, raw 0 and India degradation.
- [ ] Copilot response mode OFFLINE; a local summary executes with evidence and provider requests 0.
- [ ] Desktop/mobile, keyboard focus, internal table scroll, route reload and console checked.
- [ ] Restart: saved evidence remains; recreate transient scenarios/plans. Use reset/recovery links for expired IDs.
- [ ] Cloud deployment and Gemini live acceptance are not claimed.
