import { FacilityProjection, WarningList } from './resilience-models';
export interface PlanningRequest {
  profile?: string;
  country_id: string;
  state_id?: string;
  district_id?: string;
  scenario_id?: string;
  scope: 'district' | 'cross_district' | 'state' | 'national';
  resources: string[];
  horizon: 14;
  time_limit_seconds: number;
}
export interface PlanningCandidate {
  facility_id: string;
  facility_name: string;
  resource_id: string;
  unit: string;
  current_stock: number;
  protected_reserve: number;
  safe_surplus: number;
  protected_minimum_stock: number;
  reserve_after_max_donation: number;
  deficit: number;
  expected_unmet: number;
  depletion_date: string | null;
  safety_breach_date: string | null;
  risk: Record<string, number>;
  severity: string;
  priority: number;
  critical: boolean;
  nearest_receiver_distance_km: number | null;
}
export interface PlanningPreview {
  request: PlanningRequest;
  snapshot_id: string;
  scenario_snapshot_id: string | null;
  origin: string;
  config_version: string;
  model_version: string;
  receivers: PlanningCandidate[];
  donors: PlanningCandidate[];
  total_deficit: number;
  safe_capacity: number;
  capacity_by_resource: Record<string, number>;
  deficit_by_resource: Record<string, number>;
  limitations: string[];
}
export interface PlanningMetrics {
  target_deficit: number;
  expected_unmet: number;
  critical_resource_warnings: number;
  facilities_at_risk: number;
  max_stockout_risk: number;
}
export interface PlanningImpact {
  before: PlanningMetrics;
  after: PlanningMetrics;
  shortage_units_resolved: number;
  percent_deficit_resolved: number;
  critical_deficits_resolved: number;
  critical_deficits_total: number;
  facilities_protected: number;
  donor_facilities_used: number;
  transfer_count: number;
  transferred_units: number;
  distance_km: number;
  distance_weighted_units: number;
  donor_safety_violations: number;
  new_donor_risks: number;
  unresolved: Record<string, number>;
  conservation: Record<string, { before: number; after: number }>;
}
export interface PlanningTransfer {
  transfer_id: string;
  donor_id: string;
  donor_name: string;
  donor_state_id: string;
  donor_district_id: string;
  receiver_state_id: string;
  receiver_district_id: string;
  cross_district: boolean;
  plan_mode: string;
  receiver_id: string;
  receiver_name: string;
  resource_id: string;
  unit: string;
  quantity: number;
  distance_km: number;
  donor_stock_before: number;
  donor_stock_after: number;
  donor_protected_reserve: number;
  donor_projected_stock_after: number;
  donor_protected_minimum_after: number;
  donor_risk_before: Record<string, number>;
  donor_risk_after: Record<string, number>;
  receiver_deficit_before: number;
  receiver_deficit_after: number;
  receiver_warning_before: string;
  receiver_warning_after: string;
  receiver_risk_before: Record<string, number>;
  receiver_risk_after: Record<string, number>;
  rationale: Record<string, number | string>;
  objective_contribution: Record<string, number>;
}
export interface PlanningResult {
  geography: { receiver_district_name: string; donor_scope: string; donor_districts: {id:string;name:string}[]; donor_district_count:number; cross_district_lane_count:number; };
  run_id: string;
  created_at: string;
  preview: PlanningPreview;
  solver: {
    engine: string;
    version: string;
    status: string;
    termination: string;
    objective: number[] | null;
    time_limit_seconds: number;
    elapsed_seconds: number;
    variables: number;
    constraints: number;
    stages: {
      name: string;
      status: string;
      objective: number | null;
      best_bound: number | null;
      seconds: number;
    }[];
  };
  transfers: PlanningTransfer[];
  impact: PlanningImpact;
  greedy: PlanningImpact;
  greedy_transfers: PlanningTransfer[];
  before: FacilityProjection[];
  after: FacilityProjection[];
  before_warnings: WarningList;
  after_warnings: WarningList;
  message: string;
}
