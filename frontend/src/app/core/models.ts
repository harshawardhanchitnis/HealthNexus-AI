export type Status = 'HEALTHY' | 'WATCH' | 'AT_RISK' | 'CRITICAL';
export interface Region {
  id: string;
  name: string;
  kind: 'state' | 'union_territory';
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
  district_id: string;
  state_id: string;
  severity: Status;
  resource: string;
  title: string;
  explanation: string;
  recommended_action: string;
  method: string;
}
export interface Overview {
  as_of: string;
  synthetic: boolean;
  summary: Summary;
  history: Activity[];
  alerts: Alert[];
  regions: (Region & Summary)[];
  coverage: { states: number; union_territories: number; sample_districts: number; notice: string };
}
export interface Inventory {
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
  id: string;
  name: string;
  type: string;
  state_id: string;
  district_id: string;
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
