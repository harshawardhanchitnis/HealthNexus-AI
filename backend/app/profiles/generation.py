"""Replay inventory policy over preserved demand. No optimizer or forecast fitting."""
import gzip
import hashlib
import json
import math
import random
from datetime import timedelta
from pathlib import Path
from app.core.config import ROOT
from app.models.network import Snapshot, StockDay, ScheduledReceipt, Alert, Status
from app.forecasting.data import digest, facility_hash, series_from, TARGETS
from app.profiles.config import VERSION, ROLES, COVER_DAYS, REVIEW_CYCLE, LEAD_DAYS, folder, legacy_snapshot, NOTICES
from app.simulation.generator import inventory_status, RANK


def demand_signature(snapshot):
    # Precisely the features/targets used by Phase 3: full requested histories and
    # facility context. Consumption is censored and deliberately not a target.
    h = hashlib.sha256()
    for target in TARGETS:
        for context, values in series_from(snapshot, target):
            h.update(json.dumps(context,sort_keys=True).encode())
            h.update(values.tobytes())
    return h.hexdigest()


def replay(source):
    data = source.model_copy(deep=True)
    data.operational_profile = 'redistribution-ready'
    data.profile_version = VERSION
    data.profile_purpose = 'hackathon logistics stress-test'
    roles = {}
    for index, f in enumerate(data.facilities):
        role = ROLES[index % len(ROLES)]
        roles[f.id] = role
        for activity in f.history:
            activity.medicine_units = 0
        for item in f.inventory:
            rng = random.Random(f'{data.seed}:{f.id}:{item.medicine_id}:{VERSION}')
            target_days = rng.randint(*COVER_DAYS[role])
            old = item.ledger
            opening = math.ceil(old[0].requested * target_days)
            ledger, orders = [], []
            for day, original in enumerate(old):
                recent = [r.requested for r in old[max(0,day-7):day]]
                expected = sum(recent)/len(recent) if recent else original.requested
                received = sum(o['quantity'] for o in orders if o['arrival'] == day)
                orders = [o for o in orders if o['arrival'] != day]
                if day % REVIEW_CYCLE == 0:
                    quantity = max(0, math.ceil(target_days*expected)-opening-received-sum(o['quantity'] for o in orders))
                    if quantity:
                        orders.append({'ordered':day,'arrival':day+LEAD_DAYS,'quantity':quantity})
                consumed = min(original.requested, opening+received)
                closing = opening+received-consumed
                ledger.append(StockDay(date=original.date,opening=opening,received=received,
                    requested=original.requested,consumed=consumed,unmet_demand=original.requested-consumed,
                    closing=closing,safety_stock=original.safety_stock,scheduled_receipts=received))
                f.history[day].medicine_units += consumed
                opening = closing
            last = ledger[-1]
            item.ledger = ledger
            item.opening_stock, item.units_received, item.units_consumed, item.current_stock = last.opening,last.received,last.consumed,last.closing
            # Original safety threshold is preserved, not weakened to manufacture donors.
            item.average_daily_consumption = max(.01,round(sum(r.consumed for r in ledger[-7:])/7,2))
            item.days_of_cover = round(item.current_stock/item.average_daily_consumption,1)
            item.status = inventory_status(item.days_of_cover)
            item.scheduled_deliveries = [ScheduledReceipt(ordered_at=old[0].date+timedelta(days=o['ordered']),
                expected_at=old[0].date+timedelta(days=o['arrival']),quantity=o['quantity'],lead_time_days=LEAD_DAYS) for o in orders]
        f.status = max([i.status for i in f.inventory]+[Status.AT_RISK if f.staff.present/f.staff.scheduled < .8 else Status.HEALTHY],key=lambda v:RANK[v])
        f.resilience_score = [96,78,55,28][RANK[f.status]]
    data.inventory_roles = roles
    data.alerts = [a for a in data.alerts if a.resource == 'Staff']
    for f in data.facilities:
        for item in f.inventory:
            if item.status in (Status.AT_RISK,Status.CRITICAL):
                data.alerts.append(Alert(id=f'{f.id}-{item.medicine_id}',facility_id=f.id,facility_name=f.name,
                    state_id=f.state_id,district_id=f.district_id,country_id=f.country_id,provenance_id=f'risk-{data.country}-v2',
                    severity=item.status,resource=item.name,title=f'Low stock cover · {item.name}',
                    explanation=f'{item.current_stock} simulated units; {item.days_of_cover} days of trailing consumption cover under {roles[f.id]} replenishment policy.',
                    recommended_action='Review projected unmet demand and safe domestic redistribution.'))
    data.alerts.sort(key=lambda a:-RANK[a.severity])
    return Snapshot.model_validate(data.model_dump())


def write_json(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,sort_keys=True,indent=2),encoding='utf-8')
    temp.replace(path)


def generate_profile(country, profile, root: Path = ROOT):
    dest = folder(profile,country,root)
    source_path = root/'data/generated/history'/f'{country}.json.gz'
    source_snapshot = legacy_snapshot(country,root)
    if not source_path.exists() or not source_snapshot.exists():
        raise ValueError('Generate the original demand history and trained artifacts first; profile generation never overwrites them')
    original = Snapshot.model_validate_json(gzip.decompress(source_path.read_bytes()))
    current = Snapshot.model_validate_json(source_snapshot.read_bytes())
    if (original.country,original.as_of,original.seed) != (country,current.as_of,current.seed):
        raise ValueError('Original history/snapshot identity mismatch')
    data = original.model_copy(deep=True) if profile == 'constrained' else replay(original)
    data.operational_profile, data.profile_version = profile, VERSION
    if demand_signature(original) != demand_signature(data):
        raise ValueError('Requested-demand training inputs changed; model reuse is prohibited')
    raw_history = data.model_dump_json().encode()
    for f in data.facilities:
        f.history = f.history[-28:]
        for item in f.inventory:
            item.ledger = item.ledger[-28:]
    base_hashes = {f.id:facility_hash(f) for f in current.facilities}
    if profile == 'constrained' and base_hashes != {f.id:facility_hash(f) for f in data.facilities}:
        raise ValueError('Preserved constrained history does not match current snapshot')
    from app.forecasting.prediction import load_bundle
    bundle = load_bundle(country,root)
    if bundle['manifest']['facility_hashes'] != base_hashes or bundle['manifest']['history_sha256'] != digest(source_path):
        raise ValueError('Original model artifacts are stale for the constrained source')
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'history.json.gz').write_bytes(gzip.compress(raw_history,compresslevel=5,mtime=0))
    (dest/'network.json').write_text(data.model_dump_json(),encoding='utf-8')
    compatibility = {'profile':profile,'profile_version':VERSION,'country':country,'seed':data.seed,'as_of':str(data.as_of),
        'source_snapshot_sha256':digest(source_snapshot),'source_history_sha256':digest(source_path),
        'history_sha256':digest(dest/'history.json.gz'),'snapshot_sha256':digest(dest/'network.json'),
        'model_sha256':digest(root/'artifacts/models'/country/'bundle.joblib'),'model_version':bundle['report']['model_version'],
        'facility_hashes':{f.id:facility_hash(f) for f in data.facilities},'demand_signature':demand_signature(original),
        'weights_retrained':False,'roles':data.inventory_roles,'coverage_days':COVER_DAYS,'review_cycle':REVIEW_CYCLE,'lead_days':LEAD_DAYS,
        'notice':NOTICES[profile]}
    write_json(dest/'compatibility.json',compatibility)
    return compatibility
