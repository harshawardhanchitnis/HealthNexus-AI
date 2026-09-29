"""Provider-only narrative boundary; authoritative facts and public schemas stay intact."""
from copy import deepcopy
import json
import re
from app.ai.action_state import PLAN_TOOLS,normalize
from app.ai.client import CopilotError
from app.ai.system_prompt import SYNTHESIS

VERSION='operational-narrative-v1'
ACTION_QUESTION=re.compile(r'\b(?:execution|authorization|approval|dispatch|delivery|hospital contact|transfer status|action state)\b|'
    r'\b(?:have|has|were|was|are|is|did|do|does|will|can)\b.{0,70}\b(?:execut\w*|authori[sz]\w*|approv\w*|dispatch\w*|deliver\w*|implement\w*|mov\w*|contact\w*)\b')
SOLVER_QUESTION=re.compile(r'\b(?:solver|optimality|mathematical optimum|optimization status|optimal|feasible)\b')
ACTION_LANGUAGE=re.compile(r'\b(?:execut\w*|authori[sz]\w*|approv\w*|dispatch\w*|deliver\w*|implement\w*|completed?|completing|'
    r'mov(?:e|es|ed|ing)|carried out|carry out|perform(?:ed|ing|s)?|enact\w*|fulfill\w*|physical execution|real world transfer|hospital contact)\b')
SOLVER_LANGUAGE=re.compile(r'\b(?:optimal\w*|solver)\b')


def status_topics(request):
    text=normalize(request.message)
    return {'action':bool(ACTION_QUESTION.search(text)),'solver':bool(SOLVER_QUESTION.search(text))}


def instruction(request):
    topics=status_topics(request)
    return SYNTHESIS+('\nEXPLICIT STATUS QUESTION: Use only the requested current server-owned status facts, '
        'with exact citations. A false execution/authorization/contact state must remain false. '
        'Mathematical status cannot imply physical action or complete shortage resolution.\n'
        if any(topics.values()) else '\nORDINARY OPERATIONAL NARRATIVE: Explain current pressure, the recommended response, '
        'why it could help, and remaining gaps. Do not narrate execution, approval, authorization, '
        'dispatch, delivery or solver status, even as a denial. These statuses are displayed separately by the server.\n')


def provider_view(catalogue,request):
    """Select provider-facing facts without changing IDs, values or server catalogue."""
    topics=status_topics(request);views=[];visible=set()
    for eid,envelope in catalogue.envelopes.items():
        row=deepcopy(envelope);row.pop('result',None)
        if row['tool'] in PLAN_TOOLS:
            row['facts']=[f for f in row['facts'] if (
                (topics['solver'] or not catalogue.facts[f['fact_id']].path.startswith('solver')) and
                (topics['action'] or not (catalogue.facts[f['fact_id']].path=='action_state' or
                    (catalogue.facts[f['fact_id']].path.startswith('action_state.') and
                        catalogue.facts[f['fact_id']].path!='action_state.plan_mode'))))]
            row['narrative_scope']='Recommendations and gaps; omitted statuses remain server-owned.'
        visible.update(f['fact_id'] for f in row['facts']);views.append(row)
    schema=catalogue.schema()
    def restrict(node):
        if isinstance(node,dict):
            if 'evidence_refs' in node.get('properties',{}):
                node['properties']['evidence_refs']['items']['enum']=[fid for fid in catalogue.facts if fid in visible]
            for value in node.values():restrict(value)
        elif isinstance(node,list):
            for value in node:restrict(value)
    restrict(schema)
    return views,schema


def synthesis_input(catalogue,request,data):
    views,schema=provider_view(catalogue,request)
    if isinstance(data,list):
        # Fulfil the actual native call ID, and supply every current evidence fact.
        transformed=deepcopy(data)
        for item in transformed:
            envelope=json.loads(item['result'][0]['text'])
            row=next(v for v in views if v['evidence_id']==envelope['evidence_id'])
            item['result'][0]['text']=json.dumps({**row,'current_evidence_catalogue':views},ensure_ascii=False)
        return transformed,schema
    return json.dumps({'question':request.message,'context':request.model_dump(exclude={
        'message','request_id','conversation_id'}),'server_prefetched_evidence':views},ensure_ascii=False),schema


def validate_narrative(draft,request,records):
    """Extra intent-scoped guard; exact facts, numbers and action semantics run first."""
    if not any(r['tool'] in PLAN_TOOLS for r in records.values()):return
    topics=status_topics(request)
    for field,claims in [('situation',[draft.situation])]+[(k,getattr(draft,k)) for k in (
            'key_risks','recommended_actions','remaining_gaps')]:
        for index,claim in enumerate(claims):
            text=normalize(claim.text)
            reason=('unsolicited_action_status' if not topics['action'] and ACTION_LANGUAGE.search(text)
                else 'unsolicited_solver_status' if not topics['solver'] and SOLVER_LANGUAGE.search(text) else None)
            if reason:
                error=CopilotError('narrative_scope','Ordinary operational synthesis must explain recommendations and gaps, not unrequested statuses.',422)
                error.narrative_diagnostic={'reason':reason,'claim_field':f'{field}.{index}.text',
                    'claim_text':claim.text,'requested_status_topics':topics}
                raise error
            if SOLVER_LANGUAGE.search(text) and not any(ref.field=='solver.status' and
                    records[ref.evidence_id]['tool'] in PLAN_TOOLS for ref in claim.references):
                raise CopilotError('solver_terminology','Solver terminology requires its current scalar status citation.',422)
