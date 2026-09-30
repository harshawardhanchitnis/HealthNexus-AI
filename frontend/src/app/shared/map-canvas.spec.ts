import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Map, MapOptions } from 'maplibre-gl';
import { MapCanvas, MAP_FACTORY, BASEMAP_STYLE } from './map-canvas';
import { GeospatialView } from '../core/geospatial-models';

export function mapView():GeospatialView {
  return {metadata:{mode:'network',profile:'redistribution-ready',country_id:'IN',origin:'2026-09-27',donor_scope:'cross_district',scenario_id:null,run_id:null,data_notice:'Simulated',geometry_notice:'Illustrative'},
    geography:{states:[{id:'MH',name:'Maharashtra'}],districts:[{id:'MH-PUNE',name:'Pune',state_id:'MH'}]},
    facilities:{type:'FeatureCollection',features:[{type:'Feature',id:'receiver',geometry:{type:'Point',coordinates:[73.8,18.5]},properties:{facility_id:'receiver',name:'Illustrative receiver',facility_type:'PHC',country_id:'IN',state_id:'MH',state_name:'Maharashtra',district_id:'MH-PUNE',district_name:'Pune',status:'CRITICAL',source_status:'CRITICAL',medicine_availability:20,bed_utilisation:70,staff_availability:80,role:'receiver',forecast_signals:[],warnings:[],scenario_affected:true,simulated:true}}]},
    transfers:{type:'FeatureCollection',features:[]},summary:{visible_facilities:1,visible_lanes:0,plan:null}};
}
export class FakeMap {
  listeners:Record<string,((event:unknown)=>void)[]>={};
  sources:Record<string,{setData:jasmine.Spy}>={};
  layers=new Set<string>();
  addControl=jasmine.createSpy('addControl');fitBounds=jasmine.createSpy('fitBounds');resize=jasmine.createSpy('resize');remove=jasmine.createSpy('remove');
  setStyle=jasmine.createSpy('setStyle').and.callFake(()=>{this.sources={};this.layers.clear();});
  on(name:string, layerOrCallback:unknown, callback?:unknown){const fn=(callback||layerOrCallback) as (event:unknown)=>void;(this.listeners[name]||=[]).push(fn);return this;}
  emit(name:string,event:unknown={}){for(const fn of this.listeners[name]||[])fn(event);}
  getSource(id:string){return this.sources[id];}
  addSource(id:string){this.sources[id]={setData:jasmine.createSpy('setData')};}
  getLayer(id:string){return this.layers.has(id);}
  addLayer(layer:{id:string}){this.layers.add(layer.id);}
}

describe('MapCanvas lifecycle and graceful degradation',()=>{
  let map:FakeMap;let factory:jasmine.Spy;
  beforeEach(()=>{map=new FakeMap();factory=jasmine.createSpy('factory').and.returnValue(map as unknown as Map);
    TestBed.configureTestingModule({imports:[MapCanvas],providers:[{provide:MAP_FACTORY,useValue:factory}]});});
  it('creates exactly one public, keyless map and updates authoritative source data',()=>{
    const f=TestBed.createComponent(MapCanvas);f.componentRef.setInput('data',mapView());f.detectChanges();map.emit('style.load');
    const original=map.sources['facilities'];
    f.componentRef.setInput('data',{...mapView(),metadata:{...mapView().metadata,mode:'forecast'}});f.detectChanges();
    expect(factory).toHaveBeenCalledTimes(1);expect((factory.calls.first().args[0] as MapOptions).style).toBe(BASEMAP_STYLE);
    expect(map.sources['facilities']).toBe(original);expect(original.setData.calls.mostRecent().args[0].features[0].id).toBe('receiver');
    f.destroy();expect(map.remove).toHaveBeenCalledTimes(1);
  });
  it('clears obsolete overlays when context is loading or rejected',()=>{
    const f=TestBed.createComponent(MapCanvas);f.componentRef.setInput('data',mapView());f.detectChanges();map.emit('style.load');
    f.componentRef.setInput('data',null);f.detectChanges();
    expect(map.sources['facilities'].setData.calls.mostRecent().args[0].features).toEqual([]);
    expect(map.sources['lanes'].setData.calls.mostRecent().args[0].features).toEqual([]);f.destroy();
  });
  it('fits cross-district donor and receiver coordinates together without animation',()=>{
    const f=TestBed.createComponent(MapCanvas);const view=mapView();view.facilities.features.push({...view.facilities.features[0],id:'donor',geometry:{type:'Point',coordinates:[79.1,21.1]}});
    f.componentRef.setInput('data',view);f.detectChanges();map.emit('style.load');
    expect(map.fitBounds).toHaveBeenCalledWith([[73.8,18.5],[79.1,21.1]],{padding:48,maxZoom:11,duration:0});f.destroy();
  });
  it('cancels failed basemap once, restores local layers and retains visible attribution',()=>{
    const f=TestBed.createComponent(MapCanvas);f.componentRef.setInput('data',mapView());f.detectChanges();
    map.emit('error');map.emit('error');map.emit('style.load');f.detectChanges();
    expect(map.setStyle).toHaveBeenCalledTimes(1);expect(map.layers.has('facilities')).toBeTrue();
    expect(map.sources['facilities'].setData.calls.mostRecent().args[0].features.length).toBe(1);
    expect(f.nativeElement.textContent).toContain('Base map unavailable');
    expect(f.nativeElement.textContent).toContain('OpenFreeMap');expect(f.nativeElement.textContent).toContain('OpenStreetMap');f.destroy();
  });
  it('has a bounded cold-load timeout and cancels it after disposal',fakeAsync(()=>{
    const f=TestBed.createComponent(MapCanvas);f.detectChanges();tick(15001);expect(map.setStyle).toHaveBeenCalledTimes(1);
    f.destroy();tick(30000);expect(map.setStyle).toHaveBeenCalledTimes(1);
  }));
  it('map selection emits authoritative IDs and zero transfer sources stay empty',()=>{
    const f=TestBed.createComponent(MapCanvas);const selected=jasmine.createSpy('selection');f.componentInstance.facilitySelected.subscribe(selected);
    f.componentRef.setInput('data',mapView());f.detectChanges();map.emit('style.load');map.emit('click',{features:[{id:'receiver'}]});
    expect(selected).toHaveBeenCalledWith('receiver');expect(map.sources['lanes'].setData.calls.mostRecent().args[0].features).toEqual([]);f.destroy();
  });
});
