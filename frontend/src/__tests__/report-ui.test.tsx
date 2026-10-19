import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportView } from "@/components/ReportView";
import { reportToMarkdown } from "@/lib/reportExport";
import type { IncidentReport } from "@/lib/types";

// Hand-written fixture for rendering tests only. It is not model output.
const base: IncidentReport = {
  id: "rpt_test",
  created_at: "2026-10-20T10:00:00Z",
  mode: "simulation",
  status: "analysis_only",
  incident: {
    id: "sim-alb-503",
    title: "Fixture incident",
    summary: "s",
    category: "c",
    severity: "warning",
    affected_services: ["alb"],
    mode: "simulation",
  },
  decision: null,
  evidence: { incident_id: "sim-alb-503", mode: "simulation", items: [{ id: "E1", source: "alb", text: "Fixture evidence" }] },
  analysis: {
    summary: "Fixture summary",
    confirmed_facts: [],
    hypotheses: [
      { statement: "Maybe X", evidence_ids: ["E1"], what_would_confirm: "Check Y", plausibility: "possible" },
    ],
    probable_root_causes: [],
    recommended_actions: [
      { description: "Look at logs", kind: "read_only_check", risk: "low", rationale: "Because", evidence_ids: [] },
    ],
    impact_assessment: "Not determinable from the available evidence.",
    evidence_gaps: ["No memory metric"],
  },
  grounding: { facts_kept: 0, facts_demoted: 1, root_causes_demoted: 0, evidence_ids_removed: 0, warnings: ["Demoted one"] },
  generation: { ai_generated: true, provider: "Amazon Bedrock via Strands Agents SDK", model_id: "fixture-model", region: "r", latency_ms: 10 },
  advisory_notice: "AI-generated, advisory only.",
};

describe("ReportView", () => {
  it("labels AI generation, mode and advisory notice, and keeps facts apart from hypotheses", () => {
    render(<ReportView report={base} />);
    expect(screen.getByText(/AI-GENERATED · fixture-model/)).toBeTruthy();
    expect(screen.getByLabelText("Mode: simulation")).toBeTruthy();
    expect(screen.getByText("AI-generated, advisory only.")).toBeTruthy();
    expect(screen.getByText("No statement passed the evidence check.")).toBeTruthy();
    expect(screen.getByText("Maybe X")).toBeTruthy();
    expect(screen.getByText("Run without Decider 2B. No decision was made.")).toBeTruthy();
  });

  it("markdown export contains only report content and the simulation label", () => {
    const md = reportToMarkdown(base);
    expect(md).toContain("SIMULATION");
    expect(md).toContain("Maybe X");
    expect(md).toContain("_None passed grounding._");
    expect(md).not.toContain("Decider 2B decision");
  });
});
