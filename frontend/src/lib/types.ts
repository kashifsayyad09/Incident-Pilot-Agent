// Mirrors backend/app/schemas.py. Keep in sync with shared/openapi.json.

export type Mode = "simulation" | "live";
export type Severity = "info" | "warning" | "critical";
export type ServiceKind = "alb" | "ec2" | "rds" | "cloudwatch";

export const TOOL_OPTIONS = [
  "investigate_load_balancer",
  "investigate_ec2",
  "investigate_database",
  "investigate_cloudwatch_logs",
  "collect_more_evidence",
] as const;
export type ToolOption = (typeof TOOL_OPTIONS)[number];

export type DecisionOutcome = "tool_selected" | "evidence_requested" | "human_review";

export interface ComponentStatus {
  name: string;
  available: boolean;
  detail: string | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  mode: Mode;
  components: ComponentStatus[];
}

export interface IncidentSummary {
  id: string;
  title: string;
  summary: string;
  category: string;
  severity: Severity;
  affected_services: ServiceKind[];
  mode: Mode;
}

export interface IncidentList {
  mode: Mode;
  incidents: IncidentSummary[];
  notice: string | null;
}

export interface DecisionStatus {
  available: boolean;
  adapter: string | null;
  reason: string | null;
  confidence_threshold: number;
  options: ToolOption[];
}

export interface DecisionResult {
  incident_id: string;
  mode: Mode;
  input_state: Record<string, unknown>;
  /** The exact text the model read. */
  state_text: string;
  question: string;
  options: ToolOption[];
  selected: ToolOption;
  /** Model's own confidence, unmodified. */
  confidence: number;
  /** Model's own per-option probabilities, unmodified. */
  probabilities: Record<string, number>;
  model: string | null;
  /** Server-reported inference time; null when the server did not report it. */
  latency_ms: number | null;
  /** Measured by the API: request sent to response parsed. */
  roundtrip_ms: number;
  confidence_threshold: number;
  meets_threshold: boolean;
  outcome: DecisionOutcome;
  reason: string;
  /** Always null until diagnostic tools exist (Phase 4). */
  tool_invoked: string | null;
}
