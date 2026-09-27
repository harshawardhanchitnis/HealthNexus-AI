# HealthNexus AI — India-only master build prompt

This is the supplied build brief with the geographic change applied throughout.
The BRICS Resilience track remains hackathon context only; product geography,
datasets, federation and redistribution are scoped exclusively to India.

Scope requirement: cover every Indian state and union territory. A synthetic
sample may be used for initial implementation, but its district/facility coverage
must be labelled honestly and must not be described as a complete real registry.

We are starting a new hackathon project called:

# HealthNexus AI
**Federated Intelligence for Healthcare Resilience**

This project is for the **Google AI Build / Code for Communities Hackathon** under:

**Track:** BRICS Theme — Resilience

## Official Problem Context

Public healthcare systems across India face persistent supply-chain and resource-management vulnerabilities.

The challenge is to build a federated AI platform capable of providing national-scale visibility into:

- Medicine inventory
- Bed availability
- Patient footfall
- Medical personnel availability/attendance
- Health-resource utilisation

The platform should:

- Forecast future demand
- Detect potential medicine/resource stock-outs before they happen
- Generate early warnings during emergencies
- Recommend automated cross-district resource redistribution
- Support shared predictive modelling across Indian states and union territories
- Preserve data sovereignty by avoiding unnecessary centralisation of raw sensitive data

---

# 1. PRODUCT WE HAVE DECIDED TO BUILD

Build:

# HealthNexus AI

An India-only, national-scale AI healthcare resilience and resource-management platform covering all states and union territories.

The core concept is:

> HealthNexus AI continuously observes healthcare-resource conditions across a network of Primary Health Centres and other public facilities, forecasts shortages before they occur, detects emerging health emergencies, calculates optimal redistribution of resources, and allows Indian state and regional nodes to improve predictive models collaboratively without sharing raw operational or patient data.

This should NOT become a generic hospital-management CRUD application.

It needs to feel like a:

**National Healthcare Resilience Command Centre.**

---

# 2. PRIMARY DEMO EXPERIENCE

The strongest part of the project must be the live emergency simulation.

Example demo:

The dashboard initially shows:

- National healthcare network status
- Facilities online
- Healthy facilities
- At-risk facilities
- Critical facilities
- Medicine availability
- Bed utilisation
- Staff availability
- Current alerts

Then the user can trigger:

**Simulate Emergency → Dengue Outbreak → Pune District → +65% patient demand**

The simulation should cause realistic downstream effects:

Patient footfall increases

↓

Disease-specific medicine consumption increases

↓

Medicine stock cover decreases

↓

Bed utilisation increases

↓

Selected facilities become at risk

↓

ML forecasting detects upcoming shortages

↓

Early-warning engine generates alerts

↓

Resource redistribution engine identifies nearby facilities with safe excess inventory

↓

Google OR-Tools calculates an optimal transfer plan

↓

Gemini 3.8 Flash analyses the structured results and produces a concise emergency-response recommendation

Example:

“PHC A is projected to exhaust IV fluids within 1.8 days. Transfer 120 units from PHC B and 80 units from PHC C. Both donor facilities will remain above their seven-day emergency safety-stock threshold.”

This end-to-end flow must actually be represented in the implementation.

---

# 3. TECH STACK — LOCKED

Use this architecture unless there is a serious technical reason not to.

## Frontend

- Angular
- TypeScript
- Angular standalone architecture
- Angular Router
- SCSS
- Signals where appropriate
- Responsive dashboard
- Reusable visualisation components

For charts/maps use suitable open-source/free libraries.

The frontend should look like a premium national command centre, not a basic student dashboard.

---

## Backend

Use:

- Python
- FastAPI
- Pydantic
- REST APIs
- Async where useful

Python is preferred because we will have:

- ML forecasting
- Optimization
- Data simulation
- Federated learning
- Gemini integration

---

## Database

Use:

- Firebase / Cloud Firestore

Model collections cleanly for things such as:

