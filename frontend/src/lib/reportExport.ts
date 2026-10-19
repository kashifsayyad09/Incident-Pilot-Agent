import type { IncidentReport } from "./types";

const ids = (x: string[]) => (x.length ? ` _(${x.join(", ")})_` : "");

/** Markdown rendering of a stored report. Only fields present in the report are written. */
export function reportToMarkdown(r: IncidentReport): string {
  const a = r.analysis;
  const L: string[] = [];
  L.push(`# ${r.incident.title}`, "");
  L.push(
    `- Report: \`${r.id}\``,
    `- Created: ${r.created_at}`,
    `- Data mode: **${r.mode === "simulation" ? "SIMULATION" : "LIVE AWS"}**`,
    `- Status: ${r.status}`,
    `- Analysis: ${r.generation.provider}, \`${r.generation.model_id}\` (${r.generation.region}), AI-generated`,
    "",
    `> ${r.advisory_notice}`,
    "",
  );
  L.push("## Summary", "", a.summary, "");
  if (r.decision) {
    const d = r.decision;
    L.push(
      "## Decider 2B decision",
      "",
      `- Selected: \`${d.selected}\``,
      `- Confidence: ${d.confidence.toFixed(3)} (threshold ${d.confidence_threshold.toFixed(2)})`,
      `- Outcome: ${d.outcome}`,
      `- Server latency: ${d.latency_ms === null ? "not reported" : `${d.latency_ms.toFixed(1)} ms`}; round trip ${d.roundtrip_ms.toFixed(1)} ms`,
      `- Model: ${d.model ?? "not reported"}`,
      "",
    );
  }
  L.push("## Confirmed facts", "");
  L.push(...(a.confirmed_facts.length ? a.confirmed_facts.map((f) => `- ${f.statement}${ids(f.evidence_ids)}`) : ["_None passed grounding._"]), "");
  L.push("## Hypotheses (not confirmed)", "");
  L.push(
    ...(a.hypotheses.length
      ? a.hypotheses.map((h) => `- **${h.plausibility}**: ${h.statement}${ids(h.evidence_ids)}. To confirm: ${h.what_would_confirm}`)
      : ["_None._"]),
    "",
  );
  L.push("## Probable root causes", "");
  L.push(...(a.probable_root_causes.length ? a.probable_root_causes.map((c) => `- (${c.basis}) ${c.description}${ids(c.evidence_ids)}`) : ["_None._"]), "");
  L.push("## Recommended actions (advisory)", "");
  L.push(
    ...(a.recommended_actions.length
      ? a.recommended_actions.map((x, i) => `${i + 1}. [${x.kind}, risk ${x.risk}] ${x.description}. ${x.rationale}${ids(x.evidence_ids)}`)
      : ["_None._"]),
    "",
  );
  L.push("## Impact", "", a.impact_assessment, "");
  L.push("## Evidence gaps", "", ...(a.evidence_gaps.length ? a.evidence_gaps.map((g) => `- ${g}`) : ["_None stated._"]), "");
  L.push("## Evidence", "", ...r.evidence.items.map((e) => `- **${e.id}** [${e.source}] ${e.text}`), "");
  L.push(
    "## Grounding",
    "",
    `Facts kept ${r.grounding.facts_kept}, demoted ${r.grounding.facts_demoted}; root causes downgraded ${r.grounding.root_causes_demoted}; unknown evidence ids removed ${r.grounding.evidence_ids_removed}.`,
    ...r.grounding.warnings.map((w) => `- ${w}`),
    "",
  );
  return L.join("\n");
}

export function downloadText(filename: string, text: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
