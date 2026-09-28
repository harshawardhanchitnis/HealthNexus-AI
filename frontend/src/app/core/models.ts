export type Status = 'HEALTHY' | 'WATCH' | 'AT_RISK' | 'CRITICAL';
export interface Country {
  id: string;
  iso3: string;
  name: string;
  region_label: string;
  detailed: boolean;
}
export interface Provenance {
  id: string;
  source_type: string;
  source_name: string;
  source_url: string | null;
  accessed_at: string;
  license: string | null;
  geography: string[];
  is_synthetic: boolean;
  methodology: string;
  version: string;
  input_ids: string[];
  checksum_sha256: string | null;
}
export interface Observation {
  id: string;
  country_id: string;
  indicator: string;
  label: string;
  year: number;
  value: number;
  unit: string;
  provenance_id: string;
  source_record_id: string;
  note: string;
}
export interface Calibration {
  country_id?: string;
  public_sources_available?: boolean;
  inputs?: Observation[];
  assumptions?: string[];
  fallbacks?: string[];
  beds_per_10000?: number;
  doctors_per_10000?: number;
  doctors_by_type?: number[];
  nurses_by_type?: number[];
}
export interface DataSource {
  provenance: Provenance;
  status: string;
  cached: boolean;
  record_count: number;
  adapter_version: string;
  fields: string[];
  reference_years: number[];
  skipped_records: number;
}
export interface SourcesResponse {
  operational_profile: 'constrained' | 'redistribution-ready';
  profile_version: string;
  datasets: DataSource[];
  records: Observation[];
  notice: string;
  calibration: Calibration;
  expected_adapters: string[];
}
export interface Region {
  id: string;
  name: string;
  country_id: string;
  kind: 'state' | 'union_territory' | 'province' | 'municipality' | 'federal_subject';
  zone: string;
  latitude: number;
  longitude: number;
}
export interface District {
  id: string;
  name: string;
  state_id: string;
}
export interface Activity {
  date: string;
  footfall: number;
  medicine_units: number;
  occupied_beds: number;
}
export interface Summary {
  facilities: number;
  status_counts: Record<Status, number>;
  patient_footfall: number;
  medicine_availability: number;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  reserved_beds: number;
  bed_utilisation: number;
  staff_present: number;
  staff_scheduled: number;
  staff_availability: number;
  active_alerts: number;
}
export interface Alert {
  id: string;
  facility_id: string;
  facility_name: string;
  district_id: string | null;
  state_id: string;
  severity: Status;
  resource: string;
  title: string;
  explanation: string;
  recommended_action: string;
  method: string;
}
export interface Overview {
  country: Country;
  schema_version: number;
  calibration: Calibration;
  as_of: string;
  synthetic: boolean;
  summary: Summary;
  history: Activity[];
  alerts: Alert[];
  regions: (Region & Summary)[];
  coverage: {
    states: number;
    union_territories: number;
    sample_districts: number;
    notice: string;
    regions: number;
    complete_regions: boolean;
  };
}
export interface Inventory {
  ledger: {
    date: string;
    opening: number;
    received: number;
    requested: number;
    consumed: number;
    unmet_demand: number;
    closing: number;
  }[];
  medicine_id: string;
  name: string;
  unit: string;
  opening_stock: number;
  units_consumed: number;
  units_received: number;
  current_stock: number;
  safety_stock: number;
  average_daily_consumption: number;
  days_of_cover: number;
  status: Status;
}
export interface Facility {
  country_id: string;
  provenance_id: string;
  calibration_ids: string[];
  id: string;
  name: string;
  type: string;
  state_id: string;
  district_id: string | null;
  district_name: string;
  status: Status;
  resilience_score: number;
  footfall_today: number;
  beds: { total: number; available: number; occupied: number; reserved: number };
  staff: { scheduled: number; present: number; doctors_present: number; nurses_present: number };
  inventory: Inventory[];
  history: Activity[];
  synthetic: boolean;
}
export interface FacilityList {
  items: Facility[];
  total: number;
  offset: number;
  limit: number;
}
export interface Supply {
  medicine_id: string;
  name: string;
  unit: string;
  current_stock: number;
  daily_consumption: number;
  facilities_below_reserve: number;
  facilities: number;
}
