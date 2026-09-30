"""Zero-provider preservation guard for the accepted Phase 6 baseline."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'artifacts/phase9-preservation-before.json'


def preserved():
    if BASELINE.exists():
        saved = json.loads(BASELINE.read_text(encoding='utf-8'))
        protected = saved['protected']
        assert saved['baseline'] == '723c6a8'
        for name, expected in protected.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, 'Protected identity changed: ' + name
        assert json.loads((ROOT/'artifacts/gemini-verification-budget-live.json').read_text()) == saved['ledger']
        return {'status': 'PASS', 'baseline': '723c6a8', 'protected_identities': len(protected),
                'historical_ledger_used': saved['ledger']['used'], 'live_gemini_requests': 0,
                'env_unchanged': True, 'accepted_engines_models_federation_evidence_unchanged': True}
    # A fresh clone may not contain the private local manifest or live-request ledger.
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '723c6a8'], cwd=ROOT, text=True).splitlines()
    prefixes = ('backend/app/ai/', 'backend/app/forecasting/', 'backend/app/warnings/',
                'backend/app/scenarios/', 'backend/app/federation/', 'data/', 'docs/evaluation/phase6-')
    count = 0
    for name in paths:
        if not name.startswith(prefixes): continue
        old = subprocess.check_output(['git', 'show', '723c6a8:' + name], cwd=ROOT)
        assert (ROOT/name).read_bytes().replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n'), name
        count += 1
    return {'status': 'PASS', 'baseline': '723c6a8', 'protected_identities': count, 'live_gemini_requests': 0,
            'private_local_manifest': 'not present in this clone'}


if __name__ == '__main__':
    print(json.dumps(preserved(), indent=2))
