# Scope and milestone boundaries

HealthNexus AI is a real-data-backed healthcare resilience prototype. Public aggregates support operational simulation now; predictive models, domestic optimization and federated learning form the later product.

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

Country-scoped API and storage; India navigation and original tests; public-source ingestion and offline caches; provenance; aggregate calibration; causal demand, stock and occupancy histories; rule-based alerts; Data Sources and BRICS node pages. Foreign nodes are extensible representative samples.

## Next phases

Phase 3 should build temporal forecasting datasets, transparent demand baselines, stockout-aware targets, held-out evaluation and uncertainty displays. Then add emergency scenarios and domestic redistribution with donor reserves and audit trails. Gemini, OR-Tools and real FedAvg training are not implemented in Phase 2.

Each future learning node owns its local training data. Only model updates and permitted aggregate evaluation statistics go to the federation coordinator; raw operational records must not be pooled for that demonstration. Updates alone do not guarantee privacy: authentication, leakage testing and privacy controls require separate engineering.

Physical resources move domestically. Model learning may cross borders. There are no automatic international medicine transfers. Country selectors and local filesystem partitions are not production sovereignty or security enforcement.
