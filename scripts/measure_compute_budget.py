"""Zero-provider demo stress; cgroup total/peak, not just process RSS.

Run the server with a decimal 450000000-byte memory/swap limit. A tiny shell
reads the existing process and cgroup; never start a second scientific Python
process inside the constrained container. Historical RSS receipts stay separate.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BUDGET = 450_000_000


def measure(container, base, cycles, stability):
    records, checks, forecasts, bursts = [], [], {}, []
    began=monotonic()
    def memory(stage):
        output=subprocess.check_output(['docker','exec',container,'sh','-c',
            "cat /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.peak; sed -n '/^VmRSS:/p;/^VmHWM:/p;/^RssAnon:/p;/^RssFile:/p' /proc/1/status"],text=True).splitlines()
        row={'stage':stage,'elapsed_seconds':monotonic()-began,'total_bytes':int(output[0]),'total_peak_bytes':int(output[1])}
        row.update({line.split(':')[0]:int(line.split()[1])*1024 for line in output[2:]})
        records.append(row)
        print(f'{stage}: total {row["total_bytes"]/1e6:.1f} MB; peak {row["total_peak_bytes"]/1e6:.1f} MB; RSS {row["VmRSS"]/2**20:.1f} MiB',flush=True)
    def call(path, body=None, method=None, expected=(200,201,204)):
        req=Request(base+path,data=json.dumps(body).encode() if body is not None else None,
            method=method or ('POST' if body is not None else 'GET'),headers={'Content-Type':'application/json'})
        started=monotonic()
        try:
            with urlopen(req,timeout=120) as response:status=response.status;content=response.read()
        except HTTPError as error:status=error.code;content=error.read()
        assert status in expected,(path,status,content[:300])
        data=json.loads(content) if content else None
        return data,status,monotonic()-started
    def get(stage,path):
        data,_,_=call(path);memory(stage);return data
    for _ in range(90):
        try:
            call('/health');break
        except OSError:sleep(1)
    else:raise ValueError('Server did not bind')
    memory('startup')
    assert get('readiness','/readiness')['status']=='ready'
    policy=get('capabilities','/api/countries')['runtime_capabilities']
    assert policy['district_computation_only'] and policy['planning_scopes']==['district','cross_district']
    for method,path,body in [('GET','/api/warnings',None),('GET','/api/geospatial?mode=forecast',None),
        ('POST','/api/scenarios',{'scenario_type':'DENGUE_SURGE'}),('POST','/api/optimization/preview',{'scope':'national'}),
        ('POST','/api/optimization/redistribution',{'scope':'state','state_id':'MH'}),
        ('POST','/api/ai/copilot',{'message':'Summarize resource resilience','mode':'offline'})]:
        data,status,seconds=call(path,body,method,expected=(422,))
        checks.append({'operation':path,'status':status,'seconds':seconds,'district_required':True})
    memory('national-computation-rejected')
    # Cold simultaneous forecasts: only admitted work loads models. Rejected
    # calls have no side effects and do not consume provider requests.
    def burst(index):
        return call('/api/forecasts/facilities/IN-MH-PUNE-003/footfall?profile=redistribution-ready',expected=(200,429))
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses=list(pool.map(burst,range(8)))
    for data,status,seconds in responses:
        if status==429:assert data['detail']['code']=='operational_busy'
        bursts.append({'status':status,'seconds':seconds})
    assert any(r['status']==200 for r in bursts) and any(r['status']==429 for r in bursts)
    memory('concurrent-cold-forecasts')
    def cycle(index):
        prefix=f'cycle-{index}:'
        get(prefix+'overview','/api/overview?profile=redistribution-ready')
        get(prefix+'network-map','/api/geospatial?profile=redistribution-ready&mode=network')
        for profile in ('redistribution-ready','constrained'):
            for resource in ('footfall','beds','medicines/IVF','medicines/PCM','medicines/ORS','medicines/AMX','medicines/IFA'):
                data,_,_=call(f'/api/forecasts/facilities/IN-MH-PUNE-003/{resource}?profile={profile}')
                key=profile+':'+resource
                stamp=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                assert key not in forecasts or forecasts[key]==stamp
                forecasts[key]=stamp
            memory(prefix+profile+':forecasts')
        handles=[]
        for profile in ('redistribution-ready','constrained'):
            context={'country_id':'IN','profile':profile,'state_id':'MH','district_id':'MH-PUNE'}
            scenario,_,_=call('/api/scenarios',context|{'scenario_type':'DENGUE_SURGE','severity':'severe','duration':14,'seed':42})
            sid=scenario['scenario']['scenario_id'];handles.append(('scenario',sid,context))
            memory(prefix+profile+':scenario')
            get(prefix+profile+':live-warnings','/api/warnings?'+urlencode(context))
            get(prefix+profile+':forecast-map','/api/geospatial?'+urlencode(context|{'mode':'forecast'}))
            for scope in ('district','cross_district') if profile=='redistribution-ready' else ('district',):
                plan,_,seconds=call('/api/optimization/redistribution',context|{'scope':scope,'scenario_id':sid})
                rid=plan['run_id'];handles.append(('plan',rid,context))
                actual=[plan['preview']['total_deficit'],plan['preview']['safe_capacity'],plan['impact']['transferred_units'],len(plan['transfers']),plan['impact']['after']['target_deficit']]
                expected=[30230,0,0,0,30230] if profile=='constrained' else ([41763,17745,15679,10,26084] if scope=='district' else [41763,9307,9307,10,32456])
                assert actual==expected,(profile,scope,actual)
                assert plan['impact']['donor_safety_violations']==plan['impact']['new_donor_risks']==0
                assert all(c['before']==c['after'] for c in plan['impact']['conservation'].values())
                view=get(prefix+profile+':'+scope+'-map','/api/geospatial?'+urlencode(context|{'mode':'redistribution','donor_scope':scope,'scenario_id':sid,'run_id':rid}))
                assert len(view['transfers']['features'])==actual[3]
                if scope=='cross_district':assert all(t['donor_district_id']=='MH-NAGPUR' and t['receiver_district_id']=='MH-PUNE' for t in plan['transfers'])
                checks.append({'cycle':index,'profile':profile,'scope':scope,'metrics':actual,'seconds':seconds,'donor_violations':0,'new_donor_risks':0,'conservation':'PASS'})
                memory(prefix+profile+':'+scope+'-optimizer')
        # Both scenarios and all three accepted plans must coexist without eviction.
        for kind,ident,context in handles:
            path='/api/scenarios/' if kind=='scenario' else '/api/optimization/runs/'
            call(path+ident+'?'+urlencode(context))
        memory(prefix+'full-stores')
        # A new run is refused at capacity rather than silently replacing handles.
        context={'country_id':'IN','profile':'redistribution-ready','state_id':'MH','district_id':'MH-PUNE'}
        call('/api/scenarios',context|{'scenario_type':'DENGUE_SURGE'},expected=(422,))
        call('/api/optimization/redistribution',context|{'scope':'district'},expected=(422,))
        for kind,ident,context in reversed(handles):
            path='/api/scenarios/' if kind=='scenario' else '/api/optimization/runs/'
            call(path+ident+'?'+urlencode(context),method='DELETE')
        # Actual local tool orchestration, bounded retained conversation/progress,
        # explicit offline mode; no Gemini transport is allowed by container config.
        context={'country_id':'IN','profile':'redistribution-ready','state_id':'MH','district_id':'MH-PUNE'}
        reply,_,_=call('/api/ai/copilot',context|{'message':'Summarize current resource resilience in Pune','mode':'offline'})
        assert reply['mode']=='offline' and reply['metadata']['provider_requests']==0
        assert reply['evidence'] and all(t['status']=='success' for t in reply['tools_used'])
        memory(prefix+'offline-copilot')
        saved=get(prefix+'federation-evidence','/api/federation/saved-demo')
        assert saved['raw_records_shared']==0 and saved['saved_demo']
        get(prefix+'federation-nodes','/api/federation/nodes')
        get(prefix+'federation-status','/api/federation/status')
        memory(prefix+'complete')
    for index in range(1,cycles+1):cycle(index)
    deadline=monotonic()+stability;extra=0
    while monotonic()<deadline:
        extra+=1;cycle(cycles+extra)
        sleep(min(2,max(0,deadline-monotonic())))
    state=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
    events=dict(line.split() for line in subprocess.check_output(['docker','exec',container,'cat','/sys/fs/cgroup/memory.events'],text=True).splitlines())
    events={key:int(value) for key,value in events.items()}
    peak=max(r['total_peak_bytes'] for r in records)
    ends=[r['VmRSS'] for r in records if r['stage'].endswith(':complete')]
    # A single completion sample may include Docker's short-lived Python
    # healthcheck. Keep its allocation in total_peak_bytes, but compare retained
    # memory using per-cycle minima plus server RSS instead of calling that
    # transient allocation a leak. The 450 MB peak ceiling is unchanged.
    minima=[min(r['total_bytes'] for r in records if r['stage'].startswith(f'cycle-{i}:'))
            for i in range(1,cycles+extra+1)]
    healthy=state['State']['Running'] and not state['State']['OOMKilled'] and state['RestartCount']==0
    plateau=(len(ends)<3 or max(ends[-3:])-min(ends[-3:]) < 10_000_000) and (len(minima)<3 or max(minima[-3:])-min(minima[-3:]) < 10_000_000)
    # Merely touching the hard limit and relying on forced reclamation is not
    # sufficient release headroom, even if Linux did not kill the process.
    headroom=events.get('max',0)==0
    # Docker can charge shared read-only library pages to another cgroup. Add
    # the largest sampled server file RSS once more as a conservative allowance
    # rather than claiming a warm/shared-cache reading is an isolated footprint.
    shared_file_allowance=max(r['RssFile'] for r in records)
    conservative_peak=peak+shared_file_allowance
    return {'status':'PASS' if healthy and conservative_peak<BUDGET and plateau and headroom else 'FAIL','provider_requests':0,
        'measurement':'cgroup v2 total current/peak including charged file cache and container processes; server /proc/1 RSS separately',
        'budget_bytes':BUDGET,'peak_total_bytes':peak,'maximum_rss_bytes':max(r['VmRSS'] for r in records),
        'maximum_observed_total_bytes':max(r['total_bytes'] for r in records),'plateau':plateau,'healthy':healthy,
        'oom':state['State']['OOMKilled'],'restarts':state['RestartCount'],'container':container,'container_id':state['Id'],
        'image_id':state['Image'],'memory_limit_bytes':state['HostConfig']['Memory'],'memory_swap_limit_bytes':state['HostConfig']['MemorySwap'],
        'cycles':cycles,'extra_cycles':extra,'stability_seconds':stability,'records':records,'checks':checks,'concurrent_burst':bursts,
        'memory_events':events,'no_forced_limit_reclamation':headroom,
        'shared_file_allowance_bytes':shared_file_allowance,'conservative_peak_with_shared_file_allowance_bytes':conservative_peak,
        'shared_file_allowance_method':'Measured cgroup peak plus largest sampled server RssFile; deliberately counts even already-charged mapped files again. This is an allowance, not another peak measurement.',
        'cycle_minimum_total_bytes':minima,'completion_server_rss_bytes':ends,
        'forecast_sha256':forecasts,'limitations':'Finite local acceptance, not a guarantee for arbitrary traffic or a cloud measurement. No live provider call.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--container',required=True);p.add_argument('--base',default='http://127.0.0.1:18710')
    p.add_argument('--cycles',type=int,default=2);p.add_argument('--stability-seconds',type=int,default=180);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:report=measure(a.container,a.base,a.cycles,a.stability_seconds)
    except Exception as error:
        report={'status':'FAIL','error':str(error),'provider_requests':0}
        try:
            state=json.loads(subprocess.check_output(['docker','inspect',a.container]))[0]
            report.update(oom=state['State']['OOMKilled'],restarts=state['RestartCount'],running=state['State']['Running'])
        except Exception:pass
    a.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','checks','forecast_sha256','concurrent_burst')},indent=2))
    raise SystemExit(0 if report['status']=='PASS' else 1)