- national configuration (India only)
- states and union territories
- districts
- facilities
- medicines
- inventory
- stock transactions
- patient footfall
- beds
- staff
- alerts
- forecasts
- emergency scenarios
- resource transfers
- federated model metadata

During local development, allow a local/mock fallback if Firestore credentials are unavailable.

Do not hardcode production credentials.

---

## Generative AI

Use:

**Gemini 3.8 Flash API**

Gemini must NOT be a decorative chatbot.

Use Gemini as the reasoning and orchestration layer.

Potential responsibilities:

- Interpret structured forecast results
- Explain stock-out risks
- Generate emergency situation briefs
- Compare scenarios
- Explain redistribution recommendations
- Invoke backend functions/tools
- Answer questions about the healthcare network based on retrieved structured data
- Produce administrator-facing summaries

Prefer:

- Structured JSON outputs
- Function/tool calling
- Grounding Gemini responses in actual backend data

Never allow Gemini to invent current stock quantities.

---

# 4. CORE AI ARCHITECTURE

Follow this separation of responsibilities:

## Predictive ML

Responsible for:

- Demand forecasting
- Patient footfall forecasting
- Medicine consumption forecasting
- Resource demand prediction
- Potential stock-out timing

Gemini should NOT perform numerical forecasting itself.

Use an appropriate ML/time-series approach.

For the prototype, start with models that are reliable, explainable, fast to train and easy to demo.

Candidates:

- Gradient Boosting
- Random Forest
- XGBoost if dependency is acceptable
- Prophet if appropriate
- Scikit-learn regression/time-series features

Do not unnecessarily build an enormous deep-learning model just to sound advanced.

---

## Risk Engine

Use deterministic/business rules plus predictive outputs to calculate:

- Days of stock remaining
- Safety-stock violations
- Stock-out probability
- Bed-capacity risk
- Staff availability risk
- Facility-level resilience score
- District-level warning status

Statuses:

- HEALTHY
- WATCH
- AT_RISK
- CRITICAL

Ensure the logic is transparent and explainable.

---

## Optimization Engine

Use:

**Google OR-Tools**

Goal:

Calculate optimal resource redistribution across facilities within India, including intra-district, inter-district and permitted inter-state transfers.

Consider:

- Current stock
- Predicted demand
- Minimum safety stock
- Donor safety stock
- Distance
- Transfer quantity
- Urgency
- Lead time
- Medicine expiry where practical
- Transportation/resource constraints

Example result:

PHC-021 → PHC-014  
IV Fluid: 180 units

Reason:

PHC-014 has high stock-out risk within 48 hours while PHC-021 has sufficient excess stock after preserving its emergency reserve.

Optimization output should be structured and deterministic.

Gemini can then explain it.

---

# 5. FEDERATED LEARNING

Implement a small but genuine federated-learning demonstration.

Concept:

Each participating Indian state or regional node has its own local dataset/model. For a lightweight demo, use five Indian nodes, for example Maharashtra, Karnataka, Tamil Nadu, Uttar Pradesh and Assam. The wider platform must support every Indian state and union territory.

Raw operational records stay inside each Indian state or regional simulated node.

Only model parameters/updates are aggregated.

Implement a lightweight FedAvg-style workflow.

For example:

Local data
→ local training
→ model update
→ central aggregator
→ shared national model
→ updated model distributed back to participating Indian nodes

The UI should clearly show:

**Raw records shared: 0**

and illustrate that predictive knowledge is shared without centralising raw data.

Keep this prototype technically real but computationally lightweight.

Do not pretend that we are running an actual production interstate healthcare infrastructure network.

Clearly identify it as a demonstration/simulation.

---

# 6. DATA STRATEGY — VERY IMPORTANT

We have decided NOT to depend on live government hospital systems.

Use:

# Real public aggregate data + realistic synthetic operational data

This is intentional.

---

## Real / Publicly Sourced Data

Where practical, prepare adapters or documented download/import procedures for public sources such as:

### India

- MoHFW HMIS
- data.gov.in healthcare datasets
- Indian Public Health Standards / IPHS
- Essential Medicines Lists
- Aggregated facility/workforce information

