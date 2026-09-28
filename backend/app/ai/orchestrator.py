"""Bounded native Interactions loop and auditable request-local evidence."""
import json
from collections import OrderedDict, deque
from datetime import datetime, timezone
from time import perf_counter, monotonic
from threading import RLock, BoundedSemaphore
from uuid import uuid4
from pydantic import ValidationError
from app.ai.config import AIConfig, VERSION as CONFIG_VERSION
from app.ai.client import GeminiTransport, CopilotError
from app.ai.schemas import Context, CopilotResponse, DraftAnswer, ToolTrace
from app.ai.system_prompt import SYSTEM, VERSION as PROMPT_VERSION, LIMITATIONS
from app.ai.tool_registry import declarations, json_schema
from app.ai.tools import ToolExecutor
from app.ai.citations import build_evidence
from app.ai.fallback import clinical_request, offline_calls, offline_draft


def context_key(request):
    return (request.country_id,request.profile,request.state_id,request.district_id,request.facility_id,request.mode)


class CopilotService:
    def __init__(self, engine, planner, config=None, transport_factory=GeminiTransport):
        self.engine, self.planner = engine, planner
        self.config = config or AIConfig()
        self.transport_factory = transport_factory
        self.lock, self.capacity = RLock(), BoundedSemaphore(2)
        self.conversations, self.requests = OrderedDict(), OrderedDict()
        self.audit = deque(maxlen=100)
        self.runtime_status = 'not_attempted'

    def status(self):
        error = self.config.error()
        return {'model':self.config.model,'sdk':'google-genai','sdk_version':'2.25.0','api':'Interactions',
            'enabled':self.config.enabled,'configured':bool(self.config.api_key),
            'configuration_status':error[0] if error else 'configured',
            'runtime_status':self.runtime_status,'thinking_level':self.config.thinking,
            'offline_available':True,'offline_label':'OFFLINE — deterministic local summaries',
            'system_prompt_version':PROMPT_VERSION,'config_version':CONFIG_VERSION,
            'setup':error[1] if error else 'Configured; availability is confirmed only by a successful runtime request.'}

    def progress(self, rid, country, profile):
        with self.lock:
            row = self.requests.get(rid)
            if not row or row['country_id']!=country or row['profile']!=profile:
                raise LookupError('Copilot request not found in selected country/profile')
            return json.loads(json.dumps(row))

    def discard(self, cid, country, profile):
        with self.lock:
            row = self.conversations.get(cid)
            if not row or row['key'][:2] != (country,profile):
                raise LookupError('Conversation not found in selected country/profile')
            if row['busy']:
                raise CopilotError('conversation_busy','Wait for the active conversation request to finish.',409)
            del self.conversations[cid]
            for rid in [k for k,v in self.requests.items() if v.get('conversation_id')==cid]:
                del self.requests[rid]
            self.audit = deque((x for x in self.audit if x.get('conversation_id')!=cid),maxlen=100)
            # Provider interaction history may remain according to Google's retention policy.

    def run(self, repository, original):
        request = original.model_copy(deep=True)
        rid = str(request.request_id or uuid4())
        start = perf_counter()
        if self.config.api_key and self.config.api_key in request.message:
            raise CopilotError('credential_input','Remove credentials from the operational question.',422)
        if clinical_request(request.message):
            return CopilotResponse(request_id=rid,mode='refusal',status='refused',context=Context.model_validate(request.model_dump(include=set(Context.model_fields))),
                answer='HealthNexus Copilot supports health-system resource planning, not individual diagnosis, prescribing, treatment or private patient-record interpretation.',limitations=LIMITATIONS,
                metadata={'system_prompt_version':PROMPT_VERSION,'clinical_input_sent_to_provider':False})
        if not request.message.strip():
            raise CopilotError('empty_message','Enter an operational question.',422)
        if not self.capacity.acquire(blocking=False):
            raise CopilotError('busy','Two Copilot workflows are active. Retry shortly.',429)
        cid, row, transport, owned = None, None, None, False
        timing={'gemini_network_seconds':0.,'tool_seconds':0.}
        usages=[];interaction_count=0;provider_requests=0;interaction_ids=[]
        try:
            executor = ToolExecutor(repository,self.engine,self.planner,request)
            snapshot = executor.snapshot(request.profile)
            from app.scenarios.engine import select
            select(snapshot,request.state_id,request.district_id,[request.facility_id] if request.facility_id else None)
            if request.scenario_id: executor.scenario(snapshot,request.scenario_id)
            with self.lock:
                now=monotonic()
                for old in [k for k,v in self.conversations.items() if not v['busy'] and now-v['updated']>1800]:
                    del self.conversations[old]
                cid = str(request.conversation_id or uuid4())
                row = self.conversations.get(cid)
                if request.conversation_id and not row:
                    raise CopilotError('conversation_missing','Conversation expired or was reset. Start a new conversation.',404)
                if row and (row['key']!=context_key(request) or row['origin']!=str(snapshot.as_of)):
                    raise CopilotError('conversation_context','Conversation context changed. Start a new conversation.',409)
                if row and row['busy']:
                    raise CopilotError('conversation_busy','Wait for this conversation request to finish.',409)
                if not row:
                    if len(self.conversations)>=20:
                        idle=next((k for k,v in self.conversations.items() if not v['busy']),None)
                        if idle is None: raise CopilotError('busy','Conversation capacity reached.',429)
                        del self.conversations[idle]
                    row={'key':context_key(request),'origin':str(snapshot.as_of),'previous':None,
                         'scenario_id':None,'run_id':None,'updated':now,'busy':False}
                    self.conversations[cid]=row
                if rid in self.requests:
                    raise CopilotError('request_exists','Request ID already exists. Submit a new request ID.',409)
                while len(self.requests)>=100:
                    old=next((k for k,v in self.requests.items() if v['status']!='running'),None)
                    if old is None: raise CopilotError('busy','Request capacity reached.',429)
                    del self.requests[old]
                row['busy']=True
                owned=True
                request.scenario_id=request.scenario_id or row['scenario_id']
                request.optimization_run_id=request.optimization_run_id or row['run_id']
                executor.latest_scenario=request.scenario_id;executor.latest_plan=request.optimization_run_id
                self.requests[rid]={'request_id':rid,'conversation_id':cid,'country_id':request.country_id,
                    'profile':request.profile,'status':'running','phase':'Checking context','tools':[]}
            traces, records = [], {}
            def execute(name,args):
                if len(traces)>=self.config.max_calls:
                    raise CopilotError('tool_limit','Copilot tool-call limit reached. Narrow the question.',422)
                if perf_counter()-start>self.config.workflow_timeout:
                    raise CopilotError('workflow_timeout','Copilot workflow time limit reached. Narrow the question.',504)
                trace=ToolTrace(tool=name,status='running')
                traces.append(trace)
                with self.lock:
                    self.requests[rid].update(phase=name,tools=[t.model_dump() for t in traces])
                began=perf_counter()
                try:
                    payload=executor.execute(name,args)
                    eid=f'e{len(records)+1}'
                    records[eid]={'tool':name,'payload':payload}
                    trace.status='success';trace.evidence_id=eid
                    trace.summary='Validated HealthNexus result; no external action executed.'
                    output={'evidence_id':eid,'result':payload}
                except (ValueError,LookupError,ValidationError):
                    trace.status='error';trace.summary='Invalid arguments, stale artifacts or incompatible scope. Check selected context.'
                    output={'error':trace.summary}
                except Exception:
                    trace.status='error';trace.summary='HealthNexus tool unavailable; check trusted artifacts and service configuration.'
                    output={'error':trace.summary}
                trace.seconds=perf_counter()-began;timing['tool_seconds']+=trace.seconds
                with self.lock:
                    self.requests[rid]['tools']=[t.model_dump() for t in traces]
                return output
            interaction_id=None
            if request.mode=='offline':
                for name,args in offline_calls(request):
                    output=execute(name,args)
                    if name=='run_emergency_scenario' and 'result' in output:
                        execute('get_scenario_comparison',{'country_id':request.country_id,'profile':request.profile,
                            'state_id':request.state_id,'district_id':request.district_id,'scenario_id':executor.latest_scenario})
                if not records:
                    raise CopilotError('tools_unavailable','Local tools could not provide results for this context.')
                draft=offline_draft(records)
            else:
                error=self.config.error()
                if error: raise CopilotError(*error)
                transport=self.transport_factory(self.config)
                previous=row['previous']
                input_data=json.dumps({'question':request.message,'context':request.model_dump(exclude={'message','request_id','conversation_id'}),
                    'active_scenario_id':executor.latest_scenario,'active_optimization_id':executor.latest_plan})
                for turn in range(self.config.max_calls+1):
                    if perf_counter()-start>self.config.workflow_timeout:
                        raise CopilotError('workflow_timeout','Copilot workflow time limit reached.',504)
                    with self.lock: self.requests[rid]['phase']='Gemini selecting tools / preparing explanation'
                    body={'model':self.config.model,'input':input_data,'system_instruction':SYSTEM,
                        'tools':declarations(),'store':True,
                        'generation_config':{'thinking_level':self.config.thinking,'max_output_tokens':self.config.max_output_tokens}}
                    if previous: body['previous_interaction_id']=previous
                    began=perf_counter()
                    provider_requests+=1
                    try: response=transport.create(**body)
                    finally: timing['gemini_network_seconds']+=perf_counter()-began
                    interaction_count+=1
                    self.runtime_status='runtime_successful'
                    previous=interaction_id=response.get('id')
                    if not previous:
                        raise CopilotError('response_invalid','Gemini returned no interaction identity.')
                    interaction_ids.append(previous)
                    if response.get('usage'): usages.append(response['usage'])
                    calls=[s for s in response.get('steps',[]) if s.get('type')=='function_call']
                    if not calls:
                        if response.get('status')=='incomplete':
                            raise CopilotError('response_incomplete','Gemini reached its response budget before finishing tool gathering.')
                        break
                    input_data=[]
                    for call in calls:
                        if not isinstance(call.get('arguments'),dict) or not call.get('id') or not isinstance(call.get('name'),str):
                            raise CopilotError('malformed_tool_call','Gemini returned a malformed function call.')
                        output=execute(call['name'],call['arguments'])
                        input_data.append({'type':'function_result','name':call['name'],'call_id':call['id'],
                            'result':[{'type':'text','text':json.dumps(output,ensure_ascii=False)}]})
                else:
                    raise CopilotError('tool_limit','Copilot tool-call limit reached.',422)
                if not records:
                    raise CopilotError('tools_unavailable','Gemini did not retrieve fresh HealthNexus evidence.')
                if perf_counter()-start>self.config.workflow_timeout:
                    raise CopilotError('workflow_timeout','Copilot workflow time limit reached.',504)
                # This live endpoint rejects custom tools together with response_format.
                # Preserve native state, but request the schema in a separate tool-free turn.
                with self.lock: self.requests[rid]['phase']='Gemini synthesizing verified evidence'
                body={'model':self.config.model,'previous_interaction_id':previous,
                    'input':json.dumps({'instruction':'Now produce the structured administrator answer using only fresh evidence from this request. Preserve remaining shortages and advisory-only status. Cite exact returned fields, not entire large objects.',
                        'fresh_evidence':[{ 'evidence_id':eid,'tool':r['tool']} for eid,r in records.items()]}),
                    'system_instruction':SYSTEM,'store':True,
                    'generation_config':{'thinking_level':self.config.thinking,'max_output_tokens':self.config.max_output_tokens},
                    'response_format':{'type':'text','mime_type':'application/json','schema':json_schema(DraftAnswer)}}
                began=perf_counter();provider_requests+=1
                try: response=transport.create(**body)
                finally: timing['gemini_network_seconds']+=perf_counter()-began
                interaction_count+=1
                interaction_id=response.get('id')
                if not interaction_id or response.get('status')=='incomplete':
                    raise CopilotError('response_incomplete','Gemini did not finish structured synthesis within its response budget.')
                interaction_ids.append(interaction_id)
                if response.get('usage'):usages.append(response['usage'])
                try: draft=DraftAnswer.model_validate_json(response.get('output_text',''))
                except (ValidationError,TypeError):
                    raise CopilotError('response_schema','Gemini response failed the structured output schema.') from None
            evidence=build_evidence(draft,records)
            results=[{'evidence_id':eid,'tool':r['tool'],'result':r['payload']} for eid,r in records.items()]
            response=CopilotResponse(request_id=rid,conversation_id=cid,mode=request.mode,answer=draft.situation.text,
                **draft.model_dump(),context=Context.model_validate(request.model_dump(include=set(Context.model_fields))),
                evidence=evidence,tools_used=traces,limitations=LIMITATIONS,
                scenario_id=executor.latest_scenario,optimization_run_id=executor.latest_plan,
                operational_results=results,metadata={**timing,'total_seconds':perf_counter()-start,'tool_calls':len(traces),'interaction_count':interaction_count,
                    'provider_requests':provider_requests,'interaction_ids':interaction_ids,
                    'model':self.config.model if request.mode=='gemini' else None,'configured_model':self.config.model,
                    'sdk_version':'2.25.0','api':'Interactions',
                    'transport':'offline' if request.mode=='offline' else 'google-genai' if self.transport_factory is GeminiTransport else 'mock',
                    'thinking_level':self.config.thinking if request.mode=='gemini' else None,
                    'interaction_id':interaction_id,'timestamp':datetime.now(timezone.utc).isoformat(),
                    'system_prompt_version':PROMPT_VERSION,'config_version':CONFIG_VERSION,'usage':usages,
                    'model_versions':sorted({r['payload'].get('model_version') or r['payload'].get('provenance',{}).get('model_version')
                        for r in records.values()}-{None} | {v for r in records.values() for v in r['payload'].get('model_versions',[])})})
            with self.lock:
                row.update(previous=interaction_id,scenario_id=executor.latest_scenario,run_id=executor.latest_plan,updated=monotonic())
                self.requests[rid].update(status='completed',phase='Completed')
                self.audit.append({'request_id':rid,'conversation_id':cid,'question':request.message,
                    'country_id':request.country_id,'profile':request.profile,'state_id':request.state_id,'district_id':request.district_id,
                    'timestamp':response.metadata['timestamp'],'system_prompt_version':PROMPT_VERSION,'config_version':CONFIG_VERSION,
                    'mode':request.mode,'model':response.metadata['model'],'status':'completed',
                    'tools':[t.model_dump() for t in traces],'latency':response.metadata['total_seconds'],'usage':usages})
            return response
        except CopilotError as error:
            if request.mode=='gemini':
                self.runtime_status=error.code
            with self.lock:
                if owned and rid in self.requests:
                    self.requests[rid].update(status='error',phase=error.message,error_code=error.code)
                    self.audit.append({'request_id':rid,'conversation_id':cid,'mode':request.mode,'status':error.code,
                        'country_id':request.country_id,'profile':request.profile,
                        'model':self.config.model if request.mode=='gemini' else None,
                        'latency':perf_counter()-start,'tools':self.requests[rid]['tools'],
                        'provider_diagnostic':getattr(error,'diagnostic',{}),'timings':timing,
                        'interaction_count':interaction_count,'provider_requests':provider_requests,
                        'interaction_ids':interaction_ids,'usage':usages})
            raise
        except Exception:
            with self.lock:
                if owned and rid in self.requests:
                    self.requests[rid].update(status='error',phase='Copilot unavailable',error_code='copilot_unavailable')
            if request.mode=='gemini': self.runtime_status='runtime_failure'
            raise CopilotError('copilot_unavailable','Copilot unavailable. Check trusted artifacts and server configuration.') from None
        finally:
            if row and owned:
                with self.lock: row['busy']=False
            if transport: transport.close()
            self.capacity.release()
