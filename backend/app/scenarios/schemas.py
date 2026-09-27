from pydantic import BaseModel
from app.scenarios.models import ScenarioMetadata, Outcome, MetricDelta, ResourceImpact, ScenarioType
from app.warnings.models import WarningList


class ScenarioResult(BaseModel):
    scenario: ScenarioMetadata
    baseline: Outcome
    scenario_result: Outcome
    delta: dict[str, MetricDelta]
    resource_impact: list[ResourceImpact]
    baseline_warnings: WarningList
    warnings_created: WarningList


class ScenarioPreset(BaseModel):
    scenario_type: ScenarioType
    presets: dict[str, dict[str, float | str]]


class PresetResponse(BaseModel):
    horizon: int
    duration_range: list[int]
    types: list[ScenarioPreset]