### India-wide coverage and provenance

- Verified, dated state/UT and district reference data
- India-specific workforce, bed-capacity and facility aggregates
- Documented administrative changes and coverage gaps
- No foreign-country operational datasets or country-comparison module required

Do NOT fabricate government API endpoints.

If direct APIs are unavailable, create:

- documented CSV import support
- data adapters
- sample public-data snapshots

Record every external data source in:

`docs/data-sources.md`

Include:

- source name
- URL
- fields used
- date accessed
- whether it is real, derived or synthetic

---

# 7. SYNTHETIC DATA

Operational PHC-level data will largely be synthetic.

Generate realistic datasets such as:

- facilities
- medicine inventory
- stock transactions
- medicine consumption
- patient footfall
- bed occupancy
- staff attendance
- emergency events
- inter-facility transfers

Example folder:

data/
  official/
  generated/
  metadata/

backend/
  simulation/

scripts/
  generate_facilities.py
  generate_inventory.py
  generate_patient_demand.py
  generate_staff.py
  generate_beds.py
  generate_emergency_events.py

Synthetic operational data should NOT be simple random noise.

Model realistic relationships.

Example demand model:

Demand(t) =
baseline
+ weekly seasonality
+ annual/seasonal disease effect
+ population effect
+ trend
+ emergency effect
+ controlled noise

Example:

Normal footfall:
80 patients/day

Monday:
+15%

Sunday:
-30%

Monsoon dengue season:
fever-related cases increase

Emergency dengue event:
patient footfall +65%
IV-fluid demand increases
paracetamol consumption increases
bed occupancy increases

Medicine consumption must therefore be related to patient demand.

Avoid this type of fake implementation:

`random.randint(1, 500)`

without any underlying causal relationship.

---

# 8. MEDICINE INVENTORY MODEL

Every medicine/facility pair should support fields similar to:

- current stock
- opening stock
- units consumed
- units received
- reorder threshold
- safety stock
- average daily consumption
- forecast demand
- days of stock cover
- supplier/lead time where useful
- expiry batches where practical
- predicted stock-out date
- stock-out risk
- facility
- district

Example:

Facility:
PHC-MH-PUNE-0042

Medicine:
Paracetamol 500 mg

Current stock:
1260

Safety stock:
700

Average daily consumption:
110

Predicted 7-day demand:
945

Predicted stock-out risk:
82%

Estimated stock-out:
4.3 days

This should be synthetic demo data unless we have an explicit verified public source for the particular value.

---

# 9. PATIENT FOOTFALL

Patient demand should influence downstream resources.

Pipeline:

patient footfall
→ syndrome/disease mix
→ medicine demand
→ inventory depletion
→ predicted shortage
→ alert
→ redistribution recommendation

Example disease/syndrome buckets:

- fever
- respiratory illness
- diarrhoeal disease
- injury
- maternal health
- general medicine
- other

Do NOT attempt individual patient diagnosis.

This is operational healthcare-resource forecasting.

---

# 10. BEDS

Model:

- total beds
- available beds
- occupied beds
- reserved/emergency beds
- expected discharges
- predicted occupancy

Facility types can have different capacities.

Example:

PHC
12 beds

CHC
30 beds

District hospital
250 beds

Values in the demo should be synthetic unless grounded in verified public facility-level information.

---

# 11. PERSONNEL

Do NOT use real employee names.

Use anonymised identifiers.

Example:

STAFF-IN-MH-00382

Role:
Medical Officer

Facility:
IN-MH-PUNE-041

Scheduled:
Yes

Present:
Yes

Shift:
09:00–17:00

Possible metrics:

- scheduled staff
- present staff
- doctor coverage
- nurse coverage
- attendance %
- staffing risk

No personally identifiable health or employee information.

---

# 12. PRIVACY AND DATA ETHICS

The system must be explicitly privacy-conscious.

Rules:

