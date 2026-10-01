import { TestBed } from '@angular/core/testing';
import { signal, WritableSignal } from '@angular/core';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { WarningsPage } from './warnings';
import { RedistributionPage } from './redistribution';
import { GeospatialPage } from './geospatial';
import { mapView } from '../shared/map-canvas.spec';
import { WarningList } from '../core/resilience-models';

describe('Public computation scopes',()=>{
  let api:jasmine.SpyObj<NetworkApi>;
  beforeEach(()=>{
    api=jasmine.createSpyObj('NetworkApi',['warnings','scenarios','planningPreview','geospatial','optimize']);
    Object.defineProperty(api,'districtOnly',{value:signal(true)});api.scenarios.and.returnValue(of([]));api.geospatial.and.returnValue(of(mapView()));
    TestBed.configureTestingModule({providers:[provideRouter([]),{provide:ActivatedRoute,useValue:{queryParamMap:of(convertToParamMap({country_id:'IN',mode:'forecast'})),snapshot:{queryParamMap:convertToParamMap({})}}},{provide:NetworkApi,useValue:api}]});
  });
  it('national warnings do not request forecasts',()=>{
    const page=TestBed.runInInjectionContext(()=>new WarningsPage());
    expect(page.districtRequired()).toBeTrue();expect(page.loading()).toBeFalse();expect(api.warnings).not.toHaveBeenCalled();
  });
  it('national planning never starts an automatic preview or solve',()=>{
    const page=TestBed.runInInjectionContext(()=>new RedistributionPage());page.optimize();
    expect(page.districtRequired()).toBeTrue();expect(api.planningPreview).not.toHaveBeenCalled();expect(api.optimize).not.toHaveBeenCalled();
    expect(api.scenarios).not.toHaveBeenCalled();expect(page.loading()).toBeFalse();
  });
  it('national forecast map requests only lightweight network and blocks optimization',()=>{
    const page=TestBed.runInInjectionContext(()=>new GeospatialPage());page.optimize();
    expect(page.districtRequired()).toBeTrue();expect(api.geospatial.calls.mostRecent().args[0]['mode']).toBe('network');expect(api.optimize).not.toHaveBeenCalled();
  });
  it('unrestricted local mode resumes warnings after capabilities arrive',()=>{
    const warnings:WarningList={items:[],summary:{total:0,counts:{},facilities_affected:0,medicines_at_risk:0,bed_warnings:0,staff_warnings:0,by_country:{},by_region:{},by_district:{},by_facility:{}}};
    api.warnings.and.returnValue(of(warnings));
    const page=TestBed.runInInjectionContext(()=>new WarningsPage());
    (api.districtOnly as WritableSignal<boolean>).set(false);TestBed.flushEffects();
    expect(page.districtRequired()).toBeFalse();expect(api.warnings).toHaveBeenCalledTimes(1);
    expect(page.loading()).toBeFalse();
  });
  it('unrestricted local mode resumes the actual forecast map',()=>{
    const page=TestBed.runInInjectionContext(()=>new GeospatialPage());
    (api.districtOnly as WritableSignal<boolean>).set(false);TestBed.flushEffects();
    expect(page.districtRequired()).toBeFalse();expect(api.geospatial.calls.mostRecent().args[0]['mode']).toBe('forecast');
  });
});
