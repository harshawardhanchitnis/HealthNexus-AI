# Phase 8.5 — National Health Resilience Command Centre

The frontend redesign is complete. HealthNexus now presents a generic healthcare resource and supply-chain resilience platform: observe the network, forecast pressure, inspect warnings, stress-test disruptions and evaluate protected redistribution. Severe Pune dengue remains the flagship demand-surge preset rather than the product identity.

Baseline: commit `919c4a1`. [Pre-edit inventory](phase85-ui-inventory.md), [browser evidence](evaluation/phase85-browser.json), [regression gates](evaluation/phase85-regression.json) and [canonical engine verification](evaluation/phase85-demo.json). Original screenshots and experiment reports are preserved.

## Design system

The shared Sass presentation layer uses a deep navy navigation rail (`#0b2036`), restrained health-system blue (`#1e5fa8`), cool neutral background (`#f5f7fb`) and white panels. Critical red, warning orange, watch amber, stable green and scenario indigo remain distinct. Existing system fonts, consistent line icons, tabular KPI numerals, 14px panel corners, sparse shadows and compact labelled controls establish hierarchy without a new UI/chart dependency.

The reusable shell has a 232px desktop rail, compact utility/context bars, visible operational profile and prototype/provenance information. The mobile drawer is inert when closed, moves focus after rendering, wraps Tab, closes with Escape and returns focus to its trigger. The mobile context summary keeps geography and profile visible even when filters collapse. The guide highlights actual navigation and offers the next route; it does not manufacture completion state.

## Screen-by-screen changes

| Surface | Result and preserved behavior |
|---|---|
| Command Centre | National resource identity, Guided Pune Demo and Simulate Emergency actions, five KPIs including actual projected warnings, explicit public/simulated trust strip, actionable priority signals and an Observe → Forecast → Warn → Simulate → Optimize pipeline. Existing resource calculations, regional summaries and observed histories remain intact. |
| Network | Refined network intelligence hierarchy, compact context/filter controls, status semantics, observed trends and readable facility table. Geography/profile query context is preserved. |
| Facilities and detail | Consistent operational tables, sticky headers, status badges, current and predictive sections, medicine ledgers, bed/workforce facts, actual history and provenance. Existing search, pagination and drill-down remain functional. |
| Supply | Resource-specific inventory, status and units retain their existing source values in the shared table/panel system. No invented inventory trends or reserve calculations. |
| Forecast Explorer | Actual facility name, prominent baseline chart, distinct observed/baseline/80%/95% styling and a keyboard-accessible point readout. Model/origin/units and exact tabular fallback remain available. Existing projections and chart coordinates are unchanged. |
| Early Warning Centre | Real severity filter chips and priority queue; expanded drivers and backend-supplied next steps. Facility, baseline forecast and redistribution links retain geography/profile/scenario context. No new warning rules or recommendations. |
| Emergency Digital Twin | A functional Scenario Library exposes Demand Surge · Dengue Surge, Supply Disruption · Delivery Delay, Workforce · Staff Shortage and Infrastructure · Facility Disruption. All four cards configure existing supported types. Common baseline → operational shock → impact → warning → response language, paired KPIs and completed execution steps use actual results. The uncertainty count is taken from the returned simulation, not a fake loading animation. |
| Safe Resource Redistribution | Six actual plan KPIs separate requirement, safe supply, transferred accounting items and remaining deficit. Positive partial relief and a protected zero-donor outcome have distinct honest callouts. Actual transfer-lane cards show donor → receiver, resource quantity/unit, distance and protected reserve. Constraints and detailed impact/conservation are progressively disclosed; preview, OR-Tools and greedy behavior remain unchanged. |
| Resilience Copilot | Analyst conversation plus context/evidence sidebar; actual model, fallback, provider trace and evidence remain visible. Explicit OFFLINE deterministic summaries stay distinct from Gemini. Provider acceptance is not implied by a polished UI. Prompts, tools, schema, grounding and production failover are unchanged. |
| Federated Intelligence | Five country parameter nodes feed FedAvg/global model; actual round progression and country comparisons are prominent. Original saved run loads without retraining. India’s `8.9496% → 8.9511%` WAPE and `+0.0015` percentage-point degradation are visible in amber. Optional genuine training controls remain available but were not activated. |
| Model Performance | Operational forecasting is clearly distinguished from the separate federated experiment. WAPE remains an error metric, never converted into “accuracy.” |
| Data Sources | Four provenance categories — Official Public Data, Calibrated Simulation, Model-Based Forecast and Scenario Projection — lead into existing publisher/year/catalogue evidence. No simulated facility stock is presented as government inventory. |
| About | Generic resource decision-support positioning and architecture explain the common operational pipeline and existing privacy/scope limitations. |

