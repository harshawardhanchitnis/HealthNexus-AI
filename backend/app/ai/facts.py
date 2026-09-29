"""Request-local fact membership. Canonical paths never come from model output."""
from copy import deepcopy
from dataclasses import dataclass
import json
import re
from uuid import uuid4
from app.ai.protocol import compact
from app.ai.numeric import field_unit
from app.ai.schemas import DraftAnswer, FactDraftAnswer
from app.ai.tool_registry import json_schema
from app.ai.citations import resolve, sanitize_diagnostic, build_evidence
from app.ai.client import CopilotError

VERSION='healthnexus-facts-v1'
MAX_FACTS=64


def fact_label(path):
    # Display labels are never used for server resolution; IDs alone select facts.
    return ' / '.join(part.replace('_',' ').capitalize() if not part.isdigit() else f'Item {part}'
        for part in path.split('.'))


def leaves(value,path=''):
    if isinstance(value,dict):
        for key in sorted(value):
            yield from leaves(value[key],f'{path}.{key}' if path else key)
    elif isinstance(value,list):
        for index,item in enumerate(value):yield from leaves(item,f'{path}.{index}')
    elif value is not None:yield path,value


@dataclass(frozen=True)
class Fact:
    fact_id: str
    evidence_id: str
    path: str
    value: object
    unit: str | None
    tool: str
    context: dict


