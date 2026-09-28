import { Forecast } from './forecast-models';
export type ScenarioType =
  'DENGUE_SURGE' | 'DELIVERY_DELAY' | 'STAFF_SHORTAGE' | 'FACILITY_DISRUPTION';
export interface ScenarioDefinition {
  profile?: 'constrained' | 'redistribution-ready';
  scenario_type: ScenarioType;
  country_id: string;
  state_id?: string;
  district_id?: string;
  facility_ids: string[];
  duration: number;
  severity: string;
  seed: number;
  start_date?: string;
  parameters: {
    medicine_id?: string | null;
    delay_days?: number | null;
    unavailable_fraction?: number | null;
    capacity_reduction?: number | null;
  };
}
export interface ScenarioMetadata {
  scenario_id: string;
  definition: ScenarioDefinition;
  created_at: string;
  status: string;
  baseline_snapshot_id: string;
  origin: string;
  config_version: string;
  effective_parameters: Record<string, number | string>;
  assumptions: string[];
  data_status: string;
}
export interface WarningItem {
  warning_id: string;
  warning_type: string;
  category: string;
  severity: string;
  country_id: string;
  state_id: string;
  district_id: string | null;
  facility_id: string;
  facility_name: string;
  resource_id: string | null;
  generated_at: string;
  forecast_origin: string;
  horizon: number;
  current_value: number | null;
  threshold: number | null;
  predicted_value: number | null;
  estimated_event_date: string | null;
  model_based_probability: number | null;
  baseline_or_scenario: string;
  scenario_id: string | null;
  model_version: string;
  priority_score: number;
  baseline_severity: string | null;
  transition: string;
  recommended_next_step: string;
  explanation_factors: { factor: string; value: number | string; description: string }[];
  provenance: Record<string, string | boolean | number>;
}
export interface WarningList {
  items: WarningItem[];
  summary: {
    total: number;
    counts: Record<string, number>;
    facilities_affected: number;
    medicines_at_risk: number;
    bed_warnings: number;
    staff_warnings: number;
    by_country: Record<string, Record<string, number>>;
    by_region: Record<string, Record<string, number>>;
    by_district: Record<string, Record<string, number>>;
    by_facility: Record<string, Record<string, number>>;
  };
}
export interface OperationDay {
  date: string;
  footfall: number;
  syndrome_counts: Record<string, number>;
  admissions_requested: number;
  admissions: number;
  discharges: number;
  opening_occupied: number;
  occupied: number;
  bed_capacity: number;
  occupancy_ratio: number | null;
  bed_overflow: number;
  unmet_admissions: number;
  scheduled_staff: number;
  available_staff: number;
  service_capacity: number;
  served_patients: number;
  unserved_patients: number;
  workload_ratio: number | null;
}
export interface ResourceProjection {
  resource_id: string;
  name: string;
  unit: string;
  forecast: Forecast['forecast'];
  stockout: NonNullable<Forecast['stockout']>;
  requested_total: number;
  unmet_total: number;
}
export interface FacilityProjection {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  country_id: string;
  state_id: string;
  district_id: string | null;
  history: Forecast['history'];
  footfall: Forecast['forecast'];
  resources: ResourceProjection[];
  timeline: OperationDay[];
  provenance: Forecast['provenance'];
  receipt_changes: {
    resource_id: string;
    ordered_at: string;
    original_date: string;
    projected_date: string;
    quantity: number;
  }[];
  status: string;
  priority_score: number;
  source_models: Record<string, string>;
}
export interface Delta {
  baseline: number | null;
  scenario: number | null;
  absolute: number | null;
  percent: number | null;
  unit: string;
}
export interface ScenarioResult {
  scenario: ScenarioMetadata;
  baseline: { metrics: Record<string, number | null>; facilities: FacilityProjection[] };
  scenario_result: { metrics: Record<string, number | null>; facilities: FacilityProjection[] };
  delta: Record<string, Delta>;
  resource_impact: {
    resource_id: string;
    name: string;
    unit: string;
    demand: Delta;
    unmet_demand: Delta;
    max_stockout_risk: Delta;
  }[];
  baseline_warnings: WarningList;
  warnings_created: WarningList;
}
