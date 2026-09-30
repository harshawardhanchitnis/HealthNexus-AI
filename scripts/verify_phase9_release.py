"""Actual production-container HTTP release gates; zero Gemini, no retraining."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def verify(frontend, backend):
    def fetch(base, path, body=None):
        req = Request(base + path, data=json.dumps(body).encode() if body else None,
                      headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=180) as response:
            assert response.status == 200 or body and response.status == 201
            return response.read()

    def call(base, path, body=None):
        return json.loads(fetch(base, path, body))

    report = {'status': 'PASS', 'live_gemini_requests': 0, 'profiles': {}, 'frontend': frontend,
              'backend': backend, 'liveness': call(backend, '/health'),
              'readiness': call(backend, '/readiness'), 'spa_deep_links': []}
    assert report['readiness']['status'] == 'ready'
    assert not report['readiness']['gemini']['enabled']
    index = fetch(frontend, '/')
    for route in ('geospatial', 'overview', 'network', 'facilities', 'supply', 'alerts',
                  'facilities/IN-MH-PUNE-003', 'forecasts', 'warnings', 'emergency',
                  'redistribution', 'copilot', 'brics', 'model-performance', 'data-sources', 'about'):
        assert fetch(frontend, '/' + route) == index, route
        report['spa_deep_links'].append(route)
    assert call(frontend, '/api/health')['status'] == 'ok'
    assert b'<html' not in fetch(frontend, '/maplibre/maplibre-gl-worker.mjs')[:100]
    for profile in ('redistribution-ready', 'constrained'):
        context = dict(country_id='IN', profile=profile, state_id='MH', district_id='MH-PUNE')
        snapshot_before = fetch(frontend, '/api/facilities?' + urlencode(context))
        scenario = call(frontend, '/api/scenarios', context | dict(
            scenario_type='DENGUE_SURGE', severity='severe', duration=14, seed=42))
        sid = scenario['scenario']['scenario_id']
        scenario_path = '/api/scenarios/' + sid + '?' + urlencode(context)
        scenario_before = fetch(frontend, scenario_path)
        results = {}
        for scope in ('district', 'cross_district'):
            plan = call(frontend, '/api/optimization/redistribution', context | dict(scope=scope, scenario_id=sid))
            actual = (plan['preview']['total_deficit'], plan['preview']['safe_capacity'],
                      plan['impact']['transferred_units'], len(plan['transfers']), plan['impact']['after']['target_deficit'])
            expected = (30230, 0, 0, 0, 30230) if profile == 'constrained' else (
                (41763, 17745, 15679, 10, 26084) if scope == 'district' else (41763, 9307, 9307, 10, 32456))
            assert actual == expected, (profile, scope, actual)
            assert plan['impact']['donor_safety_violations'] == plan['impact']['new_donor_risks'] == 0
            assert all(c['before'] == c['after'] for c in plan['impact']['conservation'].values())
            query = context | dict(mode='redistribution', donor_scope=scope, scenario_id=sid, run_id=plan['run_id'])
            view = call(frontend, '/api/geospatial?' + urlencode(query))
            assert len(view['transfers']['features']) == actual[3]
            assert view['metadata']['map_coordinate_version'] == 'illustrative-district-v1'
            by_id = {f['id']: f for f in view['facilities']['features']}
            for lane, transfer in zip(view['transfers']['features'], plan['transfers']):
                assert lane['properties']['distance_km'] == transfer['distance_km']
                assert lane['properties']['quantity'] == transfer['quantity']
                assert lane['geometry']['coordinates'] == [by_id[transfer['donor_id']]['geometry']['coordinates'],
                                                          by_id[transfer['receiver_id']]['geometry']['coordinates']]
                if scope == 'cross_district':
                    assert transfer['donor_district_id'] == 'MH-NAGPUR'
                    assert transfer['receiver_district_id'] == 'MH-PUNE'
                    assert 600 < lane['properties']['map_distance_km'] < 700
            distances = [f['properties']['map_distance_km'] for f in view['transfers']['features']]
            results[scope] = dict(target_before=actual[0], safe_capacity=actual[1], recommended_items=actual[2],
                                 lanes=actual[3], unresolved=actual[4], donor_violations=0, new_donor_risks=0,
                                 map_distance_km_range=[min(distances), max(distances)] if distances else [],
                                 url=frontend + '/geospatial?' + urlencode(query))
        assert fetch(frontend, '/api/facilities?' + urlencode(context)) == snapshot_before
        assert fetch(frontend, scenario_path) == scenario_before
        report['profiles'][profile] = results
    report['baseline_and_scenario_immutable'] = True
    report['frontend_api_connectivity'] = 'PASS'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', default='http://127.0.0.1:14200')
    parser.add_argument('--backend', default='http://127.0.0.1:18000')
    parser.add_argument('--output', type=Path, default=Path('docs/evaluation/phase9-docker.json'))
    args = parser.parse_args()
    report = verify(args.frontend, args.backend)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
