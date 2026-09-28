import { Component, inject, signal, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe, JsonPipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription, interval } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { CopilotContext, CopilotMode, CopilotPlan, CopilotResponse, CopilotStatus, CopilotTrace } from '../core/copilot-models';

@Component({selector:'app-copilot', imports:[FormsModule, DecimalPipe, JsonPipe, RouterLink],
  templateUrl:'./copilot.html', styleUrl:'./copilot.scss'})
export class CopilotPage implements OnDestroy {
  private api=inject(NetworkApi); private route=inject(ActivatedRoute); private router=inject(Router);
  status=signal<CopilotStatus | null>(null); busy=signal(false); phase=signal(''); trace=signal<CopilotTrace[]>([]);
  error=signal(''); replies=signal<{question:string;response:CopilotResponse}[]>([]);
  context=signal<CopilotContext>({country_id:'IN',profile:'constrained'});
  message=''; mode:CopilotMode='offline'; allowPlanning=false; compareProfiles=false;
  private conversation?:string; private signature=''; private active?:Subscription; private polling?:Subscription;
  private progress?:Subscription; private parameters:Subscription;
  modelAttempts=signal<{model:string;status:string;http_status?:number;seconds:number}[]>([]);
  constructor() {
    this.refreshStatus();
    this.parameters=this.route.queryParamMap.subscribe(p=>{
      const context:CopilotContext={country_id:p.get('country_id')||'IN',profile:p.get('profile')||'constrained',
        state_id:p.get('state_id'),district_id:p.get('district_id'),facility_id:p.get('facility_id'),
        scenario_id:p.get('scenario_id'),optimization_run_id:p.get('run_id')};
      const next=JSON.stringify(context);
      if(this.signature && next!==this.signature) this.clearLocal();
      this.signature=next;this.context.set(context);
    });
  }
  refreshStatus() { this.api.copilotStatus().subscribe({next:s=>this.status.set(s),error:()=>this.error.set('Copilot status is unavailable. Check the backend connection.')}); }
  clearLocal() {
    this.active?.unsubscribe();this.stopPolling();this.busy.set(false);this.conversation=undefined;
    this.replies.set([]);this.trace.set([]);this.modelAttempts.set([]);this.error.set('');this.allowPlanning=false;this.compareProfiles=false;
  }
  reset() {
    if(this.conversation) this.api.discardConversation(this.conversation,this.context().country_id).subscribe({error:()=>{}});
    this.clearLocal();
  }
  offline() { this.reset();this.mode='offline'; }
  changeMode() { this.reset(); }
  pune() { this.router.navigate(['/copilot'],{queryParams:{country_id:'IN',state_id:'MH',district_id:'MH-PUNE',profile:this.context().profile}}); }
  suggest(kind:string) {
    this.allowPlanning=kind==='dengue';this.compareProfiles=kind==='compare';
    this.message=kind==='dengue'?'Simulate a severe 14-day dengue surge in the selected scope, identify resource risks and find the safest redistribution plan.':
      kind==='donors'?'Why did HealthNexus choose these donors?':kind==='provenance'?'Is this live government inventory?':
      kind==='evaluation'?'How reliable is the medicine-demand forecast?':kind==='compare'?'Compare the constrained network with the redistribution-ready stress-test.':'Summarize the most urgent healthcare-resource risks in the selected scope.';
  }
  send() {
    if(this.busy()||!this.message.trim()) return;
    this.busy.set(true);this.error.set('');this.trace.set([]);this.modelAttempts.set([]);this.phase.set('Checking context…');
    const question=this.message.trim(), rid=crypto.randomUUID(), context=this.context();
    const body={...context,message:question,mode:this.mode,allow_planning:this.allowPlanning,compare_profiles:this.compareProfiles,
      request_id:rid,conversation_id:this.conversation};
    this.polling=interval(900).subscribe(()=>{
      this.progress?.unsubscribe();
      this.progress=this.api.copilotProgress(rid,context.country_id).subscribe({next:p=>{this.phase.set(p.phase);this.trace.set(p.tools);this.modelAttempts.set(p.model_attempts||[]);},error:()=>{}});
    });
    this.active=this.api.copilot(body).subscribe({next:response=>{
      this.stopPolling();this.busy.set(false);this.conversation=response.conversation_id||undefined;
      this.context.update(c=>({...c,scenario_id:response.scenario_id,optimization_run_id:response.optimization_run_id}));
      this.replies.update(rows=>[...rows.slice(-9),{question,response}]);this.trace.set(response.tools_used);this.message='';
      this.refreshStatus();
    },error:e=>{
      this.stopPolling();this.busy.set(false);const detail=e.error?.detail;
      this.modelAttempts.set(detail?.metadata?.model_attempts||[]);
      this.error.set(typeof detail==='object'&&detail?.message?detail.message:'Copilot request failed. Check selected context and server configuration.');
      this.refreshStatus();
    }});
  }
  stopPolling() { this.polling?.unsubscribe();this.progress?.unsubscribe(); }
  plan(reply:CopilotResponse):CopilotPlan|null {
    const row=[...reply.operational_results].reverse().find(r=>r.tool==='optimize_redistribution'||r.tool==='get_optimization_result');
    return row?row.result as unknown as CopilotPlan:null;
  }
  links(reply:CopilotResponse) {
    return {country_id:reply.context.country_id,profile:reply.context.profile,state_id:reply.context.state_id,
      district_id:reply.context.district_id,scenario_id:reply.scenario_id,run_id:reply.optimization_run_id};
  }
  label(tool:string) { return tool.replace(/_/g,' '); }
  modelLabel(model?:string|null) { return (model||this.status()?.model||'gemini-3.8-flash').replace('gemini-','Gemini ').replace('-flash-lite',' Flash-Lite').replace('-flash',' Flash'); }
  latestModel() { return this.replies().at(-1)?.response.metadata.effective_model || this.status()?.model; }
  fallbackActive() { return !!this.replies().at(-1)?.response.metadata.fallback_used; }
  ngOnDestroy() { this.active?.unsubscribe();this.stopPolling();this.parameters.unsubscribe(); }
}
