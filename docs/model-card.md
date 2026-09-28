# Forecasting model card — Phase 3

HealthNexus forecasting is intended for healthcare resource planning demonstrations and is not a clinical diagnosis or treatment system. Every displayed forecast comes from the saved, evaluated country-local pipeline, including a simple baseline when that baseline wins model selection.

## Problem and data

Predict daily patient footfall, facility × medicine requested demand, and requested admissions for the next 1, 7 or 14 days. The bed endpoint predicts **admissions requested**, not occupied beds; admissions + unmet admissions avoids treating capacity-constrained admissions as unconstrained demand. Thirty-day support requires increasing the configured direct horizon, recalibration and fresh evaluation; it is not exposed yet.

The default generator produces 540 daily observations per facility, across 231 fictional facilities. India retains all 207 facilities and 36 states/UTs; each other country has six facilities. Long histories are compressed under `data/generated/history/<country>.json.gz`. The same run publishes matching last-28-day operational snapshots for the existing UI. No patient or employee data is used.

Public calibration remains MoHFW/PIB Health Dynamics of India 2022–23 workforce/infrastructure ratios and WHO GHO hospital-bed/doctor densities. See [data sources](data-sources.md). These sources do not provide real facility demand or stock. Aggregates downloaded in September 2026 are held fixed for this retrospective synthetic experiment; this is **not an as-published real-world historical backtest**. Calibration years differ across countries, including South Africa's older bed-density data.

## Causal generator and censoring

Capacity and staffing inherit explicit public aggregate ratios and bounded mapping assumptions. Synthetic catchment derives from beds and bed density. Daily visits follow facility contact rates, weekday, hemisphere-aware seasonality, gradual trend, a persistent autoregressive demand factor and bounded noise. Assumed syndrome shares partition visits and resource profiles generate medicine requests; these profiles are not treatment recommendations.

Occupancy evolves through accepted admissions and discharges with capacity limits and explicit unmet admissions. Staff attendance remains within scheduled capacity. Inventory evolves through deliveries and fulfilled consumption. Weekly ordering uses past requested demand, a 21-day target and three-day nominal lead time. A deterministic subset experiences long delivery delays; expected dates are revised only when a due date is missed. Transfers are recorded as zero and are not optimized.

`requested = fulfilled consumption + unmet demand`. Forecast targets use **requested demand**, never stock-censored consumption. In real deployments this latent target is generally unobserved; additional demand measurement or censoring-aware estimation would be required. The prototype's known latent demand is an advantage of simulation and must not be mistaken for an available real-world feed.

## Feature schema

Each row has a frozen forecast origin and direct lead time 1–14. Features include horizon, target weekday, annual sine/cosine, trend; lags 1/2/7/14/28; 7/14-day means, 28-day standard deviation and recent-week growth; historical scale, facility type, inferred catchment, beds, scheduled staffing, latitude and medicine index. Lag/rolling features use only data on or before the origin. Future weekdays and calendar dates are knowable. Same-target values, future syndrome counts, realized future stock receipts and future actual demand are excluded.

Values are normalized by the preceding 28-day mean, floored at one, and converted back to original units for evaluation/inference. This scale uses only pre-origin history. Country membership is enforced by separate training partitions and artifacts; no raw international training pool is created. Region/district/facility IDs remain row context but are not ordinal numeric predictors. No claim of causal feature attribution is made: UI explanations show measured recent trends, censoring totals and the actual selection rule.

## Models and chronology

One `HistGradientBoostingRegressor` candidate per target per country (15 models total), using scikit-learn 1.7.2: absolute-error loss, 100 iterations, 15 leaves, learning rate 0.08, L2=1, seed 42. Internal early stopping is disabled to avoid a random validation split. This lightweight pooled approach avoids per-facility models. A future model interface can replace it without changing the temporal schema or API.

Mandatory baselines freeze the same origin: last observed value, seasonal naive cycling the last seven observed days, and the preceding seven-day mean. All receive identical origin/horizon evaluation rows. The candidate approximates conditional median demand; the API calls all outputs **point forecasts**, including baselines, rather than claiming every champion is a trained conditional median.

| Partition | Target-date window | Role |
| --- | --- | --- |
| Warm-up | 2025-04-06–2025-05-03 | 28 days for initial lag features |
| Training | 2025-05-04–2026-04-18 | Fit candidate models |
| Selection | 2026-04-19–2026-06-11 | Select lowest WAPE among all four models |
| Calibration | 2026-06-12–2026-08-04 | Estimate champion residual distributions only |
| Test | 2026-08-05–2026-09-27 | Final errors and interval coverage only |

Training uses staggered weekly origins across series. Evaluation uses 14-day rolling origins with a final origin aligned to each window's end. That last block can overlap its predecessor by two days; metrics describe forecast-origin/horizon errors, not independent day samples. All target horizons stay inside their partition. Later origins may use earlier held-out observations as history because those are already observable by that origin; model weights remain frozen. There is no random train/test split and no refitting on test data.

Champion selection uses aggregate selection-period WAPE, not test scores. A champion can lose to another model on the later test window; all comparisons remain visible. Models are intentionally not refit after selection so reported interval calibration and held-out metrics apply to the deployed fitted model. The freshest observations enter inference lags, not the model fit.

## Metrics and uncertainty