- No real patient names
- No Aadhaar numbers
- No personal medical records
- No actual sensitive patient-level data
- No real employee personally identifying information
- Clearly mark synthetic operational data
- Explain federated-learning privacy advantages accurately
- Never claim absolute privacy/security guarantees

Add a UI info panel:

“Prototype Data Notice”

Suggested wording:

“This prototype uses synthetic facility-level operational data calibrated using publicly available aggregate health statistics. No patient-identifiable information is used.”

---

# 13. MAIN APPLICATION MODULES

Build these modules:

## A. National Command Centre

Display:

- network status
- facilities online
- healthy facilities
- at-risk facilities
- critical facilities
- medicine availability
- bed utilisation
- personnel availability
- active alerts
- map
- trends

---

## B. Facility Explorer

Allow drill-down:

India
→ State / Union Territory
→ District
→ Facility

Facility page should show:

- facility health score
- medicines
- beds
- patient demand
- staff
- alerts
- forecasts
- recommended actions

---

## C. Medicine & Supply Dashboard

Show:

- current inventory
- consumption
- days of stock cover
- shortage probability
- predicted depletion
- expiring stock
- redistribution opportunities

---

## D. Early Warning Centre

Show alerts such as:

- predicted medicine stock-out
- unusual patient-footfall spike
- bed-capacity pressure
- staff shortage
- emergency-risk event
- delayed supply

Each warning should have:

- severity
- predicted timing
- affected facility
- affected resource
- confidence
- explanation
- recommended action

---

## E. Emergency Simulator / Digital Twin

This is a key differentiator.

Allow scenarios such as:

- Dengue outbreak
- Influenza surge
- Flood disruption
- Medicine delivery delayed
- Facility unavailable
- Staff shortage

Controls should include:

- region
- severity
- duration

After simulation:

show before/after network conditions.

---

## F. Redistribution Planner

Visualise:

- shortage facility
- donor facilities
- resource
- transfer quantities
- route/distance if available
- donor safety-stock remaining
- resolved risk

Provide:

**Optimize Redistribution**

button.

Run OR-Tools.

Then allow:

**Explain with Gemini**

---

## G. Gemini Health Resilience Copilot

Examples:

“What are Maharashtra's biggest health-resource risks for the next seven days?”

“Which districts are likely to face IV-fluid shortages?”

“Explain why Pune District has moved to AT_RISK.”

“What should the emergency-response team prioritise?”

Gemini must use backend tools/data.

Do NOT let it provide individual medical diagnosis or treatment advice.

This is an administrative healthcare-resource assistant.

---

## H. India Federated Intelligence

Show Indian state or regional nodes.

Example demo UI:

Maharashtra
Karnataka
Tamil Nadu
Uttar Pradesh
Assam

Support adding all other Indian states and union territories through configuration.

Show:

- local dataset size
- local model metric
- current training round
- raw data transferred: 0
- model update sent
- shared national model performance

Allow:

**Run Federated Round**

Show model updates being aggregated.

---

# 14. FRONTEND DESIGN DIRECTION

Visual personality:

- modern
- premium
- trustworthy
- analytical
- government-command-centre quality
- healthcare-oriented
- polished
- minimal
- data-dense without feeling cluttered

Avoid:

- generic Bootstrap appearance
- huge gradients everywhere
- excessive animations
- childish healthcare imagery
- fake futuristic sci-fi interfaces

Potential navigation:

HealthNexus AI

Overview
Network Map
Facilities
Supply Chain
Forecasts
Early Warnings
Redistribution
Emergency Simulator
India Federation
AI Copilot
Data Sources
About

Provide desktop-first but fully responsive design.

---

# 15. ARCHITECTURE

Conceptual architecture:

Angular Frontend
        |
        v
FastAPI Backend
        |
        +-----------------------------+
        |                             |
        v                             v
Firestore                     Gemini 3.8 Flash
        |
        +------------------+
        |                  |
        v                  v
Forecasting Engine     Risk Engine
        |
        v
OR-Tools Optimization
        |
        v
Redistribution Plan

Separate federated-learning service/module:

