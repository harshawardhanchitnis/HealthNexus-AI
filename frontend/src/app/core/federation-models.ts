export interface FederationMetric {
  samples: number; mae: number; rmse: number; wape: number | null; normalized_mae: number;
}
export interface FederationNode {
  country_id: string; status?: string; local_samples?: number; validation_samples?: number;
  test_samples?: number; facility_count?: number; history_days?: number; raw_records_shared: number;
  local_only?: FederationMetric; initial_global?: FederationMetric; federated_global?: FederationMetric;
  change?: string; wape_change_vs_local?: number; latest_update_bytes?: number;
}
export interface FederationUpdate {
  country_id: string; sample_count: number; bytes_transferred: number; raw_records_shared: number;
  train_loss_before: number; train_loss_after: number; parameter_checksum: string;
}
export interface FederationRound {
  round: number; global_validation: FederationMetric; update_bytes: number; downlink_bytes: number;
  raw_records_shared: number; clients: FederationUpdate[]; weights: Record<string, number>;
}
export interface FederationRequest {
  rounds: number; local_epochs: number; seed: number; policy: 'sample-weighted' | 'balanced-country';
}
export interface FederationRun {
  saved_demo?: boolean;
  run_id: string; model_version: string; status: string; policy: string; config: FederationRequest;
  current_round: number; current_country: string | null; stage: string; message: string;
  nodes: FederationNode[]; rounds: FederationRound[]; raw_records_shared: number; bytes_exchanged: number;
  events: {timestamp: string; stage: string; round: number; country_id: string | null; message: string}[];
  training_seconds?: number; global_test?: FederationMetric; parameter_count?: number;
  update_bytes?: number; downlink_bytes?: number; aggregate_metadata_bytes?: number;
}
export interface FederationStatus {
  available: boolean; active_run_id: string | null; parameter_count: number; client_count: number;
  raw_records_shared: number; notice: string; phase6_status: string;
}
