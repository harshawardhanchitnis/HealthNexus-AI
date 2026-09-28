"""Live API profile isolation checks; keep two freshly solved Pune demos."""
import json
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE='http://127.0.0.1:8000/api'

def call(path, body=None, method=None):
    request=Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,
        method=method or ('POST' if body is not None else 'GET'),headers={'Content-Type':'application/json'})
    with urlopen(request,timeout=300) as response:
        payload=response.read()
        return json.loads(payload) if payload else None

def rejected(path, code, body=None):
    try: call(path,body)
    except HTTPError as error: assert error.code==code
    else: raise AssertionError('Expected country/profile validation failure')

def main():
    report={'country_profiles':[],'demos':{}}
    rejected('/overview?profile=unknown',422)
    rejected('/scenarios?profile=constrained',422,{'country_id':'IN','profile':'redistribution-ready','scenario_type':'DENGUE_SURGE'})
    for profile in ['constrained','redistribution-ready']:
        for country in ['IN','BR','RU','CN','ZA']:
            query=f'country_id={country}&profile={profile}'
            facilities=call('/facilities?'+query+'&limit=250')['items']
            assert all(f['country_id']==country for f in facilities)
            facility=next((f for f in facilities if f['district_id']=='MH-PUNE'),facilities[0])
            forecast=call(f"/forecasts/facilities/{facility['id']}/medicines/IVF?{query}")
            assert forecast['provenance']['operational_profile']==profile
            before=call('/inventory?'+query)
            body={'country_id':country,'profile':profile,'state_id':facility['state_id'],
                'district_id':facility['district_id'],'scope':'district' if facility['district_id'] else 'state'}
            result=call('/optimization/redistribution',body)
            assert result['impact']['donor_safety_violations']==result['impact']['new_donor_risks']==0
            assert before==call('/inventory?'+query)
            rid=result['run_id']
            assert call(f'/optimization/runs/{rid}?{query}')==result
            other='BR' if country=='IN' else 'IN'
            opposite='constrained' if profile=='redistribution-ready' else 'redistribution-ready'
            rejected(f'/optimization/runs/{rid}?country_id={other}&profile={profile}',404)
            rejected(f'/optimization/runs/{rid}?country_id={country}&profile={opposite}',404)
            call(f'/optimization/runs/{rid}?{query}',method='DELETE')
            report['country_profiles'].append({'country':country,'profile':profile,'status':result['solver']['status'],'isolation':'passed'})
        body={'country_id':'IN','profile':profile,'state_id':'MH','district_id':'MH-PUNE','scenario_type':'DENGUE_SURGE',
            'severity':'severe','duration':14,'seed':42}
        scenario=call('/scenarios',body);sid=scenario['scenario']['scenario_id']
        req={k:body[k] for k in ['country_id','profile','state_id','district_id']}
        req.update({'scenario_id':sid,'scope':'district'})
        preview=call('/optimization/preview',req)
        start=perf_counter();result=call('/optimization/redistribution',req);elapsed=perf_counter()-start
        assert result['preview']['snapshot_id']==preview['snapshot_id']
        assert call(f'/scenarios/{sid}?country_id=IN&profile={profile}')==scenario
        if profile=='constrained':
            assert (preview['total_deficit'],preview['safe_capacity'],result['impact']['transferred_units'])==(30230,0,0)
        else:
            assert result['impact']['transferred_units']>0 and result['impact']['after']['target_deficit']<preview['total_deficit']
        rid=result['run_id']
        report['demos'][profile]={'scenario_id':sid,'run_id':rid,'http_wall_seconds':elapsed,
            'target':preview['total_deficit'],'safe_capacity':preview['safe_capacity'],'impact':result['impact'],
            'solver':result['solver'],'greedy':result['greedy'],
            'url':f'http://127.0.0.1:4200/redistribution?profile={profile}&country_id=IN&state_id=MH&district_id=MH-PUNE&scenario_id={sid}&run_id={rid}'}
        print(profile,result['solver']['status'],result['impact']['transferred_units'],flush=True)
    Path('docs/evaluation/phase55-live-api.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

if __name__=='__main__':main()