## First-screen hierarchy and scenario storytelling

The Command Centre first establishes the product, current geography/profile, network condition, projected warning signal and next action. Dengue appears through the guide or Scenario Library, not the national headline. The guide uses “Stress-test” as the operational step and retains the reproducible severe dengue story.

Scenario output compares the immutable baseline with the selected shock, then shows projected impacts and actual warnings. Completion markers appear only once a result exists. All four supported scenario families were run through the production UI without altering backend definitions, algorithms or canonical parameters.

## Locked operational outcomes

Both plans were independently reproduced by the existing engines and exercised through the browser, with district donor scope and the existing severe 14-day Pune dengue preset.

| Measure | Redistribution-ready | Constrained |
|---|---:|---:|
| Receiver target before | 41,763 | 30,230 |
| Safe donor capacity | 17,745 | 0 |
| Accounting items transferred | 15,679 | 0 |
| Transfer lanes | 10 | 0 |
| Unresolved target | 26,084 | 30,230 |
| Donor reserve violations / new donor risks | 0 / 0 | 0 / 0 |
| Solver status | OPTIMAL | OPTIMAL |

Ready receiver critical medicine warnings improve **7 → 0**, while maximum individual stock-out risk remains **100% → 100%**. Expected unmet demand decreases **27,655.2181 → 17,378.1980**. The outcome explicitly remains partial: 37.5% of target accounting items resolved. OR-Tools and greedy tie in this district case. Mixed medicine units are accounting totals, not interchangeable tablets/bags/sachets. The constrained result remains a valid optimal decision under reserve constraints, not a failed solver. Per-resource conservation and baseline/scenario immutability pass.

India operational held-out WAPE is unchanged: footfall **2.996932%**, pooled medicine demand **3.079865%**, admissions **3.344126%**.

## Accepted federation preserved

The original accepted run `fdbaaedb-773d-4b67-be50-ad406b130950` remains the source: **5 logical nodes, 5 rounds, 1 local epoch, 417 parameters, 0 raw training rows shared, 4.8011 seconds, 614,235 logical boundary bytes**. Its saved report is byte-identical to the original Phase 7 evidence. Global validation WAPE remains **100 → 15.95 → 9.97 → 9.51 → 9.37 → 9.33%**; global test WAPE **8.9472%**.

| Country | Local-only WAPE | Federated WAPE |
|---|---:|---:|
| India | 8.9496% | 8.9511% |
| Brazil | 26.7746% | 8.7975% |
| Russia | 28.3658% | 9.0454% |
| China | 28.3849% | 8.9523% |
| South Africa | 27.1055% | 8.8088% |

No accepted federation run was retrained or retimed. Regression tests use their existing temporary fixtures. The verifier reloads/evaluates the saved checkpoint, not a replacement experiment. These are five configured logical nodes with representative foreign facilities, not connected government systems or exhaustive BRICS coverage.

## Accessibility and responsive verification

**70 layout checks** cover 14 routes (including facility detail) at **1440×900, 1280×800, 1024×768, 768×1024 and 390×844**. There are **zero document-overflow failures, application alerts or captured console warnings/errors**. Wide tables scroll within their panels. Mobile geography/profile stays visible; priority warning signals lead the compact layout.

