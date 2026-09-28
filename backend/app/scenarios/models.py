from datetime import date, datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.provenance import CountryCode
from app.forecasting.schemas import ForecastPoint, HistoryPoint, StockRisk, ForecastProvenance


class ScenarioType(str, Enum):
    DENGUE_SURGE = "DENGUE_SURGE"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    STAFF_SHORTAGE = "STAFF_SHORTAGE"
    FACILITY_DISRUPTION = "FACILITY_DISRUPTION"


class Parameters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    medicine_id: Literal["PCM", "IVF", "ORS", "AMX", "IFA"] | None = None
    delay_days: int | None = Field(None, ge=1, le=30)
    unavailable_fraction: float | None = Field(None, gt=0, le=1)
    capacity_reduction: float | None = Field(None, gt=0, le=1)


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_type: ScenarioType
    profile: Literal["constrained", "redistribution-ready"] = "constrained"
    country_id: CountryCode = "IN"
    state_id: str | None = None
    district_id: str | None = None
    facility_ids: list[str] = Field(default_factory=list, max_length=250)
    start_date: date | None = None
    duration: int = Field(14, ge=1, le=14)
    severity: Literal["moderate", "severe", "critical"] = "severe"
    seed: int = Field(42, ge=0, le=2147483647)
    parameters: Parameters = Field(default_factory=Parameters)

    @model_validator(mode="after")
    def parameter_scope(self):
        allowed = {ScenarioType.DENGUE_SURGE: set(), ScenarioType.DELIVERY_DELAY: {"medicine_id", "delay_days"},
            ScenarioType.STAFF_SHORTAGE: {"unavailable_fraction"}, ScenarioType.FACILITY_DISRUPTION: {"capacity_reduction"}}
        supplied = {k for k, v in self.parameters.model_dump().items() if v is not None}
        if supplied - allowed[self.scenario_type]:
            raise ValueError("Parameters do not apply to the selected scenario type")
        if len(self.facility_ids) != len(set(self.facility_ids)):
            raise ValueError("Duplicate facility IDs")
        return self


class ReceiptChange(BaseModel):
    resource_id: str
    ordered_at: date
    original_date: date
    projected_date: date
    quantity: int


class OperationDay(BaseModel):
    date: date
    footfall: float
    syndrome_counts: dict[str, float]
    admissions_requested: float
    admissions: float
    discharges: float
    opening_occupied: float
    occupied: float
    bed_capacity: float
    occupancy_ratio: float | None
    bed_overflow: float
    unmet_admissions: float
    scheduled_staff: int
    available_staff: float
    service_capacity: float
    served_patients: float
    unserved_patients: float
    workload_ratio: float | None


class ResourceProjection(BaseModel):
    resource_id: str
    name: str
    unit: str
    forecast: list[ForecastPoint]
    stockout: StockRisk
    requested_total: float
    unmet_total: float


class FacilityProjection(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    country_id: CountryCode
    state_id: str
    district_id: str | None
    history: list[HistoryPoint]
    footfall: list[ForecastPoint]
    resources: list[ResourceProjection]
    timeline: list[OperationDay]
    receipt_changes: list[ReceiptChange]
    provenance: ForecastProvenance
    source_models: dict[str, str]
    baseline_recent_daily_mean: float
    current_staff_fraction: float
    current_occupancy_ratio: float
    current_workload_ratio: float | None
    status: Literal["NORMAL", "INFO", "WATCH", "WARNING", "CRITICAL"] = "NORMAL"
    priority_score: float = 0


class Metrics(BaseModel):
    patient_demand: float
    admissions_requested: float
    unmet_admissions: float
    unserved_patients: float
    peak_bed_occupancy_percent: float | None
    peak_workload_ratio: float | None
    max_stockout_probability: float
    critical_facilities: int


class MetricDelta(BaseModel):
    baseline: float | None
    scenario: float | None
    absolute: float | None
    percent: float | None
    unit: str


class ResourceImpact(BaseModel):
    resource_id: str
    name: str
    unit: str
    demand: MetricDelta
    unmet_demand: MetricDelta
    max_stockout_risk: MetricDelta


class Outcome(BaseModel):
    metrics: Metrics
    facilities: list[FacilityProjection]


class ScenarioMetadata(BaseModel):
    scenario_id: str
    definition: ScenarioRequest
    created_at: datetime
    status: Literal["completed"] = "completed"
    baseline_snapshot_id: str
    origin: date
    config_version: str
    effective_parameters: dict[str, float | str]
    assumptions: list[str]
    data_status: Literal["simulated_operational_resilience"] = "simulated_operational_resilience"