Indian State / Regional Nodes
        |
        v
Local Training
        |
        v
FedAvg Aggregator
        |
        v
Shared National Forecast Model

Deployment target:

Frontend:
Firebase Hosting

Backend:
Google Cloud Run

Database:
Firestore

AI:
Gemini API

---

# 16. REPOSITORY STRUCTURE

Use a clean monorepo such as:

healthnexus-ai/
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── forecasting/
│   │   ├── optimization/
│   │   ├── federation/
│   │   ├── simulation/
│   │   └── ai/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   ├── official/
│   ├── generated/
│   └── metadata/
│
├── scripts/
│
├── docs/
│   ├── architecture.md
│   ├── data-sources.md
│   ├── model-card.md
│   ├── api.md
│   └── demo-script.md
│
├── .env.example
├── docker-compose.yml
├── README.md
└── LICENSE

Adjust only when technically justified.

---

# 17. GOOGLE TECHNOLOGY REQUIREMENT

This is a Google hackathon.

The finished project should genuinely integrate Google technology.

Prioritise:

- Gemini 3.8 Flash API
- Firebase / Firestore
- Firebase Hosting
- Google Cloud Run
- Google OR-Tools

Google AI Studio may be used for genuinely testing/refining Gemini prompts, but the application itself should call the Gemini API.

Do not falsely claim that the entire project was developed in Google AI Studio.

Document the Google technology integration clearly in the README and architecture documentation.

---

# 18. COST CONSTRAINT

Prefer:

- free tiers
- open-source libraries
- locally generated synthetic data
- lightweight ML
- minimal cloud consumption

Do not introduce paid third-party APIs unless absolutely necessary.

If a feature requires money, provide a free alternative first.

---

# 19. SECURITY

Follow proper practices from the beginning:

- `.env`
- `.env.example`
- no committed API keys
- validate backend inputs
- CORS configuration
- secure Firebase setup
- proper exception handling
- rate-limit Gemini endpoints where appropriate
- sanitise tool inputs
- keep secrets server-side

The Gemini API key must never be exposed directly in the Angular frontend.

---

# 20. README REQUIREMENTS

The final README must eventually contain:

- project overview
- problem statement
- solution
- architecture diagram
- Google technologies used
- feature list
- screenshots
- local setup
- environment variables
- frontend commands
- backend commands
- synthetic-data generation
- ML training
- federated-learning demo
- emergency-simulation demo
- deployment steps
- data sources
- privacy/data disclaimer
- limitations
- future roadmap

---

# 21. HACKATHON SUBMISSION OUTPUTS

We will ultimately need:

1. Working application
2. Public GitHub repository
3. Running instructions
4. Architecture overview
5. Google technology integration explanation
6. Project pitch deck
7. Demo video/script
8. Data-source documentation

Structure the project so these can be generated easily later.

---

# 22. IMPORTANT ENGINEERING RULES

Do NOT:

- create fake government APIs
- pretend synthetic data is live government data
- expose secrets
- hardcode Gemini responses
- make Gemini responsible for raw numerical forecasting
- make the emergency simulator simply switch cards from green to red
- create dummy buttons that do nothing
- overengineer with dozens of microservices
- introduce unnecessary blockchain
- create fake AI features
- implement patient diagnosis
- use actual sensitive patient information

Do:

- keep components modular
- use typed schemas
- write useful comments
- add tests for critical logic
- keep algorithms explainable
- ensure generated datasets have internal relationships
- keep the demo fast
- ensure all major buttons actually work
- make every AI feature technically defensible

---

# 23. HOW I WANT YOU TO WORK

Do not only give me an architecture proposal.

**Start building the project.**

First inspect the existing workspace.

If the workspace is empty, initialize the complete `healthnexus-ai` monorepo.

Before writing each major component, inspect relevant files so you do not duplicate architecture.

Work incrementally and keep the project runnable.

Use small logical commits if Git is available.

When you discover a missing requirement or architectural conflict, solve it in the most sensible way instead of repeatedly stopping to ask me obvious implementation questions.

