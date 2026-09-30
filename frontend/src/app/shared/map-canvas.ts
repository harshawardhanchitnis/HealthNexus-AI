import { AfterViewInit, Component, ElementRef, OnDestroy, NgZone, InjectionToken, inject, input, output, effect, signal, ViewChild } from '@angular/core';
import { Map, MapOptions, NavigationControl, GeoJSONSource, setWorkerUrl } from 'maplibre-gl';
import { GeospatialView } from '../core/geospatial-models';

export const MAP_FACTORY = new InjectionToken<(options:MapOptions)=>Map>('MapLibre factory', {
  providedIn:'root',factory:()=>options=>new Map(options),
});
export const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/positron';
@Component({selector:'app-map-canvas',template:`
  <link rel="stylesheet" href="/maplibre/maplibre-gl.css">
  <div #host class="map-surface" aria-label="Geographic network visualization" role="region"></div>
  @if(unavailable()) {<div class="map-message" role="status"><strong>Base map unavailable</strong><span>Operational overlays and the synchronized list remain available.</span></div>}
  <div class="map-credit"><a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> · <a href="https://openmaptiles.org" target="_blank" rel="noopener">OpenMapTiles</a> · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap</a></div>`,
  styles:[`:host{display:block;position:relative;min-width:0}.map-surface{height:570px;min-height:350px;background:#eaf0f5;border-radius:12px}.map-credit{position:absolute;bottom:0;left:0;background:#fffffff0;font-size:10px;padding:3px 6px;max-width:calc(100% - 90px)}.map-credit a{color:#425975}.map-message{position:absolute;top:12px;left:12px;right:55px;background:#fff;border:1px solid #c5d1df;border-radius:8px;padding:12px;font-size:12px;display:grid;gap:4px}@media(max-width:600px){.map-surface{height:420px}}`],
})
export class MapCanvas implements AfterViewInit, OnDestroy {
  @ViewChild('host',{static:true}) host!:ElementRef<HTMLElement>;
  data=input<GeospatialView|null>(null);
  facilitySelected=output<string>(); laneSelected=output<string>();
  unavailable=signal(false);
  private zone=inject(NgZone); private factory=inject(MAP_FACTORY);
  private map?:Map; private ready=false; private timer?:ReturnType<typeof setTimeout>;
  private observer?:ResizeObserver;
  constructor(){effect(()=>{this.data();this.update();});}
  ngAfterViewInit(){
    this.zone.runOutsideAngular(()=>{
      try {
        setWorkerUrl('/maplibre/maplibre-gl-worker.mjs');
        this.map=this.factory({container:this.host.nativeElement,style:BASEMAP_STYLE,center:[79,23],zoom:4,
          attributionControl:false,maxZoom:15,renderWorldCopies:false});
        this.map.addControl(new NavigationControl({showCompass:false}),'top-right');
        this.map.on('style.load',()=>{this.ready=true;this.installLayers();this.update();});
        this.map.on('load',()=>{if(this.timer)clearTimeout(this.timer);});
        this.map.on('error',()=>this.fail());
        this.map.on('click','facilities',(e)=>{const id=e.features?.[0]?.id;if(id)this.zone.run(()=>this.facilitySelected.emit(String(id)));});
        this.map.on('click','lanes',(e)=>{const id=e.features?.[0]?.id;if(id)this.zone.run(()=>this.laneSelected.emit(String(id)));});
        this.timer=setTimeout(()=>this.fail(),15000);
        this.observer=new ResizeObserver(()=>this.map?.resize());this.observer.observe(this.host.nativeElement);
      } catch {this.zone.run(()=>this.unavailable.set(true));}
    });
  }
  private fail(){
    if(this.unavailable())return;
    this.zone.run(()=>this.unavailable.set(true));if(this.timer)clearTimeout(this.timer);
    // Cancel failed basemap sources; never retry automatically or lose local overlays.
    try{this.ready=false;this.map?.setStyle({version:8,sources:{},layers:[]},{diff:false});}catch{/* WebGL unavailable: list is authoritative. */}
  }
  private installLayers(){
    const map=this.map!;
    const empty={type:'FeatureCollection' as const,features:[]};
    if(!map.getSource('facilities'))map.addSource('facilities',{type:'geojson',data:empty});
    if(!map.getSource('lanes'))map.addSource('lanes',{type:'geojson',data:empty});
    if(!map.getLayer('lanes'))map.addLayer({id:'lanes',type:'line',source:'lanes',paint:{'line-color':'#255bc2','line-width':3,'line-opacity':0.8},layout:{'line-cap':'round'}});
    if(!map.getLayer('facility-halo'))map.addLayer({id:'facility-halo',type:'circle',source:'facilities',paint:{'circle-radius':['match',['get','role'],'donor',13,'receiver',15,9],'circle-color':['match',['get','role'],'donor','#9864d8','receiver','#ea6b59','#fff'],'circle-opacity':0.3}});
    if(!map.getLayer('facilities'))map.addLayer({id:'facilities',type:'circle',source:'facilities',paint:{'circle-radius':['match',['get','facility_type'],'District Hospital',7,'CHC',6,5],'circle-color':['match',['get','status'],'CRITICAL','#c53e45','AT_RISK','#df7833','WATCH','#c79522','#249882'],'circle-stroke-color':'#fff','circle-stroke-width':2}});
  }
  private update(){
    const view=this.data(),map=this.map;if(!map||!this.ready)return;
    const empty={type:'FeatureCollection' as const,features:[]};
    (map.getSource('facilities') as GeoJSONSource)?.setData(view?.facilities||empty);
    (map.getSource('lanes') as GeoJSONSource)?.setData(view?.transfers||empty);
    if(!view)return;
    const coords=view.facilities.features.map(f=>f.geometry.coordinates);
    if(coords.length){const xs=coords.map(c=>c[0]!),ys=coords.map(c=>c[1]!);
      map.fitBounds([[Math.min(...xs),Math.min(...ys)],[Math.max(...xs),Math.max(...ys)]],{padding:48,maxZoom:11,duration:0});}
  }
  ngOnDestroy(){if(this.timer)clearTimeout(this.timer);this.observer?.disconnect();this.map?.remove();this.map=undefined;}
}
