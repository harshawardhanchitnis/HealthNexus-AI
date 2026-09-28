export type CopilotMode = 'gemini' | 'offline';
export interface CopilotContext {
  country_id: string; profile: string; state_id?: string | null; district_id?: string | null;
  facility_id?: string | null; scenario_id?: string | null; optimization_run_id?: string | null;
}
export interface CopilotRequest extends CopilotContext {
  message: string; mode: CopilotMode; allow_planning: boolean; compare_profiles: boolean;
  request_id: string; conversation_id?: string;
}
export interface CopilotClaim {
  text: string; references: { evidence_id: string; field: string }[];
}
export interface CopilotTrace {
  tool: string; status: 'running' | 'success' | 'error'; seconds: number; summary: string;
  evidence_id?: string | null;
}
export interface CopilotEvidence {
  evidence_id: string; tool: string; source_type: string; source_id: string | null;
  field: string; value: unknown; profile: string; unit: string | null;
}
export interface CopilotResponse {
  request_id: string; conversation_id: string | null; mode: CopilotMode | 'refusal';
  status: 'completed' | 'refused'; answer: string; situation: CopilotClaim | null;
  key_risks: CopilotClaim[]; recommended_actions: CopilotClaim[]; remaining_gaps: CopilotClaim[];
  evidence: CopilotEvidence[]; tools_used: CopilotTrace[]; limitations: string[];
  context: CopilotContext; scenario_id: string | null; optimization_run_id: string | null;
  metadata: { total_seconds?: number; gemini_network_seconds?: number; tool_seconds?: number;
    model?: string | null; interaction_id?: string | null; usage?: unknown[] };
  operational_results: { evidence_id: string; tool: string; result: Record<string, unknown> }[];
}
export interface CopilotStatus {
  configured: boolean; enabled: boolean; model: string; configuration_status: string;
  runtime_status: string; thinking_level: string; setup: string;
}
export interface CopilotProgress { status: string; phase: string; tools: CopilotTrace[]; }
export interface CopilotPlan {
  run_id: string; scenario_id: string | null; solver: { status: string };
  safe_capacity: number; impact: { before: { target_deficit: number; expected_unmet: number };
    after: { target_deficit: number; expected_unmet: number }; transferred_units: number;
    transfer_count: number; new_donor_risks: number; donor_safety_violations: number;
    unresolved: Record<string, number> };
  transfers: { donor_name: string; receiver_name: string; resource_id: string; quantity: number;
    unit: string; distance_km: number; donor_protected_minimum_after: number;
    donor_protected_reserve: number }[];
  transfers_truncated: boolean; unit_notice: string;
  resource_risks: {facility_id:string; resource_id:string; unit:string;
    risk_before:Record<string,number>;risk_after:Record<string,number>;unresolved:number}[];
  resource_risks_truncated:boolean;
}
