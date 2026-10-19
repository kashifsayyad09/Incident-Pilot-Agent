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

// ---- Phase 3: reports (mirrors backend/app/agent/report.py) ----

export type EvidenceSource = "alb" | "ec2" | "rds" | "cloudwatch_alarm" | "change" | "log";

export interface EvidenceItem {
  id: string;
  source: EvidenceSource;
  text: string;
}

export interface EvidenceBundle {
  incident_id: string;
  mode: Mode;
  items: EvidenceItem[];
}

export interface Fact {
  statement: string;
  evidence_ids: string[];
}

export interface Hypothesis {
  statement: string;
  evidence_ids: string[];
  what_would_confirm: string;
  plausibility: "leading" | "possible" | "unlikely";
}

export interface RootCause {
  description: string;
  basis: "confirmed" | "hypothesis";
  evidence_ids: string[];
}

export interface RecommendedAction {
  description: string;
  kind: "read_only_check" | "human_executed_change";
  risk: "low" | "medium" | "high";
  rationale: string;
  evidence_ids: string[];
}

export interface IncidentAnalysis {
  summary: string;
  confirmed_facts: Fact[];
  hypotheses: Hypothesis[];
  probable_root_causes: RootCause[];
  recommended_actions: RecommendedAction[];
  impact_assessment: string;
  evidence_gaps: string[];
}

export interface GroundingReport {
  facts_kept: number;
  facts_demoted: number;
  root_causes_demoted: number;
  evidence_ids_removed: number;
  warnings: string[];
}

export interface Generation {
  ai_generated: boolean;
  provider: string;
  model_id: string;
  region: string;
  latency_ms: number;
}

export type ReportStatus =
  | "complete"
  | "needs_more_evidence"
  | "needs_human_review"
  | "analysis_only";

export interface IncidentReport {
  id: string;
  created_at: string;
  mode: Mode;
  status: ReportStatus;
  incident: IncidentSummary;
  decision: DecisionResult | null;
  evidence: EvidenceBundle;
  analysis: IncidentAnalysis;
  grounding: GroundingReport;
  generation: Generation;
  advisory_notice: string;
}
