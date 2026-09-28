"""Explicit verification: choose --live, --offline or --mock. Never trains models."""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.ai.config import AIConfig
from app.ai.schemas import CopilotRequest
from app.ai.orchestrator import CopilotService
from app.ai.client import CopilotError
from app.ai.tools import scenario_summary, plan_summary
from app.services.repository import LocalRepository
from app.scenarios.engine import ScenarioEngine
from app.optimization.service import OptimizationService


class DemoTransport:
    """Cost-free native-loop test double; model behaviour is explicitly mocked."""
    def __init__(self, config): self.count=0
    def create(self, **body):
        self.count+=1
        if self.count==1:
            self.context=json.loads(body['input'])['context']
            self.question=json.loads(body['input'])['question'].lower()
            self.args={k:self.context[k] for k in ('country_id','profile','state_id','district_id')}
            if 'government' in self.question:
                self.sequence=['get_data_provenance']
            elif 'simulate' in self.question:
                self.sequence=['get_network_summary','run_emergency_scenario','get_scenario_comparison',
                    'get_warnings','get_redistribution_preview','optimize_redistribution']
            else: self.sequence=['get_network_summary','get_warnings']
        else:
            returned=json.loads(body['input'][0]['result'][0]['text'])
            if 'error' in returned: raise AssertionError(returned['error'])
            self.eid=returned['evidence_id'];self.payload=returned['result']
            if self.payload.get('scenario_id'):self.sid=self.payload['scenario_id']
        if self.count<=len(self.sequence):
            name=self.sequence[self.count-1];args=dict(self.args)
            if name=='run_emergency_scenario':args.update(scenario_type='DENGUE_SURGE',severity='severe',duration=14,seed=42)
            if name=='get_scenario_comparison':args.update(scenario_id=self.sid)
            if name in ('get_redistribution_preview','optimize_redistribution'):args.update(scope='district',scenario_id=self.sid)
            return {'id':f'mock-interaction-{self.count}','steps':[{'type':'function_call',
                'name':name,'arguments':args,'id':f'mock-call-{self.count}'}]}
        if 'solver' in self.payload:
            text='OR-Tools proved an optimal recommendation under the configured constraints.'
            field='solver.status'
        elif 'live_government_inventory' in self.payload:
            text='This is calibrated simulation, not live government inventory.';field='live_government_inventory'
        else:text='Structured warnings identify operational pressure.';field='summary.total'
        return {'id':'mock-final','output_text':json.dumps({'situation':{'text':text,
            'references':[{'evidence_id':self.eid,'field':field}]},'key_risks':[],
            'recommended_actions':[],'remaining_gaps':[]})}
    def close(self): pass


def verify(mode, output):
    config=AIConfig()
    if mode=='live' and config.error():
        report={'mode':'live','status':'not_run','reason':config.error()[0],'model':config.model}
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report));return 2
    engine=ScenarioEngine();planner=OptimizationService(engine);repo=LocalRepository()
    if mode=='mock':config=AIConfig(api_key='unit-test-placeholder')
    service=CopilotService(engine,planner,config,**({'transport_factory':DemoTransport} if mode=='mock' else {}))
    tests=[('risk','redistribution-ready',"Summarize Pune's current resilience risks.",False),
        ('positive','redistribution-ready','Simulate severe dengue in Pune for 14 days and find the safest redistribution plan.',True),
        ('constrained','constrained','Simulate severe dengue in Pune for 14 days and find the safest redistribution plan.',True),
        ('provenance','constrained','Is this live government inventory?',False)]
    report={'mode':mode,'model':config.model if mode!='offline' else None,'status':'passed','tests':[]}
    for label,profile,message,planning in tests:
        before=repo.profile_snapshot('IN',profile).model_dump_json();began=perf_counter()
        try:
            response=service.run(repo,CopilotRequest(country_id='IN',state_id='MH',district_id='MH-PUNE',
                profile=profile,message=message,mode='offline' if mode=='offline' else 'gemini',allow_planning=planning))
            assert all(t.status=='success' for t in response.tools_used)
            for r in response.operational_results:
                assert r['result']['context']['country_id']=='IN' and r['result']['context']['profile']==profile
            assert before==repo.profile_snapshot('IN',profile).model_dump_json()
            entry={'label':label,'profile':profile,'status':'passed','seconds':perf_counter()-began,
                'response':response.model_dump(mode='json')}
            if planning:
                scenario=engine.store.get(response.scenario_id,'IN',profile)
                plan=planner.get(response.optimization_run_id,'IN',profile)
                row=next(r['result'] for r in response.operational_results if r['tool'] in ('optimize_redistribution','get_optimization_result'))
                authoritative=plan_summary(plan)
                for key in ('solver','impact','safe_capacity','transfers','request'):
                    assert row[key]==authoritative[key],key
                assert plan.preview.request.scenario_id==scenario.scenario.scenario_id
                assert plan.impact.new_donor_risks==plan.impact.donor_safety_violations==0
                if profile=='constrained':assert plan.impact.transferred_units==plan.preview.safe_capacity==0
                else:assert plan.impact.transferred_units>0 and plan.impact.after.target_deficit<plan.impact.before.target_deficit
                entry['accuracy']='Compared exact solver/impact/capacity/transfer/request fields with stored authoritative results'
            report['tests'].append(entry)
            print(label,profile,'passed',round(entry['seconds'],3),[t.tool for t in response.tools_used],flush=True)
        except (CopilotError,AssertionError) as error:
            report['status']='failed';report['tests'].append({'label':label,'status':'failed',
                'code':error.code if isinstance(error,CopilotError) else 'accuracy_failure'})
            break
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for mode in ('live','offline','mock'):group.add_argument('--'+mode,action='store_true')
    p.add_argument('--output',type=Path);args=p.parse_args()
    mode=next(m for m in ('live','offline','mock') if getattr(args,m))
    sys.exit(verify(mode,args.output or Path(f'docs/evaluation/phase6-{mode}.json')))
