# Scope and milestone boundaries

HealthNexus AI is a real-data-backed healthcare resilience prototype. Public aggregates support operational simulation, saved forecasting, emergency projections and domestic optimization. Phase 6 Gemini implementation is complete; live provider acceptance is pending due to Gemini service availability. Phase 7 adds genuine experimental FedAvg across five logical country nodes.

## Configured geography

| Node | Hierarchy and implemented coverage |
| --- | --- |
| India | Country → all 28 states and 8 UTs → 69 illustrative districts → 207 fictional facilities |
| Brazil | Country → São Paulo and Rio de Janeiro → 6 fictional facilities |
| Russia | Country → Moscow and Saint Petersburg → 6 fictional facilities |
| China | Country → Guangdong and Shanghai → 6 fictional facilities |
| South Africa | Country → Gauteng and Western Cape → 6 fictional facilities |

The five configured countries follow the hackathon brief; they are not an exhaustive statement of current BRICS membership. India's complete state/UT coverage does not imply a complete district or facility registry. Coordinates indicate illustrative locations; identifiers are internal, not official registry codes.

## Implemented

Country-scoped API and storage; India navigation and original tests; public-source ingestion and offline caches; provenance; aggregate calibration; causal 540-day histories; rule alerts; trained country-local demand/admissions forecasts; baseline comparison and chronological evaluation; residual intervals and stock-out intelligence; Forecasts, Model Performance, Data Sources and BRICS pages. Foreign nodes are extensible representative samples.

## Operational and collaborative learning

Phase 3 forecasting and Phase 4 **Early Warning Engine + Emergency Digital Twin** feed the Phase 5 **domestic OR-Tools Redistribution Planner**, with reserve protection, audit evidence and immutable paired stock simulations. Phase 5.5 preserves constrained Pune's zero-donor result and adds a separate reproducible redistribution-ready simulation with protected positive transfers. See [Phase 5.5 report](phase55-report.md). Phase 6 retains shared authoritative tools and availability failover; no live Gemini calls occur during Phase 7.

Each Phase 7 learning client loads only its country's existing historical footfall tables. Actual MLP parameter tensors are locally trained and averaged; only updates and aggregate metadata go to the aggregator. No raw operational training records are pooled. The global collaboration MLP is experimental and does not replace operational forecasting. Updates alone do not guarantee privacy: authentication, leakage testing, secure aggregation and differential privacy require separate engineering. See [federated learning](federated-learning.md).

Physical resources move domestically. Model learning may cross borders. There are no automatic international medicine transfers. Country selectors and local filesystem partitions are not production sovereignty or security enforcement.
