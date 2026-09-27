from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Status(str, Enum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class Region(BaseModel):
    id: str
    name: str
    kind: Literal["state", "union_territory"]
    zone: str
    latitude: float
    longitude: float


class District(BaseModel):
    id: str
    name: str
    state_id: str


class DailyActivity(BaseModel):
    date: date
    footfall: int = Field(ge=0)
    medicine_units: int = Field(ge=0)
    occupied_beds: int = Field(ge=0)


class InventoryItem(BaseModel):
    medicine_id: str
    name: str
    unit: str
    opening_stock: int = Field(ge=0)
    units_consumed: int = Field(ge=0)
    units_received: int = Field(ge=0)
    current_stock: int = Field(ge=0)
    safety_stock: int = Field(ge=0)
    average_daily_consumption: float = Field(gt=0)
    days_of_cover: float = Field(ge=0)
    status: Status

    @model_validator(mode="after")
    def stock_balance(self):
        if self.current_stock != self.opening_stock + self.units_received - self.units_consumed:
            raise ValueError("Inventory balance does not reconcile")
        return self


class Beds(BaseModel):
    total: int = Field(gt=0)
    occupied: int = Field(ge=0)
    reserved: int = Field(ge=0)
    available: int = Field(ge=0)

    @model_validator(mode="after")
    def capacity_balance(self):
        if self.occupied + self.reserved + self.available != self.total:
            raise ValueError("Bed counts do not reconcile")
        return self


class Staff(BaseModel):
    scheduled: int = Field(gt=0)
    present: int = Field(ge=0)
    doctors_present: int = Field(ge=0)
    nurses_present: int = Field(ge=0)

    @model_validator(mode="after")
    def attendance_balance(self):
        if self.present > self.scheduled:
            raise ValueError("Present staff exceeds scheduled staff")
        if self.doctors_present + self.nurses_present > self.present:
            raise ValueError("Role totals exceed staff present")
        return self


class Facility(BaseModel):
    id: str
    name: str
    type: Literal["PHC", "CHC", "District Hospital"]
    state_id: str
    district_id: str
    district_name: str
    latitude: float
    longitude: float
    status: Status
    resilience_score: int = Field(ge=0, le=100)
    footfall_today: int = Field(ge=0)
    beds: Beds
    staff: Staff
    inventory: list[InventoryItem]
    history: list[DailyActivity]
    synthetic: Literal[True] = True


class Alert(BaseModel):
    id: str
    facility_id: str
    facility_name: str
    district_id: str
    state_id: str
    severity: Status
    resource: str
    title: str
    explanation: str
    recommended_action: str
    method: Literal["deterministic_threshold"] = "deterministic_threshold"


class Snapshot(BaseModel):
    schema_version: Literal[1] = 1
    country: Literal["IN"] = "IN"
    as_of: date
    seed: int
    regions: list[Region]
    districts: list[District]
    facilities: list[Facility]
    alerts: list[Alert]

