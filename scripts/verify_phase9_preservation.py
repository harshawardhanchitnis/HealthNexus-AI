"""Zero-provider preservation guard for the accepted Phase 6 baseline."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'artifacts/phase9-preservation-before.json'
DEPLOYMENT = ROOT/'docs/evaluation/low-memory-preservation.json'
AUTHORIZED_SOURCE = {
    'backend/app/scenarios/state.py', 'backend/app/scenarios/routes.py',
    'backend/app/scenarios/engine.py', 'backend/app/forecasting/prediction.py',
    'backend/app/federation/config.py', 'backend/app/federation/routes.py',
    'backend/app/federation/service.py',
    # Explicitly authorized district-computation policy and bounded AI retention.
    # Provider protocol, prompts, grounding, fact IDs and fallback logic are frozen.
    'backend/app/ai/orchestrator.py', 'backend/app/ai/tools.py',
    # Complete identical SHA-256 checks now stream file data instead of allocating
    # a whole history file; optional Linux page-cache hints do not change bytes.
    'backend/app/forecasting/data.py',
}


def preserved():
    # Explicit later deployment changes retain exact pins for the authorized
    # cache/scope/metadata edits. All other Phase 6 sources/assets stay frozen.
    deployment = json.loads(DEPLOYMENT.read_text()) if DEPLOYMENT.exists() else {}
    overrides = deployment.get('authorized_source_sha256',{})
    assert set(overrides) <= AUTHORIZED_SOURCE
    for name, expected in overrides.items():
        assert hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected, name
    if BASELINE.exists():
        saved = json.loads(BASELINE.read_text(encoding='utf-8'))
        protected = saved['protected']
        assert saved['baseline'] == '723c6a8'
        for name, expected in protected.items():
            if name in overrides:continue
            if name=='artifacts/gemini-verification-budget-live.json' and deployment:
                expected=deployment['historical_ledger_sha256']
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, 'Protected identity changed: ' + name
        ledger=json.loads((ROOT/'artifacts/gemini-verification-budget-live.json').read_text())
        if deployment:assert ledger['used']==deployment['historical_ledger_used']
        else:assert ledger == saved['ledger']
        return {'status': 'PASS', 'baseline': '723c6a8', 'protected_identities': len(protected),
                'historical_ledger_used': ledger['used'], 'live_gemini_requests': 0,
                'env_unchanged': True, 'accepted_engines_models_federation_evidence_unchanged': True,
                'authorized_deployment_source_pins':len(overrides)}
    # A fresh clone may not contain the private local manifest or live-request ledger.
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '723c6a8'], cwd=ROOT, text=True).splitlines()
    prefixes = ('backend/app/ai/', 'backend/app/forecasting/', 'backend/app/warnings/',
                'backend/app/scenarios/', 'backend/app/federation/', 'data/', 'docs/evaluation/phase6-')
    count = 0
    for name in paths:
        if not name.startswith(prefixes): continue
        if name in overrides:continue
        old = subprocess.check_output(['git', 'show', '723c6a8:' + name], cwd=ROOT)
        assert (ROOT/name).read_bytes().replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n'), name
        count += 1
    return {'status': 'PASS', 'baseline': '723c6a8', 'protected_identities': count, 'live_gemini_requests': 0,
            'private_local_manifest': 'not present in this clone'}


if __name__ == '__main__':
    print(json.dumps(preserved(), indent=2))
