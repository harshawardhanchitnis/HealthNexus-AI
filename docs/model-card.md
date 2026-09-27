# Operational generator and rule model card

Version: Phase 2, aggregate-anchors-v2. Purpose: reproducible engineering and hackathon demonstration. This is not a fitted epidemiological model or clinical recommendation system. No forecasting model is trained yet.

## Public calibration

India's PHC and CHC staffing templates use matching national workforce/facility ratios from MoHFW/PIB. Hospital doctor staffing uses pooled SDH+DH totals. Hospital nurses and other unspecified roles remain assumptions. Foreign care-centre types borrow these templates explicitly.

WHO hospital beds per 10,000 scales illustrative bed capacity: `clamp(sqrt(country density / India density), 0.65, 2.0)`. Foreign doctor staffing uses `clamp(sqrt(country doctor density / India doctor density), 0.7, 2.3)`. These bounded mappings are design assumptions, not empirically fitted relationships.

Synthetic catchment = synthetic beds / country bed density × 10,000 × bounded 0.9–1.1 variation. This is not an official population estimate. Calibration retains actual source records, reference years, assumptions and missing-data fallback descriptions. Latest years differ across countries; old source values remain visibly dated.

## Causal generation

- Daily visits derive from inferred catchment, care-centre type, assumed daily visit rates (0.011, 0.009 or 0.004), weekday, hemisphere-aware seasonality, a small trend and bounded noise (0.96–1.04).
- Assumed syndrome shares partition visits. Assumed resource profiles convert those counts into medicine requests; they are not treatment guidance.
- Occupancy follows previous occupancy + accepted admissions − discharges. Capacity limits admissions; unmet admissions are recorded separately.
- Staff availability is bounded by scheduled staffing, with controlled absence variation. Scheduling derives from calibrated role templates where public anchors exist.
- Medicine stock follows previous stock + deliveries − actual consumption. Consumption cannot exceed available supply; requested consumption = actual consumption + unmet demand. Daily closing balances become the next day's opening balance.
- Weekly replenishment uses trailing requested demand and a 21-day target: seven days each for reserve, review period and logistics buffer. A deterministic subset of facilities misses later deliveries to exercise shortages. There are no transfer events yet.

All operations span 28 days and are deterministic for a given seed, date, code and source cache. Refreshing source data can change outcomes. Public calibration supports plausibility, not validation against observed local operations. There are no real regional disease observations or emergency effects in Phase 2.

## Current alerts and limitations

Rules flag medicine cover, beds and staffing thresholds. They are not ML predictions. Days of cover uses observed consumption and can be misleading during stockouts, so unmet demand is retained and called out. Expiry, procurement lead-time uncertainty, actual local disease burden and clinical substitution are not modeled. No real patient, employee or operational facility records are ingested.

Phase 3 must build temporal train/validation splits, simple forecast baselines and measured errors. Targets should account for censored consumption and source vintage; future observations must not leak into historical evaluation. Report uncertainty and country-level limitations before presenting predictive performance. Federated models must train locally and exchange updates only; privacy is not guaranteed merely by using federation.