Keyboard checks cover drawer focus entry/Tab wrapping/Escape/focus return, closed-drawer inertness, skip-link focus and preserved query context, warning filters/drill-down, guided Next and exact forecast-point readouts. Labels, semantic headings, visible focus and reduced-motion handling remain in place. This is interactive accessibility review, not WCAG certification or a browser automation test suite.

Final screenshot review found sidebar selectors leaking into guided navigation. They are now scoped to the sidebar. Five additional guide checks confirm a compact horizontal step rail at every target viewport, no document overflow and working profile-preserving Next navigation. Final desktop/mobile guide captures show loaded data rather than an intermediate loading state.

Actual browser workflows cover positive and constrained planning, all four scenario families, warning navigation, facility detail, saved federation and explicit offline Copilot with authoritative local tools/evidence. **Zero live Gemini requests occurred during UI work or browser testing.**

## Build, regression and Docker

| Check | Measured result |
|---|---|
| Backend regression | **340 passed in 55.88 seconds**, one existing Starlette/AnyIO deprecation warning |
| Python compilation | PASS: backend and scripts |
| Dependency checks | Windows and Docker backend `pip check` PASS; production npm audit **0 known vulnerabilities** |
| Strict TypeScript | PASS |
| Angular production | PASS, **0 build warnings**, **0 new dependencies** |
| Docker | Production frontend rebuilt; unchanged backend healthy; liveness/readiness, all ten country/profile overview partitions, saved federation and SPA deep link PASS |
| Protected source/data/artifact/evidence files before matrix | **260 unchanged**, including `.env` and the historical 12-request ledger |

| Initial frontend bundle | Before | After | Change |
|---|---:|---:|---:|
| Raw | 370.25 kB | 387.99 kB | +17.74 kB |
| Estimated transfer | 101.28 kB | 104.69 kB | +3.41 kB |

These are Angular build measurements, not an invented runtime performance benchmark. Local Docker preview is available on frontend port `14200`, backend `18000`; no cloud deployment occurred.

## Security and scope

No backend source/test, dataset, stock snapshot, model weights, warning/optimization policy, Gemini implementation or accepted experiment evidence changed. `.env` is ignored/untracked and unchanged. The same existing key/project is used only by the explicitly authorized final diagnostic. No key rotation, billing change, additional project/account, deployment or pitch deck was performed. Public reports omit credentials, headers, environment contents and secret fingerprints.

## Gemini live availability matrix

The final diagnostic ran only after all preceding gates passed. It tested the exact production model order with **two independent fresh minimal smoke requests per model**, **no per-attempt failover**, **no retry**, **medium thinking**, a global **ten-new-request ceiling** and conservative pacing. Existing server-prefetched authoritative reads, prompt, structured schema and evidence validator were reused. The production orchestration was not modified.

The 12 historical local requests are retained; the additional ten-request allowance is verifier-only and increments that same ledger. User-confirmed Google AI Studio Free-tier headroom is separate from local accounting. No exact provider reset timestamp was supplied or inferred. Provider availability and accepted grounded smoke responses are reported separately in [sanitized matrix evidence](evaluation/phase85-gemini-availability.json).

<!-- GEMINI_MATRIX_RESULTS -->
| Model | Attempt 1 | Attempt 2 | Provider available | Schema valid | Accepted grounded | Observed provider latency; median | Provider error |
|---|---|---|---:|---:|---:|---|---|
| `gemini-3.8-flash` | 503_HIGH_DEMAND | 503_HIGH_DEMAND | 0/2 | 0/0 | 0/2 | 4.457s, 13.692s; 9.074s | provider_unavailable |
| `gemini-3.7-flash` | 503_HIGH_DEMAND | 503_HIGH_DEMAND | 0/2 | 0/0 | 0/2 | 4.799s, 6.528s; 5.663s | provider_unavailable |
| `gemini-3.6-flash` | GROUNDING_FAILURE | 503_HIGH_DEMAND | 1/2 | 1/1 | 0/2 | 15.155s, 15.304s; 15.230s | provider_unavailable, unsupported_number |
| `gemini-3.5-flash` | 503_HIGH_DEMAND | 503_HIGH_DEMAND | 0/2 | 0/0 | 0/2 | 3.981s, 3.815s; 3.898s | provider_unavailable |
| `gemini-3.5-flash-lite` | GROUNDING_FAILURE | GROUNDING_FAILURE | 2/2 | 2/2 | 0/2 | 13.525s, 12.181s; 12.853s | unsupported_number |

