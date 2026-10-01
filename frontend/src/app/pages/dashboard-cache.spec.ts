import { createEnvironmentInjector, EnvironmentInjector, runInInjectionContext } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { Dashboard } from './dashboard';
import { ReadCache } from '../core/read-cache';

describe('Dashboard route recreation with shared cached reads', () => {
  let http: HttpTestingController; let current: EnvironmentInjector | undefined;
  const scope = {country_id:'IN', profile:'constrained'};
  const overview = {as_of:'2026-09-27', country:{id:'IN',name:'India'}, regions:[]};
  function visit(page: string, params = scope) {
    current?.destroy();
    current = createEnvironmentInjector([{provide:ActivatedRoute,useValue:{data:of({page}),queryParamMap:of(convertToParamMap(params))}}],TestBed.inject(EnvironmentInjector));
    return runInInjectionContext(current, () => new Dashboard());
  }
  function flush(url: string, value: object) { http.expectOne(r => r.url === url).flush(value); }
  beforeEach(() => {
    current = undefined;
    TestBed.configureTestingModule({providers:[provideRouter([]),provideHttpClient(),provideHttpClientTesting()]});
    http = TestBed.inject(HttpTestingController);
    spyOnProperty(TestBed.inject(Router),'url','get').and.returnValue('/overview?profile=constrained');
  });
  afterEach(() => { current?.destroy(); http.verify(); });
  it('loads once then removes duplicate overview/facility requests across all five views', () => {
    let page = visit('overview'); expect(page.loading()).toBeTrue();
    flush('/api/overview', overview); flush('/api/facilities',{items:[],total:207}); expect(page.loading()).toBeFalse();
    page = visit('network'); expect(page.loading()).toBeTrue();
    http.expectNone(r => r.url === '/api/overview');
    const facilities = http.expectOne(r => r.url === '/api/facilities'); expect(facilities.request.params.get('limit')).toBe('15'); facilities.flush({items:[],total:207});
    page = visit('facilities'); expect(page.loading()).toBeFalse(); http.expectNone(r => r.url.startsWith('/api/'));
    page = visit('supply'); flush('/api/inventory',{items:[]});
    page = visit('alerts'); flush('/api/alerts',{items:[],total:0});
    for (const path of ['overview','network','facilities','supply','alerts','overview']) {
      page = visit(path); expect(page.loading()).toBeFalse(); expect(page.data()).toEqual(jasmine.objectContaining(overview));
      http.expectNone(r => r.url.startsWith('/api/'));
    }
  });
  it('keeps cached dashboard visible during stale and explicit refresh, including a refresh failure', () => {
    let now = 100_000; spyOn(Date,'now').and.callFake(() => now);
    visit('overview'); flush('/api/overview',overview); flush('/api/facilities',{items:[],total:207});
    now += 60_001; const page = visit('overview'); expect(page.loading()).toBeFalse(); expect(page.data()).not.toBeNull();
    const key = page.cacheKeys()[0]; expect(TestBed.inject(ReadCache).state(key).refreshing).toBeTrue();
    http.expectOne(r => r.url === '/api/overview').flush({detail:'offline'},{status:503,statusText:'Unavailable'});
    flush('/api/facilities',{items:[],total:207}); expect(page.error()).toBe(''); expect(page.data()).not.toBeNull();
    expect(TestBed.inject(ReadCache).state(key).failed).toBeTrue();
    page.refresh(); expect(page.loading()).toBeFalse(); flush('/api/overview',overview); flush('/api/facilities',{items:[],total:207});
    expect(TestBed.inject(ReadCache).state(key).failed).toBeFalse();
  });
  it('never shows old profile or geography while an uncached selection loads', () => {
    visit('overview'); flush('/api/overview',overview); flush('/api/facilities',{items:[],total:207});
    const page = visit('facilities',{...scope,profile:'redistribution-ready',district_id:'MH-NAGPUR'} as typeof scope);
    expect(page.data()).toBeNull(); expect(page.loading()).toBeTrue();
    const first = http.expectOne(r => r.url === '/api/overview'); expect(first.request.params.get('profile')).toBe('redistribution-ready'); expect(first.request.params.get('district_id')).toBe('MH-NAGPUR'); first.flush(overview);
    flush('/api/facilities',{items:[],total:3});
  });
  it('search and pagination fetch their own keys while keeping common overview cached', () => {
    const page = visit('facilities'); flush('/api/overview',overview); flush('/api/facilities',{items:[],total:207});
    page.search = 'hospital'; page.applySearch({preventDefault:() => {}} as Event);
    http.expectNone(r => r.url === '/api/overview');
    const search = http.expectOne(r => r.url === '/api/facilities'); expect(search.request.params.get('search')).toBe('hospital'); search.flush({items:[],total:70});
    page.paginate(1); const pagination = http.expectOne(r => r.url === '/api/facilities'); expect(pagination.request.params.get('offset')).toBe('15'); pagination.flush({items:[],total:70});
    page.paginate(-1); expect(page.loading()).toBeFalse(); http.expectNone(r => r.url.startsWith('/api/'));
  });
});
