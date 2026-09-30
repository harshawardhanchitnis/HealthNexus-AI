# Deployment decision — ₹0 first

## Current Render Free / India-only runtime (2026-09-30)

The public endpoints are Firebase `https://healthnexus-ai.web.app` and Render
`https://healthnexus-api-aizt.onrender.com`. Render reported out-of-memory restarts.
The new local capacity gate is documented in [the memory report](low-memory-deployment-report.md);
it does **not** establish that the cloud deployment is fixed.

The **only new Render environment variable** is `HEALTHNEXUS_LOW_MEMORY=true`.
Keep the existing API key, Gemini enabled/model/fallback settings, storage and CORS.
Use the existing service, repository-root context and `backend/Dockerfile`.
The public image defaults to `INSTALL_FEDERATION_TRAINING=0`: no PyTorch installation.
India is the sole operational country; foreign operational requests return a clear 422.
Saved five-node federation evidence is validated and readable without training or
foreign operational model deserialization. Live federation starts return controlled 409.

Low-memory readiness streams trusted India artifact hashes and verifies compatibility
metadata and saved federation integrity. It never predicts, unpickles operational models,
imports PyTorch or probes Gemini. The capability response remains cached for 30 seconds.
The immutable bundle still contains 77 files with its original pinned SHA-256.

Full local/unconstrained behavior remains available with `HEALTHNEXUS_LOW_MEMORY=false`.
`docker compose` explicitly builds with `INSTALL_FEDERATION_TRAINING=1`; a standalone
training image can be built with `docker build --build-arg INSTALL_FEDERATION_TRAINING=1
-f backend/Dockerfile -t healthnexus-local .`. Do not use that training image on Render Free.

Frontend source changed to show India operations and saved experiment capabilities.
Angular has been rebuilt; its production runtime configuration retains the Render HTTPS
origin above. **A new Firebase Hosting deployment is required, but was not executed.**
No Firebase configuration, map provider, CORS, billing or API key was changed.

## Historical hosting review (2026-09-28)

The following review predates the existing public deployment and the low-memory runtime.
At that time no cloud resources were created or billing enabled by Codex, and the
complete interactive demo was verified locally in Docker. Its image/memory measurements
describe the older training-enabled image, not the new public runtime.

| Component | Prepared / verified | Billing and decision |
|---|---|---|
| Angular / nginx | Production build, lazy routes, API proxy, SPA reload verified in Docker | Local ₹0 demonstration works |
| Firebase Hosting | `firebase.json`, `/index.html` rewrite, uncached runtime API origin prepared | Static Hosting has Spark no-cost allowances. No project/site was selected or deployed |
| Cloud Run | Linux container, non-root process, `PORT`, `/health`, `/readiness`, baked assets verified | A linked Cloud Billing account is required even for free usage. Deployment blocked by the no-billing instruction |
| Firestore | Existing explicit snapshot adapter retained | Spark has a limited free default database; no available project/database/credentials were supplied for acceptance. Migration is unnecessary for this demo |
| Gemini | Five-model implementation retained, optional backend configuration | No live calls; prior real-provider acceptance blocked by HTTP 503 HIGH DEMAND |

