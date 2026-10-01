import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { WarningsPage } from './warnings';

describe('Cached baseline warnings with fresh scenario choices', () => {
  it('shows valid cached evidence without waiting for a mutable scenario list and reports list failure', () => {
    const params = {country_id:'IN', state_id:'MH', district_id:'MH-PUNE', profile:'constrained'};
    TestBed.configureTestingModule({providers:[provideRouter([]),provideHttpClient(),provideHttpClientTesting(),
      {provide:ActivatedRoute,useValue:{queryParamMap:of(convertToParamMap(params)),snapshot:{queryParamMap:convertToParamMap(params)}}}]});
    spyOnProperty(TestBed.inject(Router),'url','get').and.returnValue('/warnings?profile=constrained');
    const api = TestBed.inject(NetworkApi), http = TestBed.inject(HttpTestingController);
    const warnings = {items:[],summary:{total:0,counts:{},facilities_affected:0}};
    api.warnings(params).subscribe(); http.expectOne(r => r.url === '/api/warnings').flush(warnings);
    const page = TestBed.runInInjectionContext(() => new WarningsPage());
    expect(page.loading()).toBeFalse(); expect(page.data()).toEqual(jasmine.objectContaining(warnings));
    http.expectNone(r => r.url === '/api/warnings');
    http.expectOne(r => r.url === '/api/scenarios').flush({detail:'unavailable'},{status:503,statusText:'Unavailable'});
    expect(page.error()).toBe(''); expect(page.data()).not.toBeNull(); expect(page.scenarioListError()).toBeTrue(); http.verify();
  });
});
