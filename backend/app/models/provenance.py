"""Public observations retain their origin; calibration never makes simulation real."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator

CountryCode = Literal["IN", "BR", "RU", "CN", "ZA"]
SourceType = Literal["official_public", "public_international", "derived", "synthetic", "simulation"]


class Provenance(BaseModel):
    id: str
    source_type: SourceType
    source_name: str
    source_url: HttpUrl | None = None
    accessed_at: date
    license: str | None = None
    geography: list[CountryCode]
    is_synthetic: bool
    methodology: str
    version: str
    input_ids: list[str] = Field(default_factory=list)
    checksum_sha256: str | None = None

    @model_validator(mode="after")
    def honest_classification(self):
        if self.source_type in ("official_public", "public_international"):
            if self.is_synthetic or self.source_url is None:
                raise ValueError("Public data requires a source URL and cannot be synthetic")
        if self.source_type in ("synthetic", "simulation") and not self.is_synthetic:
            raise ValueError("Generated or simulated data must be labelled synthetic")
        return self


class Observation(BaseModel):
    id: str
    country_id: CountryCode
    region_id: str | None = None
    indicator: str
    label: str
    year: int = Field(ge=1900, le=2100)
    value: float = Field(ge=0, allow_inf_nan=False)
    unit: Literal["count", "per_10000_population", "per_facility", "percent"]
    provenance_id: str
    source_record_id: str
    note: str = ""

    @model_validator(mode="after")
    def valid_percentage(self):
        if self.unit == "percent" and self.value > 100:
            raise ValueError("Percentages must be between 0 and 100")
        if self.unit == "count" and not self.value.is_integer():
            raise ValueError("Counts must be whole numbers")
        return self


class PublicDataset(BaseModel):
    schema_version: Literal[1] = 1
    adapter_version: str
    provenance: Provenance
    records: list[Observation]
    skipped_records: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_records(self):
        ids, keys = set(), set()
        if not self.records:
            raise ValueError("Source has no valid observations")
        for row in self.records:
            key = (row.country_id, row.region_id, row.indicator, row.year)
            if row.id in ids or key in keys:
                raise ValueError("Duplicate observation")
            if row.country_id not in self.provenance.geography or row.provenance_id != self.provenance.id:
                raise ValueError("Observation geography/provenance does not match source")
            ids.add(row.id)
            keys.add(key)
        return self
