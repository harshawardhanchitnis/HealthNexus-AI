import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';
import { GeospatialPage } from './geospatial';
import { NetworkApi } from '../core/network-api';
import { mapView } from '../shared/map-canvas.spec';

describe('Geospatial context and authoritative workflows',()=>{
  let params:BehaviorSubject<ReturnType<typeof convertToParamMap>>;let api:jasmine.SpyObj<NetworkApi>;let page:GeospatialPage;let router:Router;
  const base={country_id:'IN',profile:'redistribution-ready',state_id:'MH',district_id:'MH-PUNE',donor_scope:'cross_district'};
  beforeEach(()=>{
    params=new BehaviorSubject(convertToParamMap(base));api=jasmine.createSpyObj('NetworkApi',['geospatial','optimize','runScenario']);
    api.geospatial.and.returnValue(of(mapView()));
    TestBed.configureTestingModule({providers:[provideRouter([]),{provide:ActivatedRoute,useValue:{queryParamMap:params}},{provide:NetworkApi,useValue:api}]});
    router=TestBed.inject(Router);spyOn(router,'navigate').and.resolveTo(true);
    page=TestBed.runInInjectionContext(()=>new GeospatialPage());
  });
  it('preserves donor scope/profile/geography in every planning request',()=>{
    expect(page.body().scope).toBe('cross_district');expect(page.body().profile).toBe('redistribution-ready');expect(page.body().district_id).toBe('MH-PUNE');
    expect(api.geospatial.calls.mostRecent().args[0]['country_id']).toBe('IN');
  });
  it('shows network with explicit notice until required scenario or plan exists',()=>{
    for(const mode of ['emergency','redistribution']){params.next(convertToParamMap({...base,mode}));expect(page.missingHandle()).toBeTrue();expect(page.context()['mode']).toBe('network');}
  });
  it('passes actual scenario/run handles to redistribution, not cached invented lanes',()=>{
    params.next(convertToParamMap({...base,mode:'redistribution',scenario_id:'actual-scenario',run_id:'actual-plan'}));
    expect(page.context()['run_id']).toBe('actual-plan');expect(page.context()['scenario_id']).toBe('actual-scenario');expect(page.missingHandle()).toBeFalse();
  });
  it('rejects stale context cleanly and clears selections',()=>{
    page.pickFacility('receiver');api.geospatial.and.returnValue(throwError(()=>({error:{detail:'Profile mismatch'}})));
    params.next(convertToParamMap({...base,profile:'constrained',run_id:'stale'}));
    expect(page.view()).toBeNull();expect(page.selected()).toBe('');expect(page.error()).toBe('Profile mismatch');expect(page.loading()).toBeFalse();
  });
  it('geography changes invalidate scenario, plan, filters and donor scope',()=>{
    page.geography('state_id',{target:{value:'KA'}} as unknown as Event);
    expect(router.navigate).toHaveBeenCalledWith([],{relativeTo:jasmine.anything(),queryParams:{state_id:'KA',district_id:null,scenario_id:null,run_id:null,donor_scope:null,status:null,facility_type:null,resource:null},queryParamsHandling:'merge'});
  });
  it('scope changes invalidate only the plan while retaining scenario through merged navigation',()=>{
    page.scope('district');expect(router.navigate).toHaveBeenCalledWith([],{relativeTo:jasmine.anything(),queryParams:{donor_scope:'district',run_id:null},queryParamsHandling:'merge'});
  });
  it('synchronizes accessible selection with inspector and excludes unsupported donor scenario context',()=>{
    page.pickFacility('receiver');expect(page.facility()?.properties.name).toBe('Illustrative receiver');
    page.scenario='scenario';page.mode.set('emergency');expect(page.facilityLinks('receiver').scenario_id).toBe('scenario');
    page.mode.set('forecast');expect(page.facilityLinks('receiver').scenario_id).toBeNull();page.mode.set('network');
    page.view()!.facilities.features[0].properties.scenario_affected=false;expect(page.facilityLinks('receiver').scenario_id).toBeNull();
    page.pickLane('lane');expect(page.selected()).toBe('');
  });
  it('demo selection changes operational context without supplying an optimizer result',()=>{
    page.loadDemo();expect(router.navigate).toHaveBeenCalledWith(['/geospatial'],{queryParams:{...base,mode:'network'}});expect(api.optimize).not.toHaveBeenCalled();
  });
});
