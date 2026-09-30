"""Sequential zero-provider Linux-container deployment journey and RSS/HWM receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from time import monotonic, sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def measure(container, base, cycles, stability_seconds):
    records, forecasts, checks = [], {}, []
    began = monotonic()
    def memory(stage):
        code = "import json; from pathlib import Path; d={r.split(':')[0]:r.split(':')[1].strip() for r in Path('/proc/1/status').read_text().splitlines() if ':' in r}; print(json.dumps({k:int(d[k].split()[0])*1024 for k in ('VmRSS','VmHWM')}))"
        row = json.loads(subprocess.check_output(['docker','exec',container,'python','-c',code]))
        row.update(stage=stage, elapsed_seconds=monotonic()-began)
        records.append(row)
        print(f'{stage}: RSS {row["VmRSS"]/2**20:.1f}; peak {row["VmHWM"]/2**20:.1f} MiB',flush=True)
        return row
    def call(path, body=None, method=None):
        req = Request(base+path, data=json.dumps(body).encode() if body else None,
                      method=method or ('POST' if body else 'GET'), headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=240) as response:
            assert response.status in (200,201,204)
            content=response.read()
            return json.loads(content) if content else None
    for _ in range(90):
        try:
            # Docker's port proxy can accept TCP before uvicorn is ready.
            assert call('/health')['status']=='ok'
            break
        except OSError:sleep(1)
    else:raise ValueError('Server did not bind')
    memory('startup')
    def cycle(index):
        prefix=f'cycle-{index}:'
        def get(stage,path):
            data=call(path);memory(prefix+stage);return data
        get('health','/health')
        assert get('readiness','/readiness')['status']=='ready'
        get('overview','/api/overview?country_id=IN&profile=redistribution-ready')
        get('facilities','/api/facilities?country_id=IN&profile=redistribution-ready')
        for profile in ('redistribution-ready','constrained'):
            for resource in ('footfall','beds','medicines/IVF','medicines/PCM','medicines/ORS','medicines/AMX','medicines/IFA'):
                path=f'/api/forecasts/facilities/IN-MH-PUNE-003/{resource}?country_id=IN&profile={profile}'
                response=call(path)
                key=profile+':'+resource
                stamp=hashlib.sha256(json.dumps(response,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                assert key not in forecasts or forecasts[key]==stamp,'Forecast changed within run'
                forecasts[key]=stamp
        memory(prefix+'forecast')
        get('model-performance','/api/models/forecasting/metrics?country_id=IN&profile=redistribution-ready')
        # Plain network geography must remain operationally lightweight.
        get('geospatial-network','/api/geospatial?country_id=IN&profile=redistribution-ready&mode=network')
        for profile in ('redistribution-ready','constrained'):
            context=dict(country_id='IN',profile=profile,state_id='MH',district_id='MH-PUNE')
            scenario=call('/api/scenarios',context|dict(scenario_type='DENGUE_SURGE',severity='severe',duration=14,seed=42))
            sid=scenario['scenario']['scenario_id'];memory(prefix+profile+':scenario')
            get(profile+':warnings','/api/warnings?'+urlencode(context|dict(scenario_id=sid)))
            for scope in ('district','cross_district') if profile=='redistribution-ready' else ('district',):
                plan=call('/api/optimization/redistribution',context|dict(scope=scope,scenario_id=sid))
                actual=(plan['preview']['total_deficit'],plan['preview']['safe_capacity'],plan['impact']['transferred_units'],len(plan['transfers']),plan['impact']['after']['target_deficit'])
                expected=(30230,0,0,0,30230) if profile=='constrained' else ((41763,17745,15679,10,26084) if scope=='district' else (41763,9307,9307,10,32456))
                assert actual==expected,(profile,scope,actual)
                assert plan['impact']['donor_safety_violations']==plan['impact']['new_donor_risks']==0
                assert all(c['before']==c['after'] for c in plan['impact']['conservation'].values())
                if scope=='cross_district':assert all(t['donor_district_id']=='MH-NAGPUR' and t['receiver_district_id']=='MH-PUNE' for t in plan['transfers'])
                memory(prefix+profile+':'+scope+'-optimizer')
                if profile=='redistribution-ready':
                    view=get('geospatial-'+scope,'/api/geospatial?'+urlencode(context|dict(mode='redistribution',donor_scope=scope,scenario_id=sid,run_id=plan['run_id'])))
                    assert len(view['transfers']['features'])==actual[3]
                checks.append(dict(cycle=index,profile=profile,scope=scope,metrics=actual))
                call('/api/optimization/runs/'+plan['run_id']+'?'+urlencode(context),method='DELETE')
            call('/api/scenarios/'+sid+'?'+urlencode(context),method='DELETE')
        get('national-warnings','/api/warnings?country_id=IN&profile=redistribution-ready')
        saved=get('federation-evidence','/api/federation/saved-demo')
        assert saved['raw_records_shared']==0 and saved['saved_demo']
        get('federation-nodes','/api/federation/nodes')
        get('federation-status','/api/federation/status')
        get('copilot-status','/api/ai/status')
        memory(prefix+'complete')
        print(f'Cycle {index}: PASS; RSS {records[-1]["VmRSS"]/2**20:.1f} MiB; peak {records[-1]["VmHWM"]/2**20:.1f} MiB',flush=True)
    for index in range(1,cycles+1):cycle(index)
    deadline=monotonic()+stability_seconds
    extra=0
    while monotonic()<deadline:
        extra+=1;cycle(cycles+extra)
        sleep(min(3,max(0,deadline-monotonic())))
    state=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
    assert state['RestartCount']==0 and not state['State']['OOMKilled'] and state['State']['Running']
    peak=max(r['VmHWM'] for r in records)
    ends=[r['VmRSS'] for r in records if r['stage'].endswith(':complete')]
    comfortable=not state['HostConfig']['Memory'] or peak < 430*2**20
    plateau=len(ends)<2 or max(ends[1:])-min(ends[1:]) < 10*2**20
    return dict(status='PASS' if comfortable and plateau else 'FAIL',comfortable_memory=comfortable,memory_plateau=plateau,
                provider_requests=0,container=container,records=records,canonical_checks=checks,
                container_id=state['Id'],image_id=state['Image'],started_at=state['State']['StartedAt'],
                forecast_sha256=forecasts,cycles=cycles,stability_seconds=stability_seconds,extra_cycles=extra,
                maximum_rss_bytes=max(r['VmRSS'] for r in records),peak_rss_bytes=peak,
                memory_limit_bytes=state['HostConfig']['Memory'],oom=False,restarts=state['RestartCount'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container',required=True);parser.add_argument('--base',default='http://127.0.0.1:18700')
    parser.add_argument('--cycles',type=int,default=2);parser.add_argument('--stability-seconds',type=int,default=0)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=measure(args.container,args.base,args.cycles,args.stability_seconds)
    args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','canonical_checks','forecast_sha256')},indent=2))
    raise SystemExit(0 if report['status']=='PASS' else 1)
