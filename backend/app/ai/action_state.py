"""Server-owned advisory state and bounded operational-language validation.

This is a deterministic domain guard, not general natural-language understanding.
It changes neither numerical evidence validation nor an operational calculation.
"""
import re
import unicodedata
from typing import Literal
from pydantic import BaseModel,ConfigDict,ValidationError
from app.ai.client import CopilotError

VERSION='advisory-action-state-v1'
PLAN_TOOLS=frozenset(('optimize_redistribution','get_optimization_result'))


class PlanActionState(BaseModel):
    model_config=ConfigDict(frozen=True,extra='forbid')
    plan_mode: Literal['advisory']='advisory'
    physical_execution: Literal[False]=False
    externally_authorized: Literal[False]=False
    hospital_contacted: Literal[False]=False
    real_world_transfer_status: Literal['not_executed']='not_executed'


def advisory_state():
    # These tools have no hospital-contact, authorization or physical dispatch adapter.
    return PlanActionState().model_dump()


def normalize(text):
    text=unicodedata.normalize('NFKC',text).casefold().replace('\u2019',"'")
    text=''.join(c for c in text if unicodedata.category(c)!='Cf')
    text=re.sub(r"\b(can|do|does|did|has|have|had|is|are|was|were|will|would|could|should)n['’]t\b",r'\1 not',text)
    text=re.sub(r"\bwon't\b",'will not',text)
    text=re.sub(r"\bcan't\b",'can not',text)
    text=re.sub(r'[_\-\u2010-\u2015]', ' ',text)
    text=re.sub(r'[*`#]', '',text)
    return re.sub(r'\s+',' ',text).strip()


# Subjects/objects identify this narrow logistics domain. Mathematical completion
# is distinct from completing a transfer, approval, or real-world redistribution.
ENTITIES=re.compile(r'\b(?:transfers?|redistribut\w*|resources?|supplies|items?|medicines?|inventory|shipments?|plans?|hospitals?|facilities|lanes?|operational success)\b')
OPERATIONS=re.compile(r'\b(?:execut(?:e|es|ed|ing)|dispatch(?:ed|ing|es)?|deliver(?:ed|ing|s)?|'
    r'mov(?:e|es|ed|ing)|authori[sz](?:e|es|ed|ing)|approv(?:e|es|ed|ing)|implement(?:ed|ing|s)?|'
    r'complet(?:e|es|ed|ing)|redistribut(?:e|es|ed|ing)|shipp(?:ed|ing)|sent|send(?:ing|s)?|'
    r'transferred|transferring|contact(?:ed|ing|s)?|received|arrived|carried out|put into effect|signed off|gave (?:the )?green light|'
    r'took place|occurred|underway|in progress|finished|operational success)\b')
MATH_COMPLETION=re.compile(r'\b(?:optimizer|solver|optimization|simulation|calculation|computation)\s+(?:(?:has|had|was|is|successfully)\s+){0,3}$')
ADVISORY=re.compile(r'\b(?:advisory|recommend(?:s|ed|ing|ation|ations)?|propos(?:ed|al|als)|planned)\b')
NON_ACTION_TRANSFER=re.compile(r'\b(?:recommend(?:s|ed|ing)?|propos(?:e|es|ed|ing))\s+(?:(?:safe|safely|to)\s+){0,2}$')
NOMINAL_ACTION=re.compile(r'\b(?:execution|dispatch|delivery|movement|authorization|approval|implementation)\b.{0,60}\b(?:successful|confirmed|complete|occurred|underway|in progress)\b')
DENIAL=re.compile(r'\b(?:not|never|none|nothing|neither)\b|\bno\s+(?:\w+\s+){0,2}(?:transfers?|resources?|supplies|items?|medicines?|hospitals?|approval|authorization|physical|execution|movement)\b|\bwithout\s+(?:being\s+)?(?:physically\s+)?$')
TOTAL_RESOLUTION=re.compile(r'\b(?:eliminat\w*|resolv\w*|solv\w*|remov\w*|prevent\w*)\s+(?:\w+\s+){0,3}(?:all|every)\s+(?:remaining\s+)?(?:shortages?|deficits?|unmet (?:demand|need)|stock outs?)\b|'
    r'\b(?:all|every)\s+(?:shortages?|deficits?|stock outs?)\s+(?:\w+\s+){0,3}(?:solved|resolved|eliminated|prevented)\b|\b(?:network|system)\s+(?:is\s+)?fully resilient\b')


