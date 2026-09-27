# Phase 2 implementation report

Implemented September 27, 2026, continuing the existing Phase 1 repository.

## Files changed

- **Ingestion:** added `backend/app/data_ingestion/{base,india_hdi,who_gho,catalog}.py`, package initializer and `scripts/import_official_data.py`; added attributed extracts under `data/official/{india,who}` and normalized records under `data/normalized`.
- **Domain:** added `backend/app/models/provenance.py`, `backend/app/core/geography.py` and `data/metadata/brics-regions.csv`; extended `models/network.py` with countries, provenance, ledgers and flow validation.
- **Generation/storage:** added `simulation/calibration.py`; refactored `simulation/generator.py`; updated `services/repository.py`, generation/seeding scripts, Dockerfile and `.gitignore`.
- **API/tests:** extended `backend/app/main.py`; added `backend/tests/test_phase2.py`. Original tests remain intact.
- **Frontend:** added `pages/data-sources.ts` and `pages/brics.ts`; updated navigation, country selection, routes, client, models, dashboard, facility detail, scope page, responsive styles and page metadata.
- **Docs:** updated README, master brief, scope, architecture, sources, model card, API, demo, validation, data-layer READMEs and screenshots; added this report.

## Geography

India retains all 36 states/UTs, 69 illustrative districts and 207 fictional facilities. Brazil, Russia, China and South Africa each have two representative regions and six fictional facilities. Snapshot files/API requests are country-scoped; India's defaults and legacy snapshot format remain compatible. These are the five configured hackathon nodes, not an exhaustive current BRICS membership list. Logical partitioning does not imply production security isolation.

## Actual sources

1. **MoHFW/PIB Health Dynamics of India 2022–23 summary:** actual HTML adapter/cache, 13 national infrastructure/workforce counts referenced to March 31, 2023. Ratios influence synthetic staffing. This is not HMIS API integration or a facility registry.
2. **WHO GHO OData:** actual API adapter/cache, 20 country/year observations for hospital beds and doctors per 10,000 across five countries. Indicators influence capacity, catchment and staffing. Heterogeneous reference years remain visible.

Both were fetched on 2026-09-27 and imported offline. [Source documentation](data-sources.md) contains links, fields, terms, attribution and refresh commands. Source material retains its own terms; WHO does not endorse this project.

## Generation and provenance

Public anchors drive explicit baseline ratios. Demand depends on inferred catchment, facility type, weekday, assumed seasonality/trend and bounded noise. Syndrome counts drive medicine requests; consumption is limited by available stock and unmet demand is explicit. Daily inventory and admission/discharge balances reconcile. Weekly deliveries and deterministic delays exercise shortages.

Metadata distinguishes official public, international public, derived, synthetic and future simulation, retaining URLs, access dates, geography, terms, methods, versions, hashes and input references. Snapshots freeze calibration inputs. Missing data produces visible assumptions; corruption fails validation. All fictional operations remain labelled simulated.

## Verification

**38 backend tests passed**, including the original 13. Angular production build, strict TypeScript checks, Python compilation, offline import and all-country generation passed. Desktop/mobile browser checks verified India drill-down, Brazil isolation/details, source filtering and honest node status. See [validation](validation.md).

## Exact local commands

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe scripts\import_official_data.py
.\.venv\Scripts\python.exe scripts\generate_data.py --country all --seed 42 --as-of 2026-09-27
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Second terminal, from the repository root:

```powershell
cd frontend
npm ci
npm start
```

App: http://127.0.0.1:4200. API documentation: http://127.0.0.1:8000/docs. No credentials required. Add `--refresh` to import for real-source downloads, then regenerate and restart. Existing environments can skip creation/install steps.

## Phase 3 and later

Next: temporal training tables, demand/stockout targets accounting for censored consumption, baseline forecasting, held-out evaluation, uncertainty and forecast UI. Dashboards already exist despite the original brief's historical phase numbering.

Later: emergency scenarios; domestic redistribution with donor reserves/audited transfers; OR-Tools; verified Gemini integration; genuine local country training and update-only FedAvg. Do not pool raw operational training data. Live operational connectors, authentication and production country isolation remain future work. Firestore and Docker deployment were not exercised here.
