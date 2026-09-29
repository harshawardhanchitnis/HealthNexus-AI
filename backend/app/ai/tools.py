"""Thin bounded adapters over Phase 1–5.5 services."""
import json
from fastapi.encoders import jsonable_encoder
from app.services.summary import summarize
from app.scenarios.engine import select
from app.scenarios.effects import parameters
from app.scenarios.models import ScenarioRequest, ScenarioType
from app.profiles.identity import fingerprint
from app.warnings.engine import listing
from app.data_ingestion.catalog import datasets
from app.ai.tool_registry import validated
from app.ai.action_state import advisory_state


def dump(model, **options):
    return model.model_dump(mode='json', **options)


def scenario_summary(result):
    return {'scenario':dump(result.scenario), 'scenario_id':result.scenario.scenario_id,
            'model_versions':sorted({f.provenance.model_version for f in result.scenario_result.facilities}),
            'baseline':dump(result.baseline.metrics), 'projection':dump(result.scenario_result.metrics),
            'delta':{k:dump(v) for k,v in result.delta.items()},
            'resource_impact':[dump(r) for r in result.resource_impact],
            'warnings_before':dump(result.baseline_warnings.summary),
            'warnings_after':dump(result.warnings_created.summary)}


def preview_summary(result):
    return {'request':dump(result.request), 'snapshot_id':result.snapshot_id,
            'scenario_snapshot_id':result.scenario_snapshot_id, 'origin':str(result.origin),
            'model_version':result.model_version, 'policy_version':result.config_version,
            'total_deficit':result.total_deficit, 'safe_capacity':result.safe_capacity,
            'capacity_by_resource':result.capacity_by_resource, 'deficit_by_resource':result.deficit_by_resource,
            'receiver_pairs':len(result.receivers), 'donor_pairs':len(result.donors), 'feasible_lanes':len(result.edges),
            'receivers':[dump(r) for r in result.receivers[:8]], 'donors':[dump(d) for d in result.donors[:8]],
            'candidates_truncated':len(result.receivers)>8 or len(result.donors)>8, 'limitations':result.limitations}


def plan_summary(result, offset=0, limit=10):
    receivers={(r.facility_id,r.resource_id) for r in result.preview.receivers}
    before={(f.facility_id,r.resource_id):r for f in result.before for r in f.resources}
    risks=[{'facility_id':f.facility_id,'resource_id':r.resource_id,'unit':r.unit,
            'risk_before':before[(f.facility_id,r.resource_id)].stockout.probabilities,
            'risk_after':r.stockout.probabilities,
            'unresolved':result.impact.unresolved.get(f'{f.facility_id}:{r.resource_id}',0)}
        for f in result.after for r in f.resources if (f.facility_id,r.resource_id) in receivers]
    return {'run_id':result.run_id, 'scenario_id':result.preview.request.scenario_id,
            'action_state':advisory_state(),
            'request':dump(result.preview.request), 'solver':dump(result.solver),
            'model_version':result.preview.model_version, 'snapshot_id':result.preview.snapshot_id,
            'policy_version':result.preview.config_version,
            'resource_units':{r.resource_id:r.unit for r in result.preview.receivers},
            'resource_risks':risks[:8],'resource_risks_truncated':len(risks)>8,
            'safe_capacity':result.preview.safe_capacity, 'capacity_by_resource':result.preview.capacity_by_resource,
            'deficit_by_resource':result.preview.deficit_by_resource,
            'impact':dump(result.impact), 'greedy':dump(result.greedy),
            'warnings_before':dump(result.before_warnings.summary), 'warnings_after':dump(result.after_warnings.summary),
            'transfers':[dump(t) for t in result.transfers[offset:offset+limit]],
            'transfers_total':len(result.transfers), 'offset':offset, 'limit':limit,
            'transfers_truncated':offset+limit<len(result.transfers), 'message':result.message,
            'unit_notice':'Aggregate counts are inventory-item accounting tallies across different resource units, not interchangeable doses.'}


