# Model and risk notes — Phase 1

No trained ML or generative model is deployed in this milestone. The chart is a synthetic 28-day history. Stock cover divides present inventory by trailing seven-day average use; it is not a probabilistic forecast. Alerts are explicitly tagged `deterministic_threshold`.

Synthetic generation models weekly/seasonal variation, facility size and bounded noise, but has not been fitted to Indian epidemiological or operational data. It is inappropriate for real-world resource decisions.

The later forecasting model card must describe data provenance, temporal validation, baseline comparisons, per-region metrics, uncertainty, failure cases and drift. The federation demo must use compatible parameterized models at Indian nodes and distinguish local versus national evaluation, raw records versus updates, and measured metric changes versus guaranteed improvement. Federated updates can leak information; no absolute privacy claims.
