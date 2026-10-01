import { ApplicationRef } from '@angular/core';
import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { routes } from '../app.routes';
import { SelectivePreloading } from './selective-preloading';

describe('Selective standalone code preloading', () => {
  let stable: Subject<boolean>; let strategy: SelectivePreloading;
  beforeEach(() => {
    stable = new Subject<boolean>();
    Object.defineProperty(TestBed.inject(ApplicationRef), 'isStable', {value:stable});
    strategy = TestBed.inject(SelectivePreloading);
  });
  it('waits until initial app settles plus one second and loads code only', fakeAsync(() => {
    const load = jasmine.createSpy().and.returnValue(of('component'));
    strategy.preload({data:{preload:true}},load).subscribe();
    tick(2000); expect(load).not.toHaveBeenCalled(); stable.next(false); expect(load).not.toHaveBeenCalled();
    stable.next(true); tick(999); expect(load).not.toHaveBeenCalled(); tick(1); expect(load).toHaveBeenCalledTimes(1);
    strategy.preload({data:{preload:true}},load).subscribe(); expect(load).toHaveBeenCalledTimes(2);
  }));
  it('keeps heavy/action routes on demand while preserving lazy components', () => {
    const load = jasmine.createSpy().and.returnValue(of('component'));
    for (const path of ['geospatial','copilot','redistribution','emergency','brics']) {
      const route = routes.find(r => r.path === path)!;
      expect(route.loadComponent).toBeDefined(); strategy.preload(route,load).subscribe();
    }
    expect(load).not.toHaveBeenCalled();
    for (const path of ['overview','network','facilities','supply','alerts','facilities/:id','forecasts','warnings','model-performance','data-sources']) {
      const route = routes.find(r => r.path === path)!; expect(route.loadComponent).toBeDefined(); expect(route.data?.['preload']).toBeTrue();
    }
  });
  it('does not break navigation when a speculative chunk import fails', fakeAsync(() => {
    let failed = false; strategy.preload({data:{preload:true}}, () => throwError(() => 'offline')).subscribe({error:() => failed = true});
    stable.next(true); tick(1000); expect(failed).toBeFalse();
  }));
});