Sources: [Firebase plans](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans), [Hosting with Cloud Run and billing requirement](https://firebase.google.com/docs/hosting/cloud-run), [Firestore free quota](https://firebase.google.com/docs/firestore/quotas), [Cloud Run container contract](https://cloud.google.com/run/docs/container-contract). A free allowance is not a spending cap or a promise of a ₹0 invoice.

## Recommended hackathon route

Use the verified local Docker product, current screenshots and a screen recording. This requires no cloud account, network inference, billing or Firestore migration. A static Firebase page alone cannot run FastAPI, OR-Tools or PyTorch. Publishing the Angular dashboard without a reachable HTTPS backend would produce unavailable-data states, not a complete hosted demonstration.

Firebase Hosting is a feasible later static target on Spark, subject to project ownership, current plan and quotas. The following are reviewable commands only; **none were executed**:

```powershell
cd frontend
npm ci
npm run build
cd ..
# Only after an HTTPS backend is selected:
.\.venv\Scripts\python.exe scripts/configure_frontend.py --api-base https://YOUR_APPROVED_API_ORIGIN
# Select an existing Spark project/site; verify its plan before publishing:
npx firebase-tools deploy --only hosting --project YOUR_APPROVED_PROJECT_ID
```

The public API origin goes in the built `runtime-config.js`. It contains no credentials. The backend must allow exactly the approved Hosting origins through `HEALTHNEXUS_CORS_ORIGINS`. No Cloud Run rewrite is present in `firebase.json`: that integration would require billing. Base href is `/`; nginx and Hosting both rewrite deep routes to the SPA. Hashed nginx JS/CSS assets cache immutably; the runtime configuration stays uncached.

## Cloud Run: prepared, not activated

Before any Cloud Run action, a separate decision must approve billing, project, region, registry/build charges, IAM and spending controls. The current instruction forbids billing, so this work stops at configuration and documentation. A future deployment could build the verified Dockerfile and deploy an **existing approved image** using:

```sh
# FUTURE ONLY — requires a billing-enabled project; do not execute under the ₹0 restriction.
gcloud run deploy healthnexus-api --image APPROVED_IMAGE_URI --project APPROVED_PROJECT_ID \
  --region APPROVED_REGION --port 8000 --cpu 2 --memory 2Gi --concurrency 1 \
  --min-instances 0 --max-instances 1 --no-allow-unauthenticated \
  --set-env-vars HEALTHNEXUS_STORAGE=local,GEMINI_ENABLED=false
```

This intentionally does not grant public API access. The Angular-to-private-backend authentication design is not implemented. Building/pushing through Google services may incur costs too. No claim is made that the above command alone gives a secure, production-ready hosted system.

`backend/start.py` listens on `0.0.0.0:$PORT` with one process. Linux assets use repository-relative paths. `/health` is fast liveness; `/readiness` checks ten profile/model partitions and saved federation evidence, caches the capability check for 30 seconds, and never probes Gemini. Forecasts are never trained at startup. Trusted assets are owned by root; the runtime user can write only the federation experiment directory among application assets.

Measured image size: backend **2,159,139,278 bytes**, final frontend **94,430,376 bytes**. CPU PyTorch and scientific/Google dependencies dominate the backend. Canonical generated data are about 104 MB and operational bundles about 2.1 MB. A cold restart reached `/health` in **4.61 s**; an observed post-readiness backend memory reading was **328.5 MiB**, not a peak guarantee. Training/container behavior must be capacity-tested on the actual cloud machine; no cloud latency is asserted.

The experimental federation worker runs in the background. Request-based Cloud Run CPU allocation can suspend work after the start response; instance-based CPU or a job/queue design would be needed for reliable cloud training. That introduces another deployment/billing decision. Use saved, integrity-checked federation evidence for presentations. Scenarios, plans, conversations and new run indexes remain bounded process-local state; restart loses their IDs. Do not scale this prototype across replicas without durable state. Firestore's existing snapshot adapter does **not** solve those workflow/queue requirements.

## Laptop reset and portability

### Render clean-checkout packaging (2026-09-30)

The reviewed canonical bundle is now versioned at `deployment-assets/demo-assets.zip`:
77 asset files, 72,340,666 bytes, SHA-256
`966f452b95d7bacff92ccfdbb0fce8ba1beb4593ad0bcb8064d6c0d03397f7dd`.
It contains only `data/generated/`, `artifacts/models/` and `artifacts/planning/`
assets plus their checksum manifest; no credentials. Loose operational assets
remain gitignored. The Docker context excludes them and all other local artifacts.

For the existing Render service, retain repository-root build context and use
`backend/Dockerfile`; do not set the service root to `backend`. The image build
checks the archive's pinned SHA-256, runs the existing path/checksum-validating
`scripts/restore_demo.py`, and removes the ZIP from the final runtime filesystem.
No models are trained and no data are regenerated. The existing non-root user,
`PORT` handling, health check and startup command are unchanged.

```powershell
docker build -f backend/Dockerfile -t healthnexus-render-test .
```

Local deployment gates passed: all 77 restored files match canonical hashes;
`/health` and `/readiness` return HTTP 200; all ten country/profile partitions
are ready; district, constrained and cross-district HTTP plans retain their
accepted accounting totals, donor safety and conservation; saved federation
evidence reloads with its accepted checksum. Gemini was disabled and provider
calls were zero. Python compilation, host/container `pip check`, the existing
canonical verifier and eight readiness/reload tests passed. These local gates
do not establish Render Free memory/CPU capacity or claim a successful cloud
deployment. Pushing the packaging commit triggers the already configured
service's automatic deployment; no new service or billing change is required.

On this existing checkout:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo.py
docker compose build
docker compose up -d
.\.venv\Scripts\python.exe scripts/smoke_demo.py --base http://127.0.0.1:8000
```

`prepare_demo.py` is a verifier, not a reseeder. It retains all measured snapshots, models and the accepted experiment. For a fresh machine, `scripts/package_demo.py` produces an ignored `artifacts/demo-assets.zip` with all canonical generated/model/planning assets and SHA-256 entries, never `.env`. The current bundle is 72,340,666 bytes. Transfer only this trusted simulated-data bundle and the repository, then run:

```powershell
.\.venv\Scripts\python.exe scripts/restore_demo.py PATH_TO_TRUSTED_DEMO_BUNDLE.zip
.\.venv\Scripts\python.exe scripts/prepare_demo.py
```

Restore validates every path/hash before writing missing files, and refuses to overwrite differing measured assets. Only trust bundles you generated or whose external SHA-256 you verified; a self-contained checksum is not an authenticity signature. The canonical small federation checkpoint/report is versioned under `data/demo/federation/` and survives backend restarts.

If the bundle is unavailable on a fresh clone, the historical explicit workflow remains: offline public import; `forecast.py generate --country all --days 540 --seed 42 --as-of 2026-09-27`; `build`, `train`, `evaluate`; both `generate_data.py --profile ... --country all`; both India `prepare_planning.py` commands. This is a full rebuild, **not** the normal startup/reset path. Rebuilding can change artifact identities and last-bit numeric results across platforms. It must pass compatibility checks and a separately recorded federation evaluation; never silently rebind the preserved Phase 7 evidence to different tables.
