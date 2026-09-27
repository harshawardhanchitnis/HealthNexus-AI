# Phase 3 implementation report

Phase 3 adds predictive forecasting, measured evaluation and stock-out intelligence while retaining the Phase 1/2 application and all 38 original tests.

## Files and implementation

Added `backend/app/forecasting/` with `data.py`, `features.py`, `training.py`, `evaluation.py`, `prediction.py`, `stockout.py`, `schemas.py`, `routes.py` and the package initializer. Added the consolidated `scripts/forecast.py` workflow and `backend/tests/test_forecasting.py`.

Extended the existing generator and domain models with long histories, persistent daily demand, historical staffing/capacity, requested/fulfilled/unmet medicine demand, scheduled receipts, delays, lead times and zero transfer fields. Existing APIs retain 28-day snapshots; Phase 3 publishes them from the same long histories. Updated API route registration, JSON persistence, dependency pins, ignored artifact directories and optional read-only Compose mounts.

Added Angular `pages/forecasts.ts/html`, `pages/model-performance.ts`, `core/forecast-models.ts`, `shared/forecast-chart.ts` and `shared/predictive-outlook.ts`. Updated API client, routes, navigation, geographic selectors, facility page, responsive styling and scope/BRICS labels. Deep-link reload selection now stays consistent with the displayed resource/district. Updated README, architecture, scope, API, master prompt, data-source instructions, model card, demo and validation. Measured reports are preserved under `docs/evaluation/` and `docs/phase3-results.md`.

## Data, model and chronology

Generated 540 days from **2025-04-06 through 2026-09-27**, for all 231 fictional facilities across the five configured nodes. Histories occupy approximately 13.7 MB compressed; all saved model bundles/metadata total approximately 2.1 MB. Raw operations remain country-local; there is no international training pool.

Trained three pooled `HistGradientBoostingRegressor` candidates per country: patient footfall, requested medicine demand across five resources, and requested admissions. Features include calendar/horizon, pre-origin lags and rolling statistics, recent growth, normalized scale, type, catchment, beds, staffing, latitude and medicine index. See the [model card](model-card.md) for all assumptions and parameters.

Compared last-value naive, weekly seasonal naive, seven-day moving average and actual ML predictions. Champions use **selection WAPE**, never the later test scores. Russia's admissions champion is seasonal naive. Other targets select the histogram boosting candidate.

| Partition | Dates |
| --- | --- |
| Lag warm-up | 2025-04-06–2025-05-03 |
| Training | 2025-05-04–2026-04-18 |
| Selection validation | 2026-04-19–2026-06-11 |
| Residual calibration | 2026-06-12–2026-08-04 |
| Untouched test | 2026-08-05–2026-09-27 |

Rolling origins cover every held-out window through its final date. The final block overlaps its predecessor by two days; results represent origin/horizon forecasts, not independent daily samples. The model fit is frozen after the training period. Pre-origin held-out observations may enter later-origin lags because those observations are then available.

## Actual results

The [complete results table](phase3-results.md) includes all 60 country/target/model comparisons with MAE, RMSE and WAPE, plus observed interval coverage. Full JSON reports include day-1/day-7/day-14 scores and model versions. Nothing is replaced with invented accuracy values.

India test WAPE: patient footfall **2.996932%**, medicine demand **3.079865%**, requested admissions **3.344126%** for ML, compared with seasonal naive **3.944049%**, **3.998862%** and **3.923392%** respectively. This measures simulated demand, not real-world predictive accuracy.

Poor comparisons remain visible: Brazil and China admissions have lower test WAPE with seasonal naive than with their selected ML champion. Selection is not retroactively changed. China's admissions nominal 95% interval achieves about **92.56%** test coverage; nominal 80% ORS coverage is about **75.30%**. These limitations are reported, not tuned away using the test set.

## Uncertainty and stock-out method

Daily 80%/95% ranges use per-resource/per-horizon absolute normalized residual quantiles from the separate calibration period. Coverage is evaluated on test predictions. Whole signed 14-day residual paths are bootstrapped 500 times with a deterministic seed for cumulative-demand ranges and stock trajectories, preserving within-path error dependence.

Stock projection includes only receipts ordered by the origin, scheduled lead times and current reserves. It assumes known receipts arrive on schedule and excludes future unplaced orders, realized future delay knowledge and transfers. Outputs include point inventory/unmet demand, first safety breach, first depletion, cover excluding receipts and fraction of sampled paths reaching zero within 3/7/14 days. Probabilities are model-based estimates conditional on these assumptions, not real-world guarantees.

## Validation

- **73 backend tests pass**, including all original 38. New cases exercise temporal generation/tables, censoring, leakage prevention, origin alignment, chronological splits, baseline math, fitting reproducibility, artifact reload/integrity, horizons, isolation, intervals, stock dates/conservation, delayed known receipts, probability calculations and missing/stale models.
- Python compilation, Angular production build and strict TypeScript checks pass. Initial frontend bundle: approximately 337.69 kB raw / 93.94 kB estimated transfer.
- Generated history, built tables, trained all five countries and independently re-evaluated saved models. Reloaded models reproduce recorded test MAE within numerical tolerance.
- Backend restarted with saved artifacts; startup did not train. Live API smoke tests and desktop/mobile browser checks cover the Pune medicine workflow, admissions, horizon switching, evaluation tables, country isolation, deep-link reloads and facility outlook.
- One upstream Starlette/AnyIO deprecation warning remains. Firestore, Docker runtime deployment and clinical/real-world prediction validation remain unverified.

## Exact commands — PowerShell

From the repository root, with the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe scripts\forecast.py generate --country all --days 540 --as-of 2026-09-27 --seed 42
.\.venv\Scripts\python.exe scripts\forecast.py build --country all
.\.venv\Scripts\python.exe scripts\forecast.py train --country all
.\.venv\Scripts\python.exe scripts\forecast.py evaluate --country all
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Second terminal, from the repository root:

```powershell
cd frontend
npm ci
npm start
```

Open http://127.0.0.1:4200. A single country can be selected with `--country IN`, `BR`, `RU`, `CN` or `ZA` at each workflow stage. Use the same generation seed/date and pinned dependencies for reproducibility. For public-source updates first run `scripts/import_official_data.py --refresh`, then all four forecasting stages and restart. Existing artifacts can simply be served without regeneration.

## Limitations and Phase 4 readiness

All facility identities, demand, inventory, attendance and admissions are simulated. MoHFW/PIB national workforce/infrastructure statistics and WHO densities are genuine public calibration inputs. Source vintages are fixed retrospectively and not a historical real-time feed. Latent requested demand is known in simulation; a real deployment must measure or estimate it. Foreign nodes have small residual samples; stock-out probability calibration on actual health operations is not established.

Phase 4 **Early Warning Engine + Emergency Digital Twin** can consume typed demand trajectories, empirical residuals, inventory projections, reserve breaches, conditional risk and provenance. It should introduce explicit event inputs, scenario-state conservation and before/after evaluation. No full emergency simulator, OR-Tools, Gemini or federated training was added in Phase 3.
