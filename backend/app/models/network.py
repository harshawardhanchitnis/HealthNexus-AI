from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from app.models.provenance import CountryCode, Provenance


class Status(str, Enum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class Region(BaseModel):
    country_id: CountryCode = "IN"
    provenance_id: str = "geography-v1"
    id: str
    name: str
    kind: Literal["state", "union_territory", "province", "municipality", "federal_subject"]
    zone: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class District(BaseModel):
    country_id: CountryCode = "IN"
    provenance_id: str = "geography-v1"
    id: str
    name: str
    state_id: str


class DailyActivity(BaseModel):
    provenance_id: str = "synthetic-v1"
    date: date
    footfall: int = Field(ge=0)
    medicine_units: int = Field(ge=0)
    occupied_beds: int = Field(ge=0)
    previous_occupied: int | None = Field(default=None, ge=0)
    admissions: int = Field(default=0, ge=0)
    discharges: int = Field(default=0, ge=0)
    unmet_admissions: int = Field(default=0, ge=0)
    syndrome_counts: dict[str, int] = Field(default_factory=dict)
    total_beds: int | None = Field(default=None, gt=0)
    scheduled_staff: int | None = Field(default=None, gt=0)
    available_staff: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def activity_balance(self):
        if self.scheduled_staff is not None and (self.available_staff is None or self.available_staff > self.scheduled_staff):
            raise ValueError("Historical attendance exceeds scheduled staff")
        if self.previous_occupied is not None:
            if self.discharges > self.previous_occupied or self.occupied_beds != self.previous_occupied + self.admissions - self.discharges:
                raise ValueError("Admissions/discharges do not reconcile")
        if self.syndrome_counts and (min(self.syndrome_counts.values()) < 0 or sum(self.syndrome_counts.values()) != self.footfall):
            raise ValueError("Syndrome mix must partition patient footfall")
        return self


class StockDay(BaseModel):
    date: date
    opening: int = Field(ge=0)
    received: int = Field(ge=0)
    requested: int = Field(ge=0)
    consumed: int = Field(ge=0)
    unmet_demand: int = Field(ge=0)
    closing: int = Field(ge=0)
    transfers_received: int = Field(default=0, ge=0)
    transfers_sent: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    scheduled_receipts: int = Field(default=0, ge=0)
    delivery_delayed: bool = False

    @model_validator(mode="after")
    def conservation(self):
        if self.consumed + self.transfers_sent > self.opening + self.received + self.transfers_received:
            raise ValueError("Consumption exceeds available stock")
        if self.closing != self.opening + self.received + self.transfers_received - self.consumed - self.transfers_sent:
            raise ValueError("Daily inventory balance does not reconcile")
        if self.requested != self.consumed + self.unmet_demand:
            raise ValueError("Unserved demand must be explicit")
        return self


class ScheduledReceipt(BaseModel):
    ordered_at: date
    expected_at: date
    quantity: int = Field(gt=0)
    lead_time_days: int = Field(ge=1)


class InventoryItem(BaseModel):
    provenance_id: str = "synthetic-v1"
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
    ledger: list[StockDay] = Field(default_factory=list)
    scheduled_deliveries: list[ScheduledReceipt] = Field(default_factory=list)
    category: str = "illustrative essential medicine"

    @model_validator(mode="after")
    def stock_balance(self):
        if self.current_stock != self.opening_stock + self.units_received - self.units_consumed:
            raise ValueError("Inventory balance does not reconcile")
        if self.units_consumed > self.opening_stock + self.units_received:
            raise ValueError("Consumption exceeds available stock")
        for previous, current in zip(self.ledger, self.ledger[1:]):
            if previous.closing != current.opening or current.date <= previous.date:
                raise ValueError("Stock ledger continuity failed")
        if self.ledger:
            latest = self.ledger[-1]
            if (latest.opening, latest.received, latest.consumed, latest.closing) != (self.opening_stock, self.units_received, self.units_consumed, self.current_stock):
                raise ValueError("Latest ledger does not match inventory")
        return self


class Beds(BaseModel):
    provenance_id: str = "synthetic-v1"
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
    provenance_id: str = "synthetic-v1"
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
    country_id: CountryCode = "IN"
    provenance_id: str = "synthetic-v1"
    calibration_ids: list[str] = Field(default_factory=list)
    catchment_population: int | None = Field(default=None, gt=0)
    id: str
    name: str
    type: Literal["PHC", "CHC", "District Hospital", "Primary Care Centre", "Community Hospital", "Regional Hospital"]
    state_id: str
    district_id: str | None = None
    district_name: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    status: Status
    resilience_score: int = Field(ge=0, le=100)
    footfall_today: int = Field(ge=0)
    beds: Beds
    staff: Staff
    inventory: list[InventoryItem]
    history: list[DailyActivity]
    synthetic: Literal[True] = True


class Alert(BaseModel):
    country_id: CountryCode = "IN"
    provenance_id: str = "derived-v1"
    id: str
    facility_id: str
    facility_name: str
    district_id: str | None = None
    state_id: str
    severity: Status
    resource: str
    title: str
    explanation: str
    recommended_action: str
    method: Literal["deterministic_threshold"] = "deterministic_threshold"


class Snapshot(BaseModel):
    operational_profile: Literal['constrained', 'redistribution-ready'] = 'constrained'
    profile_version: str = 'inventory-profile-v1'
    profile_purpose: str = 'preserved constrained operational simulation'
    inventory_roles: dict[str, str] = Field(default_factory=dict)
    schema_version: Literal[1, 2] = 2
    country: CountryCode = "IN"
    as_of: date
    seed: int
    regions: list[Region]
    districts: list[District]
    facilities: list[Facility]
    alerts: list[Alert]
    provenance: dict[str, Provenance] = Field(default_factory=dict)
    calibration: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def graph_integrity(self):
        # Add explicit legacy provenance without falsely claiming old data was calibrated.
        if not self.provenance:
            for key, kind, synthetic in (("geography-v1", "derived", False), ("synthetic-v1", "synthetic", True), ("derived-v1", "derived", True)):
                self.provenance[key] = Provenance(id=key, source_type=kind, source_name="Legacy Phase 1 fixture",
                    accessed_at=self.as_of, geography=[self.country], is_synthetic=synthetic,
                    methodology="Uncalibrated legacy snapshot retained for backward compatibility; geography is manually curated.", version="1")
        regions = {r.id: r for r in self.regions}
        districts = {d.id: d for d in self.districts}
        facilities = {f.id: f for f in self.facilities}
        if len(regions) != len(self.regions) or len(districts) != len(self.districts) or len(facilities) != len(self.facilities):
            raise ValueError("Duplicate geography or facility IDs")
        for entity in [*self.regions, *self.districts, *self.facilities, *self.alerts]:
            if entity.country_id != self.country or entity.provenance_id not in self.provenance:
                raise ValueError("Invalid country/provenance relationship")
        for d in self.districts:
            if d.state_id not in regions:
                raise ValueError("District region does not exist")
        for f in self.facilities:
            if f.state_id not in regions or (self.country == "IN" and f.district_id not in districts):
                raise ValueError("Facility region or district does not exist")
            if f.district_id and (f.district_id not in districts or districts[f.district_id].state_id != f.state_id):
                raise ValueError("Facility district belongs to a different region")
            for item in [f.beds, f.staff, *f.inventory, *f.history]:
                if item.provenance_id not in self.provenance:
                    raise ValueError("Missing operational provenance")
            for previous, current in zip(f.history, f.history[1:]):
                if current.previous_occupied is not None and current.previous_occupied != previous.occupied_beds:
                    raise ValueError("Bed history continuity failed")
            if any(h.occupied_beds > f.beds.total - f.beds.reserved for h in f.history):
                raise ValueError("Bed occupancy exceeds operational capacity")
        for a in self.alerts:
            f = facilities.get(a.facility_id)
            if not f or (a.state_id, a.district_id) != (f.state_id, f.district_id):
                raise ValueError("Alert geography does not match facility")
        return self
