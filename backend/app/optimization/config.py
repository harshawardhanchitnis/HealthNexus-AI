from pydantic import BaseModel


class Policy(BaseModel):
    version: str = "redistribution-v1"
    horizon: int = 14
    reserve_multiplier: float = 1.0
    reserve_buffer_units: int = 1
    minimum_current_cover_days: int = 7
    protected_paths: str = "all 500 paired paths and point forecast, every day"
    shortage_base_weight: int = 100
    severity_weight: int = 100
    urgency_weight: int = 10
    probability_weight: int = 100
    priority_weight: int = 1
    critical_shortage_weight: int = 1
    distance_weight: int = 1
    donor_risk_weight: int = 100
    cross_district_penalty: int = 1000
    cross_state_penalty: int = 10000
    transfer_count_penalty: int = 100
    time_limit_seconds: float = 10.0
    workers: int = 1
    seed: int = 42
    max_runs: int = 30


POLICY = Policy()
LIMITATIONS = [
    "Simulated operational facilities and inventories; emergency assumptions remain unvalidated.",
    "Straight-line geographic distance used for prototype optimization; not road travel distance.",
    "Transfers are assumed to arrive before day 1, with no transit loss, vehicle limits or execution provider. Review transport feasibility before acting.",
    "Donors retain reserve throughout all 14 days under every one of the 500 sampled demand paths, and at least 7 days of current point-demand cover. This is not a guarantee against unsampled demand or delayed receipts.",
    "Policy weights are prototype assumptions. Decision support only, not an automatic order. No international physical transfers.",
    "Plans are independent alternatives, not commitments; no plan is executed or stacked on another. Process-local storage is lost on server restart.",
]
