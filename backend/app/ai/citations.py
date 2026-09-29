"""Resolve references against fresh tool outputs, rejecting fabricated fields/numbers."""
import json
import re
from app.ai.schemas import Evidence
from app.ai.client import CopilotError
from app.ai.numeric import NUMBER, canonical, numeric_sources, field_unit
from app.ai.action_state import check_action_claim


def resolve(payload, path):
    value = payload
    for part in path.split('.'):
        value = value[int(part)] if isinstance(value,list) else value[part]
    return value


def sanitize_diagnostic(value, secret=None):
    text=json.dumps(value,ensure_ascii=False)
    if secret: text=text.replace(secret,'[REDACTED]')
    text=re.sub(r'AIza[0-9A-Za-z_-]{35}','[REDACTED]',text)
    return json.loads(text)


def build_evidence(draft, records, context=None, origin=None):
    evidence, seen = [], set()
    claims=[('situation.text',draft.situation)] + [(f'{name}.{i}.text',claim)
        for name in ('key_risks','recommended_actions','remaining_gaps')
        for i,claim in enumerate(getattr(draft,name))]
    for claim_field,claim in claims:
        supported=[];references=[]
        for reference in claim.references:
            try:
                record = records[reference.evidence_id]
                payload=record['payload']
                if context is not None:
                    scope=payload['context']
                    if scope['country_id']!=context.country_id or (scope['profile']!=context.profile and not getattr(context,'compare_profiles',False)):
                        raise ValueError('Evidence belongs to another request context')
                    if any(value!=getattr(context,key,None) for key,value in record.get('request_scope',{}).items()):
                        raise ValueError('Evidence belongs to another geography')
                if origin is not None and payload.get('context',{}).get('origin')!=str(origin):
                    raise ValueError('Evidence belongs to another forecast origin')
                value = resolve(record['payload'], reference.field)
                if len(json.dumps(value)) > 1500:
                    raise ValueError('Reference must select a concise field, not an entire result')
            except (KeyError,IndexError,ValueError,TypeError):
                raise CopilotError('evidence_invalid', 'Gemini returned an unsupported evidence reference. Retry with a narrower question.') from None
            supported.extend(numeric_sources(value,reference.field,record['tool'],payload))
            references.append({'evidence_id':reference.evidence_id,'tool':record['tool'],
                'field':reference.field,'value':value,'unit':field_unit(record['tool'],reference.field,payload),
                'context':payload.get('context',{})})
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
        unsupported=[]
        for match in NUMBER.finditer(claim.text):
            percent=bool(re.match(r'\s*(?:%|percent\b)',claim.text[match.end():],re.IGNORECASE))
            if not any(canonical(match.group())==number and (not percent or unit=='%') for number,unit in supported):
                unsupported.append(match.group())
        if unsupported:
            error=CopilotError('unsupported_number', 'Gemini stated a number not supported by its cited tool fields. Retry with a narrower question.')
            error.grounding_diagnostic=sanitize_diagnostic({'claim_field':claim_field,
                'claim_text':claim.text,'unsupported_numbers':unsupported,'references':references,
                'rule':'Exact cited values only; no rounding, arithmetic or implicit unit conversion.'})
            raise error
        # A model must not strengthen FEASIBLE into OPTIMAL or claim executed transfers.
        text = claim.text.lower()
        if 'optimal' in text:
            statuses = [resolve(records[r.evidence_id]['payload'],r.field) for r in claim.references]
            if 'OPTIMAL' not in statuses:
                raise CopilotError('solver_terminology', 'Gemini overstated the available solver evidence.')
        check_action_claim(claim.text,references,records,claim_field)
        if re.search(r'\b(prescribe|dosage)\b', text):
            raise CopilotError('unsafe_claim', 'Gemini returned wording outside administrative planning scope.')
    return evidence