Actual additional provider requests: **10**. Requests per model: `gemini-3.8-flash` **2**, `gemini-3.7-flash` **2**, `gemini-3.6-flash` **2**, `gemini-3.5-flash` **2**, `gemini-3.5-flash-lite` **2**. The ignored ledger retains its **12** historical requests and now records **22** total. No reset or deletion occurred.

**Provider-available models:** gemini-3.6-flash, gemini-3.5-flash-lite. **Models with accepted grounded smoke:** none. **Models returning 503:** gemini-3.8-flash, gemini-3.7-flash, gemini-3.6-flash, gemini-3.5-flash. **Rate-limit failures:** none.

HTTP 200 availability and accepted schema/evidence grounding are counted separately above. Only models in the accepted column served a verified grounded smoke answer. Medium thinking was used for every candidate. Token usage is reported only where supplied; no remaining quota is fabricated. Provider Retry-After values: 30 seconds, honored before later sends. Provider latency excludes pacing and local tool preparation; total attempt timings and local tool timings remain in the JSON.

Schema counts use successful provider responses as the denominator; `0/0` means not evaluated, not a schema failure. A `GROUNDING_FAILURE` records the unchanged validator’s rejection of the cited claim; no unsupported answer is accepted or substituted with an offline response.

All **20 local prefetch calls** (`get_network_summary` and `get_warning_summary` for each attempt) succeeded. All **3 HTTP 200 responses** passed the existing structured schema, then were rejected with `unsupported_number`. No model served an accepted live answer. This is evidence that availability has partially recovered while grounding acceptance remains unresolved; the validator and production configuration were not weakened or changed to obtain a pass.

**Full Phase 6 acceptance remains pending.** The diagnostic stopped after this matrix: no full dengue, constrained, provenance, follow-up or browser Gemini request followed it. Production model stickiness, handoff, grounding and the five-model fallback chain remain untouched. This availability test does not establish full native function-calling workflow compatibility. The deterministic hackathon demo remains available with explicitly labelled offline summaries.

[Final preservation/security check](evaluation/phase85-security.json) passes: **259 protected files unchanged**, including `.env`; the only permitted protected-file change is the appended ignored verifier ledger. No billing, key/project/account or deployment change occurred.
<!-- END_GEMINI_MATRIX_RESULTS -->

## Screenshots and practical limits

[Current desktop/mobile gallery](screenshots/README.md) covers every major route, facility detail, chart interaction, positive/constrained plans, offline Copilot and saved federation. Captures are unedited actual viewports. Full-page stitching was avoided because the exporter duplicated sections; no pixels or values were altered to conceal results. Original Phase 8 captures remain dated comparison evidence.

Two mobile exports showed a stale scaled viewport during file review. They were recaptured after loading the correct 390×844 layout and checking the rendered dimensions. This artifact correction changed no UI code, engine state, Gemini workflow or provider request count.

No map functionality, unsupported warning-history trend or stock sparklines were invented. Existing observed histories and actual projected warning counts are used. Actual transfer-lane cards were chosen instead of introducing a risky graph dependency. Forecast tooltips show server values using the existing SVG chart. Unavailable live Gemini behavior and clinical/logistics validity remain explicit limitations.

## Product assessment

The redesigned product is a **generic National Health Resilience Command Centre** with a reproducible severe Pune dengue flagship demonstration. Its national resource overview, four-family Scenario Library and scenario-agnostic redistribution flow make that distinction visible. No new development phase, deployment or full Gemini acceptance run is started by this work.