Do not spend the entire response planning.

Begin implementation.

---

# 24. IMPLEMENTATION ORDER

Use approximately this order:

## Phase 1 — Foundation

Create:

- monorepo
- Angular frontend
- FastAPI backend
- environment configuration
- shared models
- base navigation
- application layout
- health endpoint
- frontend/backend connectivity
- Firestore abstraction
- local mock-data fallback

The application must run at the end of Phase 1.

---

## Phase 2 — Synthetic Health Network

Build realistic generators for:

- national configuration (India only)
- states and union territories
- districts
- facilities
- medicine catalogue
- inventory
- patient footfall
- bed occupancy
- staff attendance

Seed enough data to make the dashboard meaningful.

Represent every Indian state and union territory from the initial synthetic network milestone. Keep the facility sample lightweight, label incomplete district coverage, and support documented imports of the complete district registry. Maharashtra/Pune remains one drill-down and emergency example, not the product boundary. Do not build foreign-country nodes or a country selector.

---

## Phase 3 — National Dashboard

Implement:

- KPI cards
- facility status
- charts
- district trends
- alerts
- map or geographic visualisation
- facility drill-down

---

## Phase 4 — Forecasting

Build:

- feature engineering
- training pipeline
- evaluation
- saved model
- forecast API
- forecast visualisation

Show at least:

- patient demand forecast
- medicine demand forecast
- predicted stock-out timing

---

## Phase 5 — Risk Engine

Create facility/resource risk scoring and early warnings.

---

## Phase 6 — Emergency Simulator

Implement realistic scenario propagation.

Start with:

**Dengue Surge**

The simulator must modify:

- patient demand
- medicine consumption
- beds
- risk
- forecast
- alerts

---

## Phase 7 — Redistribution Optimizer

Use Google OR-Tools to calculate resource transfers.

---

## Phase 8 — Gemini

Integrate Gemini 3.8 Flash through the backend.

Implement:

- structured outputs
- tool/function calling
- resilience brief
- alert explanation
- redistribution explanation
- administrative Q&A

Provide a deterministic mock/fallback mode when the API key is absent so local UI development remains possible.

---

## Phase 9 — Federated Learning

Add five simulated Indian state/regional nodes and a genuine lightweight FedAvg demonstration, using a node registry that can support every Indian state and union territory.

---

## Phase 10 — Polish

Improve:

- UX
- loading states
- responsiveness
- charts
- map
- animations
- error handling
- accessibility
- documentation
- test coverage

---

# 25. INITIAL SUCCESS CRITERIA

The first significant milestone should let me run the system locally and see:

- HealthNexus AI branding
- working Angular frontend
- working FastAPI backend
- seeded healthcare facilities
- national/state/district dashboard
- basic inventory
- patient footfall
- beds
- staff
- alerts
- frontend/backend communication

Then continue toward forecasting and simulation.

---

# 26. FINAL DEMO TARGET

The final demo should support this sequence:

1. Open HealthNexus AI.
2. Show India-wide network health, including all states and union territories.
3. Open Maharashtra.
4. Open Pune.
5. Show healthy PHCs.
6. Trigger Dengue Surge +65%.
7. Watch footfall increase.
8. Watch medicine consumption increase.
9. Watch facilities become AT_RISK/CRITICAL.
10. Show ML stock-out forecast.
11. Generate an early warning.
12. Run OR-Tools redistribution.
13. Display donor → receiver transfers.
14. Ask Gemini to explain the response plan.
15. Open India Federation.
16. Run a federated-learning round.
17. Show “Raw records shared: 0”.
18. Show shared national model improvement.

The experience should make the key message obvious:

> **Predict shortages before they become crises. Coordinate resources before facilities fail. Share intelligence across India without sharing raw health data.**

Now inspect the workspace and **start implementing HealthNexus AI from Phase 1 immediately**.

Do not merely return another plan. Create the project, write the files, run/build/test what you create, fix errors, and continue until Phase 1 is fully working.
