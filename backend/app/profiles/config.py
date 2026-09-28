from typing import Literal
from pathlib import Path
from app.core.config import ROOT

ProfileID = Literal['constrained', 'redistribution-ready']
VERSION = 'inventory-profile-v1'
ROLES = ('buffer', 'buffer', 'strained', 'balanced', 'strained', 'balanced')
COVER_DAYS = {'buffer': (49, 56), 'balanced': (24, 28), 'strained': (9, 13)}
REVIEW_CYCLE = 7
LEAD_DAYS = 3
NOTICES = {
    'constrained': 'Preserved Phase 5 under-resourced simulation. Redistribution cannot replace missing network supply.',
    'redistribution-ready': 'Intentionally uneven replenishment to evaluate shortage detection and domestic redistribution. Simulated, aggregate-calibrated operations; not live government inventory.',
}


def folder(profile: str, country: str, root: Path = ROOT):
    if profile not in NOTICES or country not in ('IN', 'BR', 'RU', 'CN', 'ZA'):
        raise ValueError('Unsupported operational profile or country')
    return root / 'data/generated/profiles' / profile / country


def legacy_snapshot(country, root=ROOT):
    return root / 'data/generated' / ('network.json' if country == 'IN' else f'nodes/{country}/network.json')
