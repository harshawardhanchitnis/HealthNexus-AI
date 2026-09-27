from datetime import date
from typing import Literal
from pydantic import BaseModel, Field
from app.models.provenance import CountryCode


class Metric(BaseModel):
    mae: float
    rmse: float
    wape: float | None
    samples: int


class Window(BaseModel):
    start: date
    end: date


class ModelComparison(BaseModel):
    selection: Metric
    test: Metric
    test_by_horizon: dict[str, Metric]


class Coverage(BaseModel):
    coverage: float
    mean_width: float
    samples: int
    calibration_paths: int


class TargetReport(BaseModel):
    champion: str
    models: dict[str, ModelComparison]
    coverage: dict[str, dict[str, Coverage]]
    train_rows: int
    selection_rows: int
    calibration_rows: int
    test_rows: int


class PerformanceReport(BaseModel):
    country_id: CountryCode
    model_version: str
    evaluated_at: str
    windows: dict[str, Window]
    data_type: str
    history_sha256: str
    feature_schema: list[str]
    config: dict
    sklearn_version: str
    selection_rule: str
    uncertainty_method: str
    source_vintage_note: str
    targets: dict[str, TargetReport]


class ForecastPoint(BaseModel):
    date: date
    point: float = Field(ge=0)
    lower80: float = Field(ge=0)
    upper80: float = Field(ge=0)
    lower95: float = Field(ge=0)
    upper95: float = Field(ge=0)


class HistoryPoint(BaseModel):
    date: date
    value: float


class InventoryPoint(BaseModel):
    date: date
    expected_receipts: float
    demand: float
    closing_stock: float
    unmet_demand: float
    lower95: float
    upper95: float


class StockRisk(BaseModel):
    current_stock: int
    safety_stock: int
    days_of_cover: float | None
    cover_method: str
    safety_breach_date: date | None
    stockout_date: date | None
    probabilities: dict[str, float]
    simulations: int
    trajectory: list[InventoryPoint]
    status: Literal["HIGH", "WATCH", "LOW"]
    method: str


class ForecastProvenance(BaseModel):
    data_type: str
    is_synthetic: Literal[True] = True
    model_version: str
    model: str
    trained_through: date
    evaluated_at: str
    windows: dict[str, Window]
    history_sha256: str
    calibration_sources: list[dict]
    source_vintage_note: str
    uncertainty_method: str


class ForecastSummary(BaseModel):
    latest_demand: float
    recent_daily_mean: float
    forecast_daily_mean: float
    forecast_total: float
    change_percent: float | None
    total_lower80: float
    total_upper80: float
    total_lower95: float
    total_upper95: float


class ForecastResponse(BaseModel):
    country_id: CountryCode
    facility_id: str
    resource_id: str
    target: Literal["footfall", "medicine", "admissions"]
    horizon: Literal[1, 7, 14]
    as_of: date
    unit: str
    history: list[HistoryPoint]
    forecast: list[ForecastPoint]
    summary: ForecastSummary
    provenance: ForecastProvenance
    test_metric: Metric
    coverage: dict[str, Coverage]
    explanations: list[str]
    stockout: StockRisk | None = None


class StockRisksResponse(BaseModel):
    country_id: CountryCode
    facility_id: str
    as_of: date
    items: list[ForecastResponse]
