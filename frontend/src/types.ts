export type HopStatus = "ok" | "break" | "unknown";

export type HopStage =
  | "customer_channel"
  | "authentication"
  | "payment_api"
  | "payment_switch"
  | "payment_rail"
  | "receiving_institution"
  | "core_banking"
  | "settlement_reconciliation";

export interface RawArtifact {
  id: string;
  source: string;
  artifact_type: string;
  timestamp: string;
  raw_payload: Record<string, unknown>;
}

export interface Hop {
  id: string;
  sequence: number;
  stage: HopStage;
  status: HopStatus;
  artifacts: RawArtifact[];
  started_at: string | null;
  completed_at: string | null;
  notes: string | null;
}

export interface TransactionRef {
  reference: string;
  reference_type: "rail_reference" | "core_transaction_id" | "session_id";
  rail: "raast_p2p";
}

export interface TransactionDigitalTwin {
  id: string;
  ref: TransactionRef;
  created_at: string;
  hops: Hop[];
  break_hop_id: string | null;
  correlation_version: string;
}

export interface RootCauseCandidate {
  label: string;
  confidence: number;
  cited_hop_ids: string[];
  pattern_id: string | null;
}

export interface InvestigationResult {
  twin: TransactionDigitalTwin;
  explanation: string;
  root_causes: RootCauseCandidate[];
  recommendation: string;
  generated_at: string;
  model_version: string;
  self_corrected: boolean;
}

export interface ConnectorStatus {
  name: string;
  healthy: boolean;
  detail: string | null;
}

export interface DemoReference {
  reference: string;
  reference_type: TransactionRef["reference_type"];
  label: string;
  description: string;
}