class ToolExecutor:
    def __init__(self, repository, engine, planner, context):
        self.repository, self.engine, self.planner, self.context = repository, engine, planner, context
        self.latest_scenario = context.scenario_id
        self.latest_plan = context.optimization_run_id

    def snapshot(self, profile):
        if hasattr(self.repository, 'profile_snapshot'):
            return self.repository.profile_snapshot(self.context.country_id, profile)
        if profile != 'constrained':
            raise ValueError('Selected repository does not support this profile')
        return self.repository.snapshot() if self.context.country_id == 'IN' else self.repository.country_snapshot(self.context.country_id)

    def scenario(self, snapshot, sid):
        r = self.engine.store.get(sid, snapshot.country, snapshot.operational_profile)
        definition = r.scenario.definition
        original = select(snapshot, definition.state_id, definition.district_id, definition.facility_ids)
        bundle = self.engine.forecasts.bundle(snapshot.country, snapshot.operational_profile)
        if r.scenario.baseline_snapshot_id != fingerprint(snapshot, original) or any(
                f.provenance.model_sha256 != bundle.get('artifact_sha256') for f in r.scenario_result.facilities):
            raise ValueError('Scenario is stale for the current snapshot or model')
        scoped = {f.id for f in select(snapshot, self.context.state_id, self.context.district_id,
                    [self.context.facility_id] if self.context.facility_id else None)}
        if not {f.facility_id for f in r.scenario_result.facilities} <= scoped:
            raise ValueError('Scenario exceeds selected conversation geography')
        return r

    def warnings(self, snapshot, args):
        facilities = select(snapshot, args.state_id, args.district_id,
            [args.facility_id or self.context.facility_id] if args.facility_id or self.context.facility_id else None)
        ids = {f.id for f in facilities}
        sid = args.scenario_id if 'scenario_id' in args.model_fields_set else self.latest_scenario
        if sid:
            rows = self.scenario(snapshot, sid).warnings_created.items
        else:
            _, result = self.engine.baseline(snapshot, facilities)
            rows = result.items
        return listing([w for w in rows if w.facility_id in ids and
            (not args.category or w.category == args.category) and (not args.severity or w.severity == args.severity)])

    def execute(self, name, arguments):
        args = validated(name, arguments, self.context)
        snapshot = self.snapshot(args.profile)
        facilities = select(snapshot, args.state_id, args.district_id,
            [getattr(args, 'facility_id', None) or self.context.facility_id]
            if getattr(args, 'facility_id', None) or self.context.facility_id else None)
        result = self.dispatch(name, snapshot, facilities, args)
        result = {'context':{'country_id':snapshot.country, 'profile':snapshot.operational_profile,
                             'profile_version':snapshot.profile_version, 'origin':str(snapshot.as_of)}, **result}
        result = jsonable_encoder(result)
        if len(json.dumps(result, ensure_ascii=False)) > 28000:
            raise ValueError('Tool output exceeds context budget; choose a narrower scope or smaller page')
        return result

    def dispatch(self, name, snapshot, facilities, args):
        if name == 'get_network_summary':
            _, warnings = self.engine.baseline(snapshot, facilities)
            return {'summary':summarize(facilities), 'warnings':dump(warnings.summary),
                'model_version':self.engine.forecasts.bundle(snapshot.country,snapshot.operational_profile)['report']['model_version'],
                'facilities':[{'id':f.id,'name':f.name,'state_id':f.state_id,'district_id':f.district_id} for f in facilities[:8]],
                'facilities_truncated':len(facilities)>8,
                'regions':[{'id':r.id,'name':r.name} for r in snapshot.regions],
                'districts':[{'id':d.id,'name':d.name,'state_id':d.state_id} for d in snapshot.districts]}
        if name == 'get_facility_status':
            f = facilities[0]
            _, warnings = self.engine.baseline(snapshot, [f])
            return {'facility':dump(f, exclude={'history','inventory'}),
                'model_version':self.engine.forecasts.bundle(snapshot.country,snapshot.operational_profile)['report']['model_version'],
                'inventory':[dump(i, exclude={'ledger'}) for i in f.inventory],
                'warnings':dump(warnings.summary), 'provenance':{k:dump(v) for k,v in snapshot.provenance.items()}}
        if name == 'get_forecast':
            if args.target == 'medicine' and not args.resource_id:
                raise ValueError('Medicine forecast requires resource_id')
            resource = args.resource_id if args.target == 'medicine' else args.target
            return dump(self.engine.forecasts.predict(snapshot, args.facility_id, args.target, resource, args.horizon), exclude={'history'})
        if name in ('get_warnings', 'get_warning_summary'):
            result = self.warnings(snapshot, args)
            summary = {'summary':dump(result.summary), 'horizon':14,
                'model_versions':[self.engine.forecasts.bundle(snapshot.country,snapshot.operational_profile)['report']['model_version']],
                'scenario_id':args.scenario_id if 'scenario_id' in args.model_fields_set else self.latest_scenario}
            if name == 'get_warnings':
                summary.update(items=[dump(w) for w in result.items[args.offset:args.offset+args.limit]],
                    offset=args.offset, limit=args.limit, truncated=args.offset+args.limit<len(result.items))
            return summary
        if name == 'get_scenario_presets':
            return {'horizon':14,'duration_range':[1,14],'types':[{'scenario_type':t.value,
                'presets':{s:parameters(ScenarioRequest(scenario_type=t,severity=s)) for s in ('moderate','severe','critical')}} for t in ScenarioType]}
        if name == 'run_emergency_scenario':
            result = self.engine.run(snapshot, args)
            if args.profile == self.context.profile:
                self.latest_scenario = result.scenario.scenario_id
            return scenario_summary(result)
        if name == 'get_scenario_comparison':
            return scenario_summary(self.scenario(snapshot, args.scenario_id))
        if name in ('get_redistribution_preview','optimize_redistribution'):
            body = args.model_copy(deep=True)
            body.scenario_id = body.scenario_id or self.latest_scenario
            if self.context.facility_id and not body.scenario_id:
                raise ValueError('A facility-only plan requires a matching facility scenario; baseline planner scopes are geographic')
            if body.scenario_id:
                self.scenario(snapshot, body.scenario_id)
            if name == 'get_redistribution_preview':
                return preview_summary(self.planner.preview(snapshot, body))
            result = self.planner.run(snapshot, body)
            if args.profile == self.context.profile:
                self.latest_plan = result.run_id
            return plan_summary(result)
        if name == 'get_optimization_result':
            result = self.planner.get(args.run_id, snapshot.country, snapshot.operational_profile)
            # Revalidate underlying snapshot/model/scenario, without solving again.
            self.planner.preview(snapshot, result.preview.request)
            selected = {f.id for f in facilities}
            if any(r.facility_id not in selected for r in result.preview.receivers):
                raise ValueError('Plan receiver geography exceeds selected context')
            return plan_summary(result, args.offset, args.limit)
        if name == 'get_model_performance':
            return self.engine.forecasts.bundle(snapshot.country, snapshot.operational_profile)['report']
        if name == 'get_data_provenance':
            bundle = self.engine.forecasts.bundle(snapshot.country, snapshot.operational_profile)
            return {'data_type':'calibrated simulated operations','purpose':snapshot.profile_purpose,
                'seed':snapshot.seed, 'live_government_inventory':False, 'calibration':snapshot.calibration,
                'interpretation':{
                    'public_inputs':'official public aggregate source inputs',
                    'facility_operations':'fictional calibrated simulated facility operations',
                    'forecast':'derived model-based output; not clinically validated',
                    'scenario':'externally specified simulated stress-test projection',
                    'optimization':'advisory optimization recommendation',
                    'wape':'forecast error metric, not accuracy',
                    'federation':'experimental federated-learning metrics',
                    'connections':'no government systems or hospitals connected'},
                'model_version':bundle['report']['model_version'], 'model_sha256':bundle.get('artifact_sha256'),
                'sources':[{'name':d.provenance.source_name,'url':d.provenance.source_url,
                    'data_type':d.provenance.source_type,'reference_years':sorted({r.year for r in d.records})} for d in datasets()]}
        raise ValueError('Unknown registered tool')
