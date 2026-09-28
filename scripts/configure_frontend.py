"""Prepare a public HTTPS API URL in the built frontend; does not deploy anything."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--api-base',required=True);args=parser.parse_args()
    url=urlsplit(args.api_base)
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('','/'):
        parser.error('Use an HTTPS origin without credentials, path, query or fragment')
    path=ROOT/'frontend/dist/healthnexus-frontend/browser/runtime-config.js'
    if not path.exists():parser.error('Run the Angular production build first')
    path.write_text('window.HEALTHNEXUS_CONFIG = '+json.dumps({'apiBaseUrl':args.api_base.rstrip('/')})+';\n',encoding='utf-8')
    print('Public API origin configured in production build. No cloud resource changed.')