class FactCatalogue:
    def __init__(self,scope=None):
        # Server nonce is independent of caller-provided request IDs and credentials.
        self.scope=scope or uuid4().hex[:16]
        if not re.fullmatch(r'[0-9a-f]{16}',self.scope):raise ValueError('Invalid server fact scope')
        self.facts={};self.envelopes={}

    def envelope(self,eid,tool,payload,*,summary_only=False):
        if eid in self.envelopes:return deepcopy(self.envelopes[eid])
        if not re.fullmatch(r'e[1-9][0-9]*',eid):raise ValueError('Invalid server evidence identity')
        result=compact(tool,payload)
        if summary_only and tool=='get_network_summary':
            result={k:result[k] for k in ('context','summary','warnings','model_version','facilities','facilities_truncated') if k in result}
        candidates=dict(leaves({k:v for k,v in result.items() if k!='context'}))
        # Concise server-owned aggregates retain the existing bounded-reference behavior.
        for key,value in result.items():
            if key!='context' and isinstance(value,(dict,list)) and len(json.dumps(value))<=500:
                candidates[key]=value
        preferred=('summary','solver','safe_capacity','impact','data_type','live_government_inventory',
            'scenario_id','run_id','total_deficit','deficit_by_resource','targets','transfers')
        def priority(path):
            root=path.split('.')[0]
            if tool=='get_model_performance':
                champion=payload.get('targets',{}).get('medicine',{}).get('champion')
                if path in ('data_type','targets.medicine.champion',f'targets.medicine.models.{champion}.test.wape'):
                    return (-1,path)
            return (preferred.index(root) if root in preferred else len(preferred),path)
        public=[]
        for index,path in enumerate(sorted(candidates,key=priority)[:MAX_FACTS],1):
            try:value=resolve(payload,path)
            except (KeyError,IndexError,TypeError,ValueError):
                # Some metric dictionaries have literal dotted keys (e.g. 0.8).
                # Do not publish an unresolvable path or invent an alias/escape.
                continue
            if len(json.dumps(value))>1500:continue
            fid=f'{eid}_{self.scope}_f{index:03d}'
            fact=Fact(fid,eid,path,deepcopy(value),field_unit(tool,path,payload),tool,deepcopy(payload.get('context',{})))
            self.facts[fid]=fact
            entry={'fact_id':fid,'label':fact_label(path),'value':deepcopy(value),'unit':fact.unit}
            if isinstance(value,(int,float)) and not isinstance(value,bool):entry['quote']=str(value)
            public.append(entry)
        envelope={'evidence_id':eid,'tool':tool,'context':deepcopy(payload.get('context',{})),
            'facts':public,'facts_truncated':len(public)<len(candidates),
            'provenance':{k:v for k,v in {'origin':payload.get('context',{}).get('origin'),
                'model_version':payload.get('model_version')}.items() if v is not None}}
        # Native discovery/planning still receives compact operational objects and handles.
        # Read-only resilience synthesis needs only the fact catalogue and context.
        if not summary_only:envelope['result']=deepcopy(result)
        self.envelopes[eid]=envelope
        return deepcopy(envelope)

    def schema(self):
        schema=json_schema(FactDraftAnswer)
        def restrict(node):
            if isinstance(node,dict):
                if 'evidence_refs' in node.get('properties',{}):
                    node['properties']['evidence_refs']['items']={'type':'string','enum':list(self.facts)}
                for value in node.values():restrict(value)
            elif isinstance(node,list):
                for value in node:restrict(value)
        restrict(schema)
        return schema

    def resolve_draft(self,draft,records):
        data=draft.model_dump();audits=[]
        claims=[('situation',data['situation'])]+[(f'{key}.{i}',claim)
            for key in ('key_risks','recommended_actions','remaining_gaps')
            for i,claim in enumerate(data[key])]
        for index,(field,claim) in enumerate(claims):
            ids=claim.pop('evidence_refs');unknown=[fid for fid in ids if fid not in self.facts]
            facts=[self.facts[fid] for fid in ids if fid in self.facts]
            diagnostic={'claim_index':index,'claim_field':field+'.text','claim_text':claim['text'],
                'supplied_fact_ids':list(self.facts),'cited_fact_ids':ids,'unknown_fact_ids':unknown,
                'resolved_facts':[{'fact_id':f.fact_id,'evidence_id':f.evidence_id,'path':f.path,
                    'value':f.value,'unit':f.unit,'tool':f.tool,'context':f.context} for f in facts]}
            reason='unknown_fact_id' if unknown else 'duplicate_fact_id' if len(set(ids))!=len(ids) else None
            if not reason:
                for fact in facts:
                    record=records.get(fact.evidence_id,{})
                    try:
                        if record.get('tool')!=fact.tool or resolve(record['payload'],fact.path)!=fact.value or record['payload'].get('context',{})!=fact.context:
                            reason='fact_source_changed';break
                    except (KeyError,IndexError,TypeError,ValueError):reason='fact_source_changed';break
            if reason:
                error=CopilotError('evidence_invalid','Gemini returned an unsupported fact citation or interpretation. Retry with a narrower question.')
                error.citation_diagnostic=sanitize_diagnostic({**diagnostic,'reason':reason})
                raise error
            claim['references']=[{'evidence_id':f.evidence_id,'field':f.path} for f in facts]
            audits.append(diagnostic)
        return DraftAnswer.model_validate(data),audits

    def validate(self,draft,records,context=None,origin=None):
        resolved,audits=self.resolve_draft(draft,records)
        try:evidence=build_evidence(resolved,records,context=context,origin=origin)
        except CopilotError as error:
            numeric=getattr(error,'grounding_diagnostic',{})
            relevant=next((a for a in audits if a['claim_field']==numeric.get('claim_field')),audits[0])
            error.citation_diagnostic=sanitize_diagnostic({**relevant,'reason':error.code})
            raise
        for audit in audits:
            reason=semantic_error(audit['claim_text'],[self.facts[fid] for fid in audit['cited_fact_ids']])
            if reason:
                error=CopilotError('evidence_invalid','Gemini returned an unsupported fact interpretation. Retry with a narrower question.')
                error.citation_diagnostic=sanitize_diagnostic({**audit,'reason':reason})
                raise error
        units={(fact.evidence_id,fact.path):fact.unit for fact in self.facts.values()}
        for item in evidence:
            item.unit=units[(item.evidence_id,item.field)] or item.unit
        return resolved,evidence,audits


def semantic_error(text,facts):
    """Conservative topic checks, not a claim of exhaustive natural-language verification."""
    paths=' '.join(path for fact in facts for path,_ in leaves(fact.value,fact.path)).lower()
    lower=text.lower()
    if 'wape' in paths and re.search(r'\baccuracy\b',lower) and not re.search(r'\b(not|no|never|cannot)\b.{0,45}\baccuracy\b',lower):
        return 'wape_is_not_accuracy'
    topics=[(r'\bbeds?\b|\bbed utili[sz]ation\b',r'bed'),
        (r'\bmedicin\w*\b|\binventor\w*\b|\bstock\w*\b',r'medicine|inventory|stock|resource|transfer|safe_capacity|target_deficit|data_type|probab|risk'),
        (r'\bstaff\b|\bpersonnel\b|\bnurses?\b|\bdoctors?\b',r'staff|personnel|nurse|doctor'),
        (r'\bwarning\w*\b|\balerts?\b',r'warning|counts|severity|status|summary.total'),
        (r'\bdonors?\b|\btransfer\w*\b|\bredistribut\w*\b',r'donor|transfer|safe_capacity|deficit|solver|impact')]
    for phrase,relevant in topics:
        if re.search(phrase,lower) and not re.search(relevant,paths):return 'unrelated_fact'
    return None
