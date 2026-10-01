import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { DecimalPipe, PercentPipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, combineLatest, of, Subscription, switchMap, tap } from 'rxjs';
import { computationPolicy } from '../core/computation-policy';
import { NetworkApi } from '../core/network-api';
import { MapCanvas } from '../shared/map-canvas';
import { FacilityFeature, GeospatialView, LaneFeature, MapMode } from '../core/geospatial-models';
import { PlanningRequest } from '../core/optimization-models';
import { ComputationNotice } from '../shared/computation-notice';
import { operationalError } from '../core/operational-error';

@Component({selector:'app-geospatial',imports:[MapCanvas,RouterLink,DecimalPipe,PercentPipe,ComputationNotice],
  templateUrl:'./geospatial.html',styleUrl:'./geospatial.scss'})
export class GeospatialPage {
  private api=inject(NetworkApi);private route=inject(ActivatedRoute);private router=inject(Router);private destroy=inject(DestroyRef);
  private task?:Subscription;
  modes:MapMode[]=['network','forecast','emergency','redistribution'];
  country='IN';profile='constrained';state='';district='';scenario='';run='';
  mode=signal<MapMode>('network');donorScope:PlanningRequest['scope']='district';
  status='';type='';resource='';
  districtOnly = this.api.districtOnly;
  districtRequired(){return this.districtOnly() && this.mode()==='forecast' && !this.district;}
  planningDisabled(){return this.districtOnly() && (!this.district || !['district','cross_district'].includes(this.donorScope));}
  view=signal<GeospatialView|null>(null);error=signal('');loading=signal(false);busy=signal(false);
  selected=signal('');selectedLane=signal('');
  facility=computed<FacilityFeature|undefined>(()=>this.view()?.facilities.features.find(f=>f.id===this.selected()));
  lane=computed<LaneFeature|undefined>(()=>this.view()?.transfers.features.find(f=>f.id===this.selectedLane()));
  constructor(){
    this.destroy.onDestroy(()=>this.task?.unsubscribe());
    combineLatest([this.route.queryParamMap,computationPolicy(this.api)]).pipe(tap(([p])=>{
      this.task?.unsubscribe();this.busy.set(false);this.view.set(null);this.error.set('');this.loading.set(true);
      this.selected.set(p.get('facility_id')||'');this.selectedLane.set('');this.country=p.get('country_id')||'IN';this.profile=p.get('profile')||'constrained';
      this.state=p.get('state_id')||'';this.district=p.get('district_id')||'';this.scenario=p.get('scenario_id')||'';this.run=p.get('run_id')||'';
      this.mode.set(this.modes.includes(p.get('mode') as MapMode)?p.get('mode') as MapMode:'network');
      const scope=p.get('donor_scope');this.donorScope=['district','cross_district','state','national'].includes(scope||'')?scope as PlanningRequest['scope']:this.district?'district':'national';
      this.status=p.get('status')||'';this.type=p.get('facility_type')||'';
      // Resource is a medicine lane filter; inherited overview demand filters
      // (footfall/admissions) do not apply to advisory map lanes.
      const resource=p.get('resource')||'';this.resource=['PCM','IVF','ORS','AMX','IFA'].includes(resource)?resource:'';
    }),switchMap(()=>this.api.geospatial(this.context()).pipe(catchError(e=>{
      this.error.set(operationalError(e,'Unable to load this geographic context. Return to its original profile and scope.'));return of(null);
    }))),takeUntilDestroyed(this.destroy)).subscribe(v=>{this.loading.set(false);this.view.set(v);});
  }
  missingHandle(){return this.mode()==='emergency'&&!this.scenario||this.mode()==='redistribution'&&!this.run;}
  context():Record<string,string>{return {country_id:this.country,state_id:this.state,district_id:this.district,
    mode:this.missingHandle()||this.districtRequired()?'network':this.mode(),scenario_id:this.scenario,run_id:this.run,donor_scope:this.donorScope,
    resource:this.resource,status:this.status,facility_type:this.type};}
  change(values:Record<string,string|null>){this.router.navigate([], {relativeTo:this.route,queryParams:values,queryParamsHandling:'merge'});}
  switchMode(mode:MapMode){this.change({mode});}
  scope(value:string){this.change({donor_scope:value,run_id:null});}
  filter(key:string,event:Event){this.change({[key]:(event.target as HTMLSelectElement).value||null});}
  geography(key:string,event:Event){const value=(event.target as HTMLSelectElement).value;
    this.change({[key]:value||null,...(key==='state_id'?{district_id:null}:{}),scenario_id:null,run_id:null,
      donor_scope:null,status:null,facility_type:null,resource:null});}
  districts(){return this.view()?.geography.districts.filter(d=>d.state_id===this.state)||[];}
  loadDemo(profile='redistribution-ready'){
    this.router.navigate(['/geospatial'],{queryParams:{country_id:'IN',profile,state_id:'MH',district_id:'MH-PUNE',mode:'network',donor_scope:'cross_district'}});
  }
  body():PlanningRequest{return {country_id:this.country,profile:this.profile,...(this.state?{state_id:this.state}:{}),
    ...(this.district?{district_id:this.district}:{}),...(this.scenario?{scenario_id:this.scenario}:{}),
    scope:this.donorScope,resources:['PCM','IVF','ORS','AMX','IFA'],horizon:14,time_limit_seconds:10};}
  simulate(){
    if(this.busy()||!this.state||!this.district)return;this.busy.set(true);this.error.set('');
    this.task=this.api.runScenario({country_id:this.country,state_id:this.state,district_id:this.district,
      scenario_type:'DENGUE_SURGE',severity:'severe',duration:14,seed:42,facility_ids:[],parameters:{}}).subscribe({
      next:r=>{this.busy.set(false);this.change({scenario_id:r.scenario.scenario_id,run_id:null,mode:'emergency'});},
      error:e=>{this.busy.set(false);this.error.set(operationalError(e,'Scenario could not be calculated.'));}});
  }
  optimize(){
    if(this.busy()||this.planningDisabled())return;this.busy.set(true);this.error.set('');
    this.task=this.api.optimize(this.body()).subscribe({next:r=>{
      this.busy.set(false);this.change({run_id:r.run_id,scenario_id:r.preview.request.scenario_id||null,
        donor_scope:r.preview.request.scope,mode:'redistribution',status:null,facility_type:null,resource:null});
    },error:e=>{this.busy.set(false);this.error.set(operationalError(e,'No plan was produced.'));}});
  }
  facilityLinks(id:string){const f=this.view()?.facilities.features.find(f=>f.id===id)?.properties;
    const selectedMode=(this.mode()==='emergency'||this.mode()==='redistribution')&&f?.scenario_affected?this.mode():this.mode()==='forecast'?'forecast':'network';
    const receiverContext=f?.district_id===this.district && f?.state_id===this.state;
    return {country_id:this.country,profile:this.profile,state_id:f?.state_id,district_id:f?.district_id,
      facility_id:id,mode:selectedMode,scenario_id:selectedMode==='emergency'||selectedMode==='redistribution'?this.scenario||null:null,
      run_id:selectedMode==='redistribution'&&receiverContext?this.run||null:null,
      donor_scope:selectedMode==='redistribution'&&receiverContext?this.donorScope:null};}
  pickFacility(id:string){this.selected.set(id);this.selectedLane.set('');}
  pickLane(id:string){this.selectedLane.set(id);this.selected.set('');}
}
