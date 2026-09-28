"""Resolve references against fresh tool outputs, rejecting fabricated fields/numbers."""
import json
import re
from app.ai.schemas import Evidence
from app.ai.client import CopilotError


def resolve(payload, path):
    value = payload
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value,list) else value[part]
    return value


def numeric_forms(value, probability=False):
    found = set()
    if isinstance(value, (float,int)) and not isinstance(value,bool):
        for n in (value, value*100) if probability and 0<=value<=1 else (value,):
            found.update((str(n), f'{n:g}', f'{n:.0f}', f'{n:.1f}', f'{n:.2f}'))
    elif isinstance(value, dict):
        for k,v in value.items(): found.update(numeric_forms(v, 'risk' in k or 'probability' in k))
    elif isinstance(value, list):
        for v in value: found.update(numeric_forms(v, probability))
    elif isinstance(value,str):
        found.update(re.findall(r'\d+(?:\.\d+)?',value))
    return found


def build_evidence(draft, records):
    evidence, seen = [], set()
    for claim in [draft.situation, *draft.key_risks, *draft.recommended_actions, *draft.remaining_gaps]:
        supported = set()
        for reference in claim.references:
            try:
                record = records[reference.evidence_id]
                value = resolve(record['payload'], reference.field)
                if len(json.dumps(value)) > 1500:
                    raise ValueError('Reference must select a concise field, not an entire result')
            except (KeyError,IndexError,ValueError,TypeError):
                raise CopilotError('evidence_invalid', 'Gemini returned an unsupported evidence reference. Retry with a narrower question.') from None
            supported.update(numeric_forms(value, 'risk' in reference.field or 'probability' in reference.field))
            key = (reference.evidence_id, reference.field)
            if key not in seen:
                seen.add(key)
                payload = record['payload']
                unit = payload.get('unit')
                try:
                    parent = resolve(payload, reference.field.rsplit('.',1)[0])
                    if isinstance(parent,dict): unit=parent.get('unit') or unit
                except (KeyError,IndexError,TypeError,ValueError): pass
                evidence.append(Evidence(evidence_id=reference.evidence_id, tool=record['tool'],
                    source_type=record['tool'], source_id=payload.get('run_id') or payload.get('scenario_id'),
                    field=reference.field, value=value, profile=payload['context']['profile'], unit=unit))
        for number in re.findall(r'\d+(?:\.\d+)?', re.sub(r'(?<=\d),(?=\d)', '', claim.text)):
            if number not in supported:
                raise CopilotError('unsupported_number', 'Gemini stated a number not supported by its cited tool fields. Retry with a narrower question.')
        # A model must not strengthen FEASIBLE into OPTIMAL or claim executed transfers.
        text = claim.text.lower()
        if 'optimal' in text:
            statuses = [resolve(records[r.evidence_id]['payload'],r.field) for r in claim.references]
            if 'OPTIMAL' not in statuses:
                raise CopilotError('solver_terminology', 'Gemini overstated the available solver evidence.')
        if re.search(r'\b(executed|dispatched|shipped|delivered|prescribe|dosage)\b', text):
            raise CopilotError('unsafe_claim', 'Gemini returned wording outside administrative planning scope.')
    return evidence
