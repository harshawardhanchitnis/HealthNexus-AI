"""Whitelist, strict declarations and context checks; no HTTP loopback."""
from dataclasses import dataclass
from pydantic import BaseModel
from app.ai.schemas import (Scope, FacilityArgs, ForecastArgs, WarningArgs, ScenarioArgs,
                            ScenarioIDArgs, PlanArgs, PlanIDArgs)


@dataclass(frozen=True)
class Tool:
    schema: type[BaseModel]
    description: str
    planning: bool = False


TOOLS = {
    'get_network_summary': Tool(Scope, 'Read simulated network KPIs and IDs when discovery is needed. Explicit validated geography needs no discovery preamble; no emergency shock.'),
    'get_facility_status': Tool(FacilityArgs, 'Read a selected facility current simulated inventory, known receipts, beds, personnel and baseline warnings, with provenance. No full histories.'),
    'get_forecast': Tool(ForecastArgs, 'Read saved ML BASELINE demand forecast, empirical intervals, model evaluation and medicine stock trajectory. Choose horizon 1, 7 or 14. Not a scenario projection; medicine requires resource_id.'),
    'get_warnings': Tool(WarningArgs, 'Search existing 14-day structured warnings, ranked by deterministic priority. Omitted scenario_id uses the active scenario; explicit null selects baseline. Pagination is explicit.'),
    'get_warning_summary': Tool(WarningArgs, 'Read aggregated counts, severities and geography of existing warning results, with the same filters as get_warnings.'),
    'get_scenario_presets': Tool(Scope, 'Discover four supported Digital Twin scenarios, allowed duration and severity preset parameters; this does not run a simulation.'),
    'run_emergency_scenario': Tool(ScenarioArgs, 'PLANNING ONLY: run an explicitly requested non-destructive externally specified emergency shock through the existing Digital Twin. Return new scenario ID, actual comparison and assumptions. Never alter baseline.', True),
    'get_scenario_comparison': Tool(ScenarioIDArgs, 'Read a saved scenario comparison: actual baseline/scenario metrics, resource deltas and warnings. ID must match country/profile and current snapshot/model.'),
    'get_redistribution_preview': Tool(PlanArgs, 'Read actual receiver deficits and safe donor opportunities under unchanged donor protection policy. Set domestic donor scope. A preview does not solve or execute transfers.'),
    'optimize_redistribution': Tool(PlanArgs, 'PLANNING ONLY: invoke the actual OR-Tools CP-SAT planner for an explicitly requested simulated recommendation. Solver selects quantities/routes. Return solver status, protected donors, remaining deficits and greedy comparison. No physical transfer.', True),
    'get_optimization_result': Tool(PlanIDArgs, 'Read a saved actual OR-Tools result including paginated transfers, rationale, worst donor reserve, before/after risk, conservation and greedy outcomes. Never invent a plan.'),
    'get_model_performance': Tool(Scope, 'Read measured forecasting champion/baseline metrics and interval coverage. Evaluation is on simulated histories, not clinical or real-world validation.'),
    'get_data_provenance': Tool(Scope, 'Read official public aggregate sources, operational simulation profile, seed, frozen origin, calibration and model identity. Explain the distinction from live government facility feeds.'),
}


def json_schema(model):
    schema = model.model_json_schema()
    definitions = schema.get('$defs', {})
    def expand(value):
        if isinstance(value, list):
            return [expand(x) for x in value]
        if isinstance(value, dict):
            if '$ref' in value:
                return expand(definitions[value['$ref'].split('/')[-1]])
            return {k:expand(v) for k,v in value.items() if k not in ('$defs', 'title', 'default')}
        return value
    return expand(schema)


def declarations(names=None):
    return [{'type':'function', 'name':name, 'description':tool.description,
             'parameters':json_schema(tool.schema)} for name,tool in TOOLS.items() if names is None or name in names]


SUBSETS = {
    'resilience-summary': frozenset(('get_network_summary','get_warning_summary')),
    'network-risk': frozenset(('get_network_summary','get_facility_status','get_forecast',
        'get_warnings','get_warning_summary','get_scenario_presets')),
    'emergency-planning': frozenset(('get_scenario_presets','run_emergency_scenario',
        'get_scenario_comparison','get_warnings','get_warning_summary','get_redistribution_preview',
        'optimize_redistribution','get_optimization_result')),
    'provenance': frozenset(('get_data_provenance','get_model_performance')),
    'follow-up-plan': frozenset(('get_optimization_result','get_facility_status')),
    'plan-review': frozenset(('get_optimization_result','get_redistribution_preview')),
}


def intent(request):
    """Server-owned routing only; no request field can supply a tool whitelist."""
    text = request.message.lower()
    if any(word in text for word in ('provenance','government inventory','forecast accuracy','forecast reliability')):
        return 'provenance'
    if request.allow_planning and any(word in text for word in ('simulate','surge','optimize','redistribution plan')):
        return 'emergency-planning'
    if request.optimization_run_id:
        return 'follow-up-plan' if any(word in text for word in ('why','donors','shortages remain')) else 'plan-review'
    if 'resource resilience status' in text:
        return 'resilience-summary'
    return 'network-risk'


def validated(name, arguments, context):
    if name not in TOOLS:
        raise ValueError('Unknown tool; only registered HealthNexus tools are allowed')
    tool = TOOLS[name]
    args = tool.schema.model_validate(arguments)
    if args.country_id != context.country_id:
        raise ValueError('Tool country must match selected context')
    if args.profile != context.profile and not context.compare_profiles:
        raise ValueError('Tool profile must match selected context; no automatic switching')
    for field in ('state_id', 'district_id'):
        selected = getattr(context, field)
        proposed = getattr(args, field)
        if selected and proposed and proposed != selected:
            raise ValueError('Tool geography must remain within selected context')
        if selected and not proposed:
            setattr(args, field, selected)
    if context.facility_id and getattr(args, 'facility_id', context.facility_id) not in (None, context.facility_id):
        raise ValueError('Tool facility must match selected context')
    if isinstance(args, ScenarioArgs) and context.facility_id:
        if args.facility_ids and args.facility_ids != [context.facility_id]:
            raise ValueError('Scenario facilities must match selected facility')
        args.facility_ids = [context.facility_id]
    if tool.planning and not context.allow_planning:
        raise ValueError('Planning not authorized: enable simulations and plans explicitly')
    return args
