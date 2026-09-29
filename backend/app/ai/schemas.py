from typing import Any, Literal, Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.provenance import CountryCode
from app.profiles.config import ProfileID
from app.optimization.schemas import Resource, RedistributionRequest
from app.scenarios.models import ScenarioRequest
from app.warnings.models import Severity


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Context(Strict):
    country_id: CountryCode = 'IN'
    profile: ProfileID = 'constrained'
    state_id: str | None = Field(None, max_length=80)
    district_id: str | None = Field(None, max_length=80)
    facility_id: str | None = Field(None, max_length=100)
    scenario_id: str | None = Field(None, max_length=100)
    optimization_run_id: str | None = Field(None, max_length=100)


class CopilotRequest(Context):
    message: str = Field(min_length=1, max_length=2000)
    mode: Literal['gemini', 'offline'] = 'gemini'
    allow_planning: bool = False
    compare_profiles: bool = False
    conversation_id: UUID | None = None
    request_id: UUID | None = None


class Scope(Strict):
    country_id: CountryCode
    profile: ProfileID
    state_id: str | None = Field(None, max_length=80)
    district_id: str | None = Field(None, max_length=80)


class FacilityArgs(Scope):
    facility_id: str = Field(min_length=1, max_length=100)


class ForecastArgs(FacilityArgs):
    target: Literal['medicine', 'footfall', 'admissions']
    resource_id: Resource | None = None
    horizon: Literal[1, 7, 14] = 14


class WarningArgs(Scope):
    facility_id: str | None = Field(None, max_length=100)
    scenario_id: str | None = Field(None, max_length=100)
    category: Literal['medicine', 'demand', 'beds', 'personnel', 'emergency'] | None = None
    severity: Severity | None = None
    offset: int = Field(0, ge=0, le=2000)
    limit: int = Field(8, ge=1, le=12)


class ScenarioArgs(ScenarioRequest):
    country_id: CountryCode
    profile: ProfileID


class ScenarioIDArgs(Scope):
    scenario_id: str = Field(min_length=1, max_length=100)


class PlanArgs(RedistributionRequest):
    country_id: CountryCode
    profile: ProfileID


class PlanIDArgs(Scope):
    run_id: str = Field(min_length=1, max_length=100)
    offset: int = Field(0, ge=0, le=2000)
    limit: int = Field(10, ge=1, le=12)


class Reference(Strict):
    evidence_id: str = Field(min_length=1, max_length=30)
    field: str = Field(min_length=1, max_length=200, description='Exact dot path into a tool result, using array indices.')


class Claim(Strict):
    text: str = Field(min_length=1, max_length=700, description='Prefer qualitative explanation. Cite exact scalar fields; authoritative numbers are rendered by the server. Do not calculate or round.')
    references: list[Reference] = Field(min_length=1, max_length=4)


class DraftAnswer(Strict):
    situation: Claim
    key_risks: list[Claim] = Field(default_factory=list, max_length=5)
    recommended_actions: list[Claim] = Field(default_factory=list, max_length=5)
    remaining_gaps: list[Claim] = Field(default_factory=list, max_length=4)


FactId=Annotated[str,Field(min_length=1,max_length=64)]


class FactClaim(Strict):
    text: str = Field(min_length=1, max_length=700, description='Explain only the cited facts. Prefer focused qualitative text; do not calculate, round or convert values.')
    evidence_refs: list[FactId] = Field(min_length=1, max_length=4, description='Copy exact fact IDs from the CURRENT evidence catalogue. No paths, values, units or previous-request IDs.')


class FactDraftAnswer(Strict):
    """Provider-only contract. Public UI claims remain server-resolved Claim objects."""
    situation: FactClaim
    key_risks: list[FactClaim] = Field(default_factory=list, max_length=5)
    recommended_actions: list[FactClaim] = Field(default_factory=list, max_length=5)
    remaining_gaps: list[FactClaim] = Field(default_factory=list, max_length=4)


class Evidence(Strict):
    evidence_id: str
    tool: str
    source_type: str
    source_id: str | None = None
    field: str
    value: Any
    profile: ProfileID
    unit: str | None = None


class ToolTrace(Strict):
    tool: str
    status: Literal['running', 'success', 'error']
    seconds: float = 0
    summary: str = ''
    evidence_id: str | None = None


class CopilotResponse(Strict):
    request_id: str
    conversation_id: str | None = None
    mode: Literal['gemini', 'offline', 'refusal']
    status: Literal['completed', 'refused'] = 'completed'
    answer: str
    situation: Claim | None = None
    key_risks: list[Claim] = Field(default_factory=list)
    recommended_actions: list[Claim] = Field(default_factory=list)
    remaining_gaps: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    tools_used: list[ToolTrace] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    context: Context
    scenario_id: str | None = None
    optimization_run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    operational_results: list[dict[str, Any]] = Field(default_factory=list)
