import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { BricsPage } from './brics';
import { NetworkApi } from '../core/network-api';

describe('Federation deployment capabilities', () => {
  for (const training of [false,true]) {
    it(training ? 'keeps explicit local training available' : 'shows saved nodes without foreign operational navigation or training', () => {
      const nodes = ['IN','BR','RU','CN','ZA'].map(country_id=>({country_id,raw_records_shared:0,status:training?'ready':'saved_evidence'}));
      const api = {
        profile:()=> 'constrained',
        countries:jasmine.createSpy('countries'),
        federationNodes:()=>of({items:nodes}),
        federationStatus:()=>of({available:training,active_run_id:null,parameter_count:417,raw_records_shared:0}),
        savedFederation:()=>of(null),
      };
      TestBed.configureTestingModule({imports:[BricsPage],providers:[provideRouter([]),{provide:NetworkApi,useValue:api}]});
      const fixture=TestBed.createComponent(BricsPage);fixture.detectChanges();
      const element:HTMLElement=fixture.nativeElement;
      expect(element.querySelectorAll('.node-card').length).toBe(5);
      expect(element.querySelector('.federation-controls') !== null).toBe(training);
      expect(element.querySelectorAll('.node-card a').length).toBe(training?5:0);
      expect(api.countries).not.toHaveBeenCalled();
      if(!training) expect(element.textContent).toContain('Verified saved experiment only');
    });
  }
});