def denied(clause,start):
    # Negation must belong to the local predicate; contrast clauses are split first.
    before=clause[:start]
    tokens=list(re.finditer(r"\b\w+\b",before))
    nearby=before[tokens[-8].start():] if len(tokens)>8 else before
    nearby=re.sub(r'\bnot\s+(?:only|just)\b|\bno\s+doubt\b','',nearby)
    return bool(DENIAL.search(nearby))


def check_action_claim(text,references,records,claim_field='claim.text'):
    """Resolve state from server payloads, never solver status or model assertions."""
    states=[]
    for eid,record in records.items():
        if record['tool'] not in PLAN_TOOLS:continue
        raw=record['payload'].get('action_state')
        if raw is not None:
            try:state=PlanActionState.model_validate(raw).model_dump()
            except ValidationError:
                raise CopilotError('action_state_invalid','Authoritative action state is invalid.',422) from None
            states.append((eid,state))
    text=normalize(text)
    fields={ref['field'] for ref in references if ref['tool'] in PLAN_TOOLS}
    required=set()
    action_denial=False;advisory_claim=bool(ADVISORY.search(text) or re.search(
        r'\b(?:safe redistribution|transfers?|redistribution plan)\b.{0,30}\b(?:reduce[sd]?|reliev\w*)\b.{0,15}\bpressure\b',text))
    if advisory_claim:required.add('plan_mode')
    if re.search(r'\b(?:physical execution|real world transfer status)\b',text):required.add('physical_execution')
    if re.search(r'\b(?:external authorization|approval)\b',text):required.add('externally_authorized')
    for clause in re.split(r'[.,;!?]|\b(?:and|but|however|yet|despite|although|whereas|while)\b',text):
        entities=bool(ENTITIES.search(clause))
        if not entities and not states and not (re.search(r'\b(?:it|they|these|those)\b',clause) and ENTITIES.search(text)):continue
        for match in sorted([*OPERATIONS.finditer(clause),*NOMINAL_ACTION.finditer(clause)],key=lambda m:m.start()):
            verb=match.group()
            # "recommended redistribution" is an object, not a completed action.
            if verb in ('redistribute','redistributes','redistributing','transferring') and NON_ACTION_TRANSFER.search(clause[:match.start()]):continue
            if verb.startswith('complet') and MATH_COMPLETION.search(clause[:match.start()]):continue
            if denied(clause,match.start()):
                action_denial=True
                required.add('externally_authorized' if re.search(r'authori[sz]|approv|signed off|green light',verb)
                    else 'hospital_contacted' if verb.startswith('contact') else 'physical_execution')
                continue
            fail('unsupported_execution_or_authorization',clause.strip(),states,claim_field,text)
    if states and 'action_state' not in fields:
        for facet in required:
            choices={f'action_state.{facet}'}
            if facet=='physical_execution':choices.add('action_state.real_world_transfer_status')
            if not fields & choices:fail('action_state_citation_required',text,states,claim_field,text)
    if action_denial and not states:
        fail('action_state_unconfirmed',text,states,claim_field,text)
    # Complete mathematical optimization does not imply complete shortage relief.
    unresolved=any(record['tool'] in PLAN_TOOLS and record['payload'].get('impact',{}).get(
        'after',{}).get('target_deficit',0)>0 for record in records.values())
    if unresolved:
        for clause in re.split(r'[.;!?]|\b(?:but|however|yet)\b',text):
            match=TOTAL_RESOLUTION.search(clause)
            if match and not denied(clause,match.start()):
                fail('unresolved_shortages_remain',clause.strip(),states,claim_field,text)
    return {'action_state_validation':'PASS','unsupported_execution_claims':0,
        'authoritative_action_states':[state for _,state in states]}


def fail(reason,phrase,states,field,text):
    error=CopilotError('unsafe_claim','Gemini returned an unsupported operational action-state claim.',422)
    error.action_state_diagnostic={'reason':reason,'claim_field':field,'normalized_claim':text,
        'failed_phrase':phrase,'authoritative_action_states':[s for _,s in states]}
    raise error
