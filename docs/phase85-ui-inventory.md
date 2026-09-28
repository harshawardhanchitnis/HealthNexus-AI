# Phase 8.5 — pre-edit UI inventory

Baseline commit: `919c4a1`. Existing `final-*.png` captures and Phase 8 browser evidence are preserved for comparison.

| Surface | Existing implementation | Redesign direction |
|---|---|---|
| Shell | 244px green/navy rail, three tall context rows, small metadata | Navy identity, compact labelled context, accessible mobile drawer, workflow navigation |
| Command Centre | Four current KPIs, separate warning paragraph, tile grid/trend/facility table | National resource hero, five-signal strip, actionable real forecast warnings, current/predicted distinction |
| Network/facility | Reused dashboard and actual histories, status/ledger/provenance detail | Refined table hierarchy, status semantics, readable current/projected sections |
| Forecast | Native SVG, observed demand, 80/95% bands, saved model metrics | Primary chart, blue baseline line, separate bands, keyboard-accessible exact point details |
| Warnings | Real priority queue, API severity/category/context filters, expandable drivers | Severity hierarchy, compact queue, supplied recommendations, context-preserving next actions |
| Digital Twin | Four backend scenario enums, form, paired projections and real warning output | Generic scenario library, demand/supply/workforce/facility cards, completed impact timeline |
| Planner | Genuine donor preview, solver/impact/cards, constraints and conservation | Six result quantities, honest partial/no-donor outcome, measured transfer-lane cards |
| Federation | Original saved five-node MLP run, actual round SVG/table, India degradation | Prominent measured overview, five-node parameter-only topology, precise country changes |
| Copilot | Explicit offline default, context, conversation, expandable evidence/trace | Analyst workspace; visible context/grounding without changing provider logic |
| Model/data/about | Real model tables, two public catalogs, limitations | Trust hierarchy, four provenance classes, separate experimental federation branch |

No chart or UI framework is added. Existing Angular, SVG charts, line icons and system fonts are reused. Async/empty/error states, semantic headings and internal table scroll already exist and will be refined. Engine/API/data/model/test files are locked; their 260-file starting hashes are stored privately in ignored artifacts. Live diagnostics are deferred until every redesign/regression gate passes and quota availability is verified.
