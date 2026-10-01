import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { NetworkApi } from './network-api';
import { apiBaseInterceptor } from './api-base';

describe('NetworkApi read isolation and existing admission retry', () => {
  let api: NetworkApi; let http: HttpTestingController; let profile: string;
  beforeEach(() => {
    window.HEALTHNEXUS_CONFIG = {apiBaseUrl:''};
    TestBed.configureTestingModule({providers:[provideRouter([]), provideHttpClient(withInterceptors([apiBaseInterceptor])), provideHttpClientTesting()]});
    api = TestBed.inject(NetworkApi); http = TestBed.inject(HttpTestingController); profile = 'constrained';
    spyOnProperty(TestBed.inject(Router), 'url', 'get').and.callFake(() => '/overview?profile=' + profile);
  });
  afterEach(() => http.verify());
  it('reuses reads but isolates every profile/district/filter/page', () => {
    const base = {country_id:'IN', district_id:'MH-PUNE', limit:15};
    api.facilities(base).subscribe(); http.expectOne(r => r.url === '/api/facilities').flush({items:[],total:6});
    let total = 0; api.facilities(base).subscribe(v => total = v.total);
    expect(total).toBe(6); http.expectNone('/api/facilities');
    for (const scope of [{...base,district_id:'MH-NAGPUR'}, {...base,offset:15}, {...base,search:'hospital'}, {...base,status:'WATCH'}, {...base,limit:5}]) {
      api.facilities(scope).subscribe(); http.expectOne(r => r.url === '/api/facilities').flush({items:[],total:0});
    }
    profile = 'redistribution-ready'; api.facilities(base).subscribe();
    const request = http.expectOne(r => r.url === '/api/facilities');
    expect(request.request.params.get('profile')).toBe(profile); request.flush({items:[],total:6});
  });
  it('isolates forecast resource, horizon, facility and country', () => {
    for (const [id, resource, country, horizon] of [['A','PCM','IN',14],['A','IVF','IN',14],['A','PCM','IN',7],['B','PCM','IN',14],['A','PCM','BR',14]] as const) {
      api.forecast(id,resource,country,horizon).subscribe(); http.expectOne(r => r.url.startsWith('/api/forecasts/')).flush({});
    }
    api.forecast('A','PCM','IN',14).subscribe(); http.expectNone(r => r.url.startsWith('/api/forecasts/'));
  });
  it('deduplicates identical in-flight calls and captures profile before queuing', () => {
    api.overview({country_id:'IN'}).subscribe(); api.overview({country_id:'IN'}).subscribe();
    api.facilities({country_id:'IN',limit:5}).subscribe(); profile = 'redistribution-ready';
    http.expectOne(r => r.url === '/api/overview').flush({});
    const queued = http.expectOne(r => r.url === '/api/facilities'); expect(queued.request.params.get('profile')).toBe('constrained'); queued.flush({});
  });
  it('never caches scenario/plan handles, scenario warnings, provider status or live federation status', () => {
    for (let i = 0; i < 2; i++) {
      api.scenario('actual', 'IN').subscribe(); http.expectOne(r => r.url === '/api/scenarios/actual').flush({});
      api.plan('actual', 'IN').subscribe(); http.expectOne(r => r.url === '/api/optimization/runs/actual').flush({});
      api.warnings({country_id:'IN',scenario_id:'actual'}).subscribe(); http.expectOne(r => r.url === '/api/warnings').flush({});
      api.geospatial({country_id:'IN',mode:'redistribution',run_id:'actual'}).subscribe(); http.expectOne(r => r.url === '/api/geospatial').flush({});
      api.copilotStatus().subscribe(); http.expectOne('/api/ai/status').flush({});
      api.federationStatus().subscribe(); http.expectOne(r => r.url === '/api/federation/status').flush({});
      api.scenarios('IN').subscribe(); http.expectOne(r => r.url === '/api/scenarios').flush([]);
    }
  });
  it('preserves exactly three GET retries for explicit operational_busy', fakeAsync(() => {
    let failed = false; api.overview({country_id:'IN'}).subscribe({error:() => failed = true});
    for (let i = 0; i < 4; i++) {
      http.expectOne(r => r.url === '/api/overview').flush({detail:{code:'operational_busy'}}, {status:429,statusText:'Too Many Requests'});
      if (i < 3) { tick(1999); http.expectNone(r => r.url === '/api/overview'); tick(1); }
    }
    expect(failed).toBeTrue();
  }));
  it('never retries quota, ambiguous network errors, or writes', fakeAsync(() => {
    for (const body of [{detail:{code:'provider_quota'}}, {detail:'other'}]) {
      api.overview({country_id:'IN'}).subscribe({error:() => {}});
      http.expectOne(r => r.url === '/api/overview').flush(body,{status:429,statusText:'Too Many Requests'});
      tick(6000); http.expectNone(r => r.url === '/api/overview');
    }
    api.overview({country_id:'IN'}).subscribe({error:() => {}});
    http.expectOne(r => r.url === '/api/overview').error(new ProgressEvent('error'));
    tick(6000); http.expectNone(r => r.url === '/api/overview');
    api.planningPreview({country_id:'IN',scope:'district',resources:['IVF'],horizon:14,time_limit_seconds:10}).subscribe({error:() => {}});
    http.expectOne('/api/optimization/preview').flush({detail:{code:'operational_busy'}},{status:429,statusText:'Too Many Requests'});
    tick(6000); http.expectNone('/api/optimization/preview');
  }));
});
