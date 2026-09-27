from datetime import date, datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field
from app.models.provenance import CountryCode


class Severity(str, Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class WarningType(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    SAFETY_STOCK_BREACH = "SAFETY_STOCK_BREACH"
    PREDICTED_STOCKOUT = "PREDICTED_STOCKOUT"
    HIGH_STOCKOUT_RISK = "HIGH_STOCKOUT_RISK"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    PATIENT_SURGE = "PATIENT_SURGE"
    ABNORMAL_FOOTFALL = "ABNORMAL_FOOTFALL"
    HIGH_BED_OCCUPANCY = "HIGH_BED_OCCUPANCY"
    PREDICTED_BED_CAPACITY_BREACH = "PREDICTED_BED_CAPACITY_BREACH"
    STAFF_SHORTAGE = "STAFF_SHORTAGE"
    HIGH_WORKLOAD = "HIGH_WORKLOAD"
    FACILITY_DISRUPTION = "FACILITY_DISRUPTION"
    EMERGENCY_ESCALATION = "EMERGENCY_ESCALATION"


class Factor(BaseModel):
    factor: str
    value: float | str
    description: str


class Warning(BaseModel):
    warning_id: str
    warning_type: WarningType
    category: Literal["medicine", "demand", "beds", "personnel", "emergency"]
    severity: Severity
    country_id: CountryCode
    state_id: str
    district_id: str | None
    facility_id: str
    facility_name: str
    resource_id: str | None = None
    generated_at: datetime
    forecast_origin: date
    horizon: int = 14
    current_value: float | None
    threshold: float | None
    predicted_value: float | None
    estimated_event_date: date | None = None
    model_based_probability: float | None = Field(None, ge=0, le=1)
    baseline_or_scenario: Literal["baseline", "scenario"]
    scenario_id: str | None
    explanation_factors: list[Factor]
    recommended_next_step: str = "Review operational assumptions and local capacity; no automated action has been taken."
    provenance: dict[str, str | bool | int]
    model_version: str
    priority_score: float
    baseline_severity: Severity | None = None
    transition: Literal["baseline", "new", "unchanged", "worsened", "improved"] = "baseline"


class WarningSummary(BaseModel):
    total: int
    counts: dict[str, int]
    facilities_affected: int
    medicines_at_risk: int
    bed_warnings: int
    staff_warnings: int
    by_country: dict[str, dict[str, int]]
    by_region: dict[str, dict[str, int]]
    by_district: dict[str, dict[str, int]]
    by_facility: dict[str, dict[str, int]]


class WarningList(BaseModel):
    items: list[Warning]
    summary: WarningSummary
