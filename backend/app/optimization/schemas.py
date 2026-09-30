from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.provenance import CountryCode
from app.scenarios.models import FacilityProjection
from app.warnings.models import WarningList

Resource = Literal["PCM", "IVF", "ORS", "AMX", "IFA"]
Status = Literal["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"]


class RedistributionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: Literal["constrained", "redistribution-ready"] = "constrained"
    country_id: CountryCode = "IN"
    scenario_id: str | None = None
    state_id: str | None = None
    district_id: str | None = None
    scope: Literal["district", "cross_district", "state", "national"] = "national"
    resources: list[Resource] = Field(default_factory=lambda: ["PCM", "IVF", "ORS", "AMX", "IFA"], min_length=1, max_length=5)
    horizon: Literal[14] = 14
    time_limit_seconds: float = Field(default=10, ge=.01, le=30)

    @model_validator(mode="after")
    def valid(self):
        if len(set(self.resources)) != len(self.resources):
            raise ValueError("Duplicate resource")
        if self.scope == "district" and not self.district_id:
            raise ValueError("District scope requires district_id")
        if self.scope == "state" and not self.state_id:
            raise ValueError("State scope requires state_id")
        if self.scope == "cross_district" and (self.country_id != "IN" or not self.state_id or not self.district_id):
            raise ValueError("Cross-district scope requires India and a receiver state/district")
        return self


class Candidate(BaseModel):
    facility_id: str
    facility_name: str
    country_id: CountryCode
    state_id: str
    district_id: str | None
    resource_id: Resource
    unit: str
    current_stock: int
    protected_reserve: int
    safe_surplus: int = 0
    protected_minimum_stock: float
    reserve_after_max_donation: float
    deficit: int = 0
    expected_unmet: float
    depletion_date: date | None
    safety_breach_date: date | None
    risk: dict[str, float]
    severity: str
    priority: float
    critical: bool
    shortage_weight: int
    nearest_receiver_distance_km: float | None = None


class Edge(BaseModel):
    donor: int
    receiver: int
    distance_km: float
    geographic_penalty: int
    unit_cost: int


class Preview(BaseModel):
    diagnostics: dict[str, float] = Field(default_factory=dict)
    request: RedistributionRequest
    snapshot_id: str
    scenario_snapshot_id: str | None
    scenario_facility_ids: list[str] = Field(default_factory=list)
    origin: date
    config_version: str
    model_version: str
    receivers: list[Candidate]
    donors: list[Candidate]
    edges: list[Edge]
    total_deficit: int
    safe_capacity: int
    capacity_by_resource: dict[str, int]
    deficit_by_resource: dict[str, int]
    limitations: list[str]


class SolverStage(BaseModel):
    name: str
    status: Status
    objective: float | None
    best_bound: float | None
    seconds: float


class SolverMetadata(BaseModel):
    construction_seconds: float = 0.
    engine: str
    version: str
    status: Status
    termination: str
    stages: list[SolverStage]
    objective: list[int] | None
    time_limit_seconds: float
    elapsed_seconds: float
    variables: int
    constraints: int


class Metrics(BaseModel):
    target_deficit: int
    expected_unmet: float
    critical_resource_warnings: int
    facilities_at_risk: int
    max_stockout_risk: float


class Impact(BaseModel):
    before: Metrics
    after: Metrics
    shortage_units_resolved: int
    percent_deficit_resolved: float
    critical_deficits_resolved: int
    critical_deficits_total: int
    facilities_protected: int
    donor_facilities_used: int
    transfer_count: int
    transferred_units: int
    distance_km: float
    distance_weighted_units: float
    donor_safety_violations: int
    new_donor_risks: int
    unresolved: dict[str, int]
    conservation: dict[str, dict[str, int]]


class Transfer(BaseModel):
    transfer_id: str
    optimizer_run_id: str
    donor_id: str
    donor_name: str
    donor_state_id: str | None = None
    donor_district_id: str | None = None
    receiver_state_id: str | None = None
    receiver_district_id: str | None = None
    cross_district: bool = False
    plan_mode: Literal["advisory"] = "advisory"
    receiver_id: str
    receiver_name: str
    resource_id: Resource
    unit: str
    quantity: int
    distance_km: float
    donor_stock_before: int
    donor_stock_after: int
    donor_protected_reserve: int
    donor_projected_stock_after: float
    donor_protected_minimum_after: float
    donor_risk_before: dict[str, float]
    donor_risk_after: dict[str, float]
    receiver_deficit_before: int
    receiver_deficit_after: int
    receiver_warning_before: str
    receiver_warning_after: str
    receiver_risk_before: dict[str, float]
    receiver_risk_after: dict[str, float]
    rationale: dict[str, str | float | int]
    optimization_status: Status
    objective_contribution: dict[str, int]
    scenario_id: str | None
    provenance: dict[str, str]


class PlanResult(BaseModel):
    geography: dict = Field(default_factory=dict)
    diagnostics: dict[str, float] = Field(default_factory=dict)
    run_id: str
    created_at: datetime
    preview: Preview
    solver: SolverMetadata
    transfers: list[Transfer]
    impact: Impact
    greedy: Impact
    greedy_transfers: list[Transfer]
    before: list[FacilityProjection]
    after: list[FacilityProjection]
    before_warnings: WarningList
    after_warnings: WarningList
    message: str
