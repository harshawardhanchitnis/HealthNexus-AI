import { Feature, FeatureCollection, Point, LineString } from 'geojson';
import { PlanningTransfer } from './optimization-models';
import { WarningItem } from './resilience-models';
export type MapMode = 'network' | 'forecast' | 'emergency' | 'redistribution';
export interface GeographicFacility {
  facility_id: string; name: string; facility_type: string; country_id: string;
  state_id: string; state_name: string; district_id: string; district_name: string;
  status: string; source_status: string; medicine_availability: number;
  bed_utilisation: number; staff_availability: number; role: string;
  forecast_signals: {resource_id:string;name:string;unit:string;stockout_risk_14:number;expected_unmet:number}[];
  warnings: WarningItem[]; scenario_affected: boolean; simulated: boolean;
}
export interface GeographicLane extends PlanningTransfer {
  map_distance_km: number; optimizer_distance_notice: string;
  donor_district_name: string; receiver_district_name: string;
  donor_state_name: string; receiver_state_name: string; label: string;
}
export interface GeospatialView {
  metadata: { mode: MapMode; profile: string; country_id: string; origin: string;
    donor_scope: string; scenario_id: string|null; run_id: string|null; data_notice:string; geometry_notice:string; };
  geography: {states: {id:string;name:string}[];districts:{id:string;name:string;state_id:string}[]};
  facilities: FeatureCollection<Point, GeographicFacility>;
  transfers: FeatureCollection<LineString, GeographicLane>;
  summary: {visible_facilities:number;visible_lanes:number;plan:null|{
    geography:{receiver_district_name:string;donor_districts:{id:string;name:string}[];cross_district_lane_count:number};
    safe_capacity:number;target_before:number;planned_accounting_items:number;unresolved:number;donor_violations:number;new_donor_risks:number;
  }};
}
export type FacilityFeature = Feature<Point, GeographicFacility>;
export type LaneFeature = Feature<LineString, GeographicLane>;