MAE, RMSE and WAPE are calculated from saved predictions in original units. A zero WAPE denominator yields null. Reports include all models, 1/7/14-day lead-specific metrics, row counts and champion interval coverage per resource. Medicine MAE/RMSE pool mixed medicine units and WAPE weights high-volume series; comparisons are meaningful within a target, not as a universal health score. [Full measured results](phase3-results.md) preserve all five country comparisons and coverage.

For each resource and lead time, use absolute residuals divided by pre-origin scale from the separate calibration period. Conservative finite-sample empirical 80%/95% quantiles define symmetric point-centred daily bands, clipped at zero. Held-out coverage and mean width are measured, not assumed. Dependencies between facilities and across dates violate simple exchangeability assumptions, so these are empirical conformal-style intervals, not distribution-free guaranteed coverage. Representative foreign nodes have small residual pools and unstable coverage. Poor coverage is displayed rather than tuned using the test set.

For cumulative demand and inventory uncertainty, sample 500 entire signed normalized 14-day calibration residual paths with a stable model/facility/resource seed. Whole-vector resampling retains within-path dependence. Add them to point forecasts, scale, and clip negative demand to zero. Aggregate 80%/95% ranges use empirical path-total quantiles; they differ from summing daily interval bounds. Cumulative/stock interval coverage and probability calibration against real-world stockouts have not been validated.

## Stock-out intelligence

Forecast from the matching snapshot's current stock and safety reserve. Include only scheduled receipts whose orders were placed by the origin and whose expected dates fall after the origin. Known lead times are encoded in these dates. Assume these scheduled deliveries arrive on time; do not ingest future realized delay outcomes or invent later replenishment orders. This conservative finite-order scenario is explicitly conditional, not a complete future purchasing policy.

For each day: available = prior nonnegative stock + known receipts; closing = max(0, available − requested demand); unmet demand = max(0, requested demand − available). Unmet demand is lost service, not carried as backlog. Transfers remain zero. The point trajectory reports the first day closing stock is at/below safety reserve and first day at zero. If already breached/exhausted, report the origin date. Null dates mean no crossing within 14 days, not no future risk.

Estimated 3/7/14-day model-based stock-out probability is the fraction of sampled paths reaching zero at least once by that horizon, including already empty stock. This estimates depletion, not the probability that a particular patient receives no medicine. Cover = current stock / mean next-14-day point demand, excluding receipts; it is null for zero demand. The inherited operational safety reserve uses trailing fulfilled consumption and can itself understate desired reserves under censoring. Risk labels are explicit decision thresholds: HIGH at ≥50% seven-day estimated depletion; WATCH for a point safety breach or ≥20% fourteen-day depletion; LOW otherwise. These are demonstration labels, not clinical or procurement policy.

## Artifacts, reproducibility and intended use

`scripts/forecast.py generate|build|train|evaluate` runs each stage deliberately. `artifacts/models/<country>` holds a compressed joblib bundle, integrity checksum and JSON metrics. Bundles store fitted candidate models, champions, feature schema, date windows, last observations, residual paths, public calibration inputs, snapshot fingerprints and dataset/config version hashes. Runtime imports only saved models; it never trains at startup. Missing, corrupted, mismatched or stale artifacts return explicit 503 states. Restart after regeneration/retraining.

Joblib loading is restricted by workflow to trusted locally built artifacts. A checksum detects corruption, not a malicious replacement with a matching checksum. Never load untrusted model files. Raw and training datasets remain in country-local files and no federation occurs in Phase 3. Seeded generation is byte reproducible; same pinned environment/config reproduces numeric training and evaluation. Wall-clock metadata changes between training runs.

Suitable uses: demonstrating data lineage, temporal evaluation, planning interfaces and future warning/scenario integration. Prohibited uses: diagnosis, treatment, real patient triage, autonomous staffing or procurement decisions, or claims of proven live-government predictive accuracy. The simulator is regular and easier to forecast than real operations. No disease outbreak generalization, live feed validation, causal treatment inference or production security is established.

Implementation references: [scikit-learn histogram gradient boosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html), [lagged time-series features and temporal evaluation](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html).

## Separate Phase 7 federated model

The operational models above remain unchanged. A separate PyTorch 417-parameter MLP learns normalized direct-horizon footfall from existing country-local frozen-origin tables. Standard FedAvg averages locally trained weights by sample count; no tree parameters, raw rows, predictions or final accuracy numbers are averaged as a substitute. Local-only, initial-global and final-global models are evaluated chronologically on simulated histories. Test data is excluded from training and tuning. The seed-42 initial model has 100% WAPE; four representative foreign nodes improve versus their independently trained MLPs while India degrades slightly. This is not evidence that the global MLP outperforms the operational HGB/selected baseline or generalizes clinically. No differential privacy or secure aggregation is implemented. [Full model/features/normalization and limitations](federated-learning.md), [actual measurements](phase7-report.md).

## Phase 4 scenario projections

Phase 4 reuses these exact saved baseline forecasts and calibration residual vectors. It does not train an outbreak model. Deterministic fever/resource/admission increments translate baseline point forecasts, daily intervals and 500 paired residual paths. Scheduled-receipt shifts change inventory risk; staff/facility scenarios change operational capacity. Empirical Phase 3 test coverage does not validate conditional scenario bands or real outbreak stock-out probabilities. Shock uncertainty is omitted. Source target model names and bundle versions remain attached to projections/warnings. See [Phase 4 report](phase4-report.md) for equations and thresholds.
