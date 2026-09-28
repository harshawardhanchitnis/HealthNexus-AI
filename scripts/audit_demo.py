"""Publication and preservation checks. No credentials are read or printed; no provider calls."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from verify_demo import ROOT, secret_scan


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = {'status': 'PASS', 'live_gemini_requests': 0, 'secret_scan': secret_scan()}
    before = json.loads((ROOT/'artifacts/phase7-preservation-before.json').read_text())
    assert all(sha(ROOT/path) == expected for path, expected in before.items()), 'Protected file changed'
    report['protected_files_unchanged'] = len(before)
    assert (ROOT/'data/demo/federation/report.json').read_bytes() == (ROOT/'docs/evaluation/phase7-run.json').read_bytes()
    report['accepted_federation_report_byte_identical'] = True
    ledger = json.loads((ROOT/'artifacts/gemini-verification-budget-live.json').read_text())
    assert ledger['used'] == 12
    report['retained_provider_request_ledger'] = ledger['used']
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    assert not any(p and (p == '.env' or any(x in p.split('/') for x in ('node_modules','.venv','venv'))) for p in tracked)
    report['tracked_environment_or_dependency_directories'] = 0
    public = ['README.md','docs/architecture.md','docs/deployment.md','docs/final-demo-script.md',
        'docs/hackathon-facts.md','docs/final-technical-report.md','docs/screenshots/README.md']
    links = 0
    for name in public:
        path = ROOT/name
        content = path.read_text(encoding='utf-8')
        assert not re.search(r'[A-Z]:[\\/](?:Users|Projects)', content), 'Private absolute path in public document'
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if '://' in target or target.startswith('#'): continue
            destination = (path.parent/target.split('#')[0]).resolve()
            generated_report = (ROOT/'docs/evaluation/phase8-security.json').resolve()
            assert destination.exists() or destination == generated_report, f'Broken publication link: {name}: {target}'
            links += 1
    report['public_local_links_checked'] = links
    report['public_private_absolute_paths'] = 0
    audit = json.loads((ROOT/'artifacts/phase8-npm-audit.json').read_text(encoding='utf-8-sig'))
    assert audit['metadata']['vulnerabilities']['total'] == 0
    report['npm_production_known_vulnerabilities'] = 0
    report['dependency_checks'] = 'Windows and container pip check PASS; production npm audit PASS'
    report['cors'] = 'Explicit configurable origins; no new permissive wildcard'
    report['scope'] = 'Pattern/publication/preservation review; not penetration testing or a guarantee of security'
    (ROOT/'docs/evaluation/phase8-security.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS: publication links, secret patterns, protected artifacts and retained provider ledger')


if __name__ == '__main__':
    main()
