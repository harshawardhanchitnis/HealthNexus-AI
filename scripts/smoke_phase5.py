"""Live API checks. Keeps the Pune demo scenario/plan; discards other test plans."""
import json
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "http://127.0.0.1:8000/api"


def call(path, body=None, method=None):
    request = Request(BASE+path, data=json.dumps(body).encode() if body is not None else None,
        method=method or ('POST' if body is not None else 'GET'), headers={'Content-Type':'application/json'})
    with urlopen(request, timeout=300) as response:
        text = response.read()
        return json.loads(text) if text else None


def missing(path):
    try: call(path)
    except HTTPError as e:
        assert e.code == 404, e.code
    else: raise AssertionError('Cross-country/missing record was accessible')


def run():
    report = {'countries':[], 'pune':{}, 'checks':[]}
    for country in ['IN','BR','RU','CN','ZA']:
        body={'country_id':country}
        before=call(f'/inventory?country_id={country}')
        start=perf_counter()
        p=call('/optimization/redistribution',body)
        wall=perf_counter()-start
        assert p['solver']['status'] in ('OPTIMAL','FEASIBLE')
        assert p['impact']['new_donor_risks'] == p['impact']['donor_safety_violations'] == 0
        assert all(c['before']==c['after'] for c in p['impact']['conservation'].values())
        assert all(f['country_id']==country for f in p['before']+p['after'])
        assert before==call(f'/inventory?country_id={country}')
        other='BR' if country=='IN' else 'IN'
        missing(f"/optimization/runs/{p['run_id']}?country_id={other}")
        assert call(f"/optimization/runs/{p['run_id']}?country_id={country}") == p
        call(f"/optimization/runs/{p['run_id']}?country_id={country}",method='DELETE')
        missing(f"/optimization/runs/{p['run_id']}?country_id={country}")
        report['countries'].append({'country':country,'wall_seconds':wall,'solver':p['solver'],'impact':p['impact'],
            'capacity':p['preview']['capacity_by_resource'],'deficit':p['preview']['deficit_by_resource']})
        print(country,p['solver']['status'],round(wall,2),'seconds',flush=True)
    scenario=call('/scenarios',{'country_id':'IN','state_id':'MH','district_id':'MH-PUNE','scenario_type':'DENGUE_SURGE','severity':'severe','duration':14})
    sid=scenario['scenario']['scenario_id']
    before=call('/facilities/IN-MH-PUNE-003?country_id=IN')
    for scope in ['district','state','national']:
        body={'country_id':'IN','state_id':'MH','district_id':'MH-PUNE','scenario_id':sid,'scope':scope}
        preview=call('/optimization/preview',body)
        start=perf_counter();p=call('/optimization/redistribution',body);wall=perf_counter()-start
        assert preview['snapshot_id']==p['preview']['snapshot_id']
        assert preview['scenario_snapshot_id']==scenario['scenario']['baseline_snapshot_id']
        assert p['impact']['after']['target_deficit'] > 0  # Existing snapshot cannot safely donate.
        assert p['message']=='Network resources are insufficient to completely resolve this shortage.'
        assert p['impact']['new_donor_risks']==0
        assert call(f'/scenarios/{sid}?country_id=IN')==scenario
        assert call('/facilities/IN-MH-PUNE-003?country_id=IN')==before
        report['pune'][scope]={'wall_seconds':wall,'preview':p['preview'],'solver':p['solver'],
            'impact':p['impact'],'greedy':p['greedy'],'transfers':p['transfers'],'run_id':p['run_id'], 'message':p['message']}
        call(f"/optimization/runs/{p['run_id']}?country_id=IN",method='DELETE')
        assert call(f'/scenarios/{sid}?country_id=IN')==scenario
        missing(f"/optimization/runs/{p['run_id']}?country_id=IN")
        print('Pune',scope,p['solver']['status'],round(wall,2),'seconds',flush=True)
    p=call('/optimization/redistribution',{'country_id':'IN','state_id':'MH','district_id':'MH-PUNE','scenario_id':sid})
    report['demo']={'scenario_id':sid,'run_id':p['run_id'],'url':f"http://127.0.0.1:4200/redistribution?country_id=IN&state_id=MH&district_id=MH-PUNE&scenario_id={sid}&run_id={p['run_id']}"}
    report['checks']=['5 country baseline plans','5 cross-country run rejections','immutable inventory and scenario','GET exact roundtrip','DELETE 204 followed by 404','Pune district/state/national shortage','per-resource conservation','no new donor risk','actual CP-SAT and greedy comparison']
    Path('docs/evaluation/phase5-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report['demo']),flush=True)


if __name__=='__main__': run()
