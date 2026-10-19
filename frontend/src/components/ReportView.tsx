import type { IncidentReport, ReportStatus } from "@/lib/types";
import { ConfidenceMeter, ModeBadge } from "@/components/ui";

const STATUS_LABEL: Record<ReportStatus, string> = {
  complete: "COMPLETE",
  needs_more_evidence: "NEEDS MORE EVIDENCE",
  needs_human_review: "NEEDS HUMAN REVIEW",
  analysis_only: "ANALYSIS ONLY (NO DECIDER)",
};

function Ids({ ids }: { ids: string[] }) {
  if (!ids.length) return null;
  return (
    <span className="ml-2 font-mono text-[11px] text-text-faint">[{ids.join(", ")}]</span>
  );
}

function Section({ title, tone, children }: { title: string; tone?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-card border border-border bg-surface-2/40 p-4">
      <h3 className={`mb-2 font-semibold ${tone ?? ""}`}>{title}</h3>
      {children}
    </section>
  );
}

const None = ({ children = "None." }: { children?: string }) => (
  <p className="text-sm text-text-faint">{children}</p>
);

/** Renders a stored report exactly as produced. Nothing is added or inferred here. */
export function ReportView({ report: r }: { report: IncidentReport }) {
  const a = r.analysis;
  const d = r.decision;
  const warn = r.status !== "complete";
  return (
    <article aria-label={`Report ${r.id}`} className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <ModeBadge mode={r.mode} />
        <span
          className={`rounded-chip border px-2 py-0.5 font-mono text-[11px] ${
            warn ? "border-warn/50 text-warn" : "border-ok/50 text-ok"
          }`}
        >
          {warn ? "▲" : "✓"} {STATUS_LABEL[r.status]}
        </span>
        <span className="rounded-chip border border-violet/50 px-2 py-0.5 font-mono text-[11px] text-violet">
          AI-GENERATED · {r.generation.model_id}
        </span>
      </div>
      <p role="note" className="rounded-card border border-border p-3 text-xs text-text-dim">
        {r.advisory_notice}
      </p>

      <Section title="Summary" tone="text-violet">
        <p className="text-sm">{a.summary}</p>
        <p className="mt-2 text-xs text-text-faint">
          Generated {new Date(r.created_at).toLocaleString()} · {r.generation.region} ·{" "}
          {Math.round(r.generation.latency_ms)} ms
        </p>
      </Section>

      <Section title="Decider 2B decision" tone="text-indigo">
        {d ? (
          <div className="space-y-2 text-sm">
            <p>
              Selected <span className="font-mono text-indigo">{d.selected}</span> ·{" "}
              {d.outcome.replace("_", " ")}
            </p>
            <ConfidenceMeter value={d.confidence} threshold={d.confidence_threshold} />
            <p className="text-xs text-text-faint">
              Model {d.model ?? "not reported"} · server latency{" "}
              {d.latency_ms === null ? "not reported" : `${d.latency_ms.toFixed(1)} ms`} · round trip{" "}
              {d.roundtrip_ms.toFixed(1)} ms
            </p>
            <p className="text-xs text-text-faint">
              The selected diagnostic is recorded. Real AWS tool execution arrives in Phase 4; this
              analysis used the simulation evidence below.
            </p>
          </div>
        ) : (
          <None>Run without Decider 2B. No decision was made.</None>
        )}
      </Section>

      <Section title="Confirmed facts">
        {a.confirmed_facts.length ? (
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {a.confirmed_facts.map((f, i) => (
              <li key={i}>
                {f.statement}
                <Ids ids={f.evidence_ids} />
              </li>
            ))}
          </ul>
        ) : (
          <None>No statement passed the evidence check.</None>
        )}
      </Section>

      <Section title="Hypotheses (not confirmed)">
        {a.hypotheses.length ? (
          <ul className="space-y-2 text-sm">
            {a.hypotheses.map((h, i) => (
              <li key={i}>
                <span className="mr-2 rounded-chip border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase text-text-dim">
                  {h.plausibility}
                </span>
                {h.statement}
                <Ids ids={h.evidence_ids} />
                <p className="mt-0.5 text-xs text-text-dim">To confirm: {h.what_would_confirm}</p>
              </li>
            ))}
          </ul>
        ) : (
          <None />
        )}
      </Section>

      <Section title="Probable root causes">
        {a.probable_root_causes.length ? (
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {a.probable_root_causes.map((c, i) => (
              <li key={i}>
                <span className="font-mono text-[11px] uppercase text-text-dim">({c.basis})</span>{" "}
                {c.description}
                <Ids ids={c.evidence_ids} />
              </li>
            ))}
          </ul>
        ) : (
          <None />
        )}
      </Section>

      <Section title="Recommended actions (advisory)">
        {a.recommended_actions.length ? (
          <ol className="list-decimal space-y-2 pl-5 text-sm">
            {a.recommended_actions.map((x, i) => (
              <li key={i}>
                <span
                  className={`mr-2 rounded-chip border px-1.5 py-0.5 font-mono text-[10px] uppercase ${
                    x.kind === "read_only_check" ? "border-ok/50 text-ok" : "border-warn/50 text-warn"
                  }`}
                >
                  {x.kind === "read_only_check" ? "read-only check" : "human-executed change"} · risk {x.risk}
                </span>
                {x.description}
                <Ids ids={x.evidence_ids} />
                <p className="mt-0.5 text-xs text-text-dim">{x.rationale}</p>
              </li>
            ))}
          </ol>
        ) : (
          <None />
        )}
      </Section>

      <Section title="Impact and evidence gaps">
        <p className="text-sm">{a.impact_assessment}</p>
        {a.evidence_gaps.length > 0 && (
          <ul className="mt-2 list-disc pl-5 text-sm text-text-dim">
            {a.evidence_gaps.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Evidence the analysis could cite">
        <ul className="space-y-1 text-sm">
          {r.evidence.items.map((e) => (
            <li key={e.id}>
              <span className="mr-2 font-mono text-xs text-cyan">{e.id}</span>
              <span className="mr-2 font-mono text-[11px] text-text-faint">{e.source}</span>
              {e.text}
            </li>
          ))}
        </ul>
        {r.mode === "simulation" && (
          <p className="mt-2 text-xs text-text-faint">Simulation data bundled with the project.</p>
        )}
      </Section>

      <Section title="Grounding check">
        <p className="text-sm text-text-dim">
          Facts kept {r.grounding.facts_kept}, demoted to hypotheses {r.grounding.facts_demoted};
          root causes downgraded {r.grounding.root_causes_demoted}; unknown evidence ids removed{" "}
          {r.grounding.evidence_ids_removed}.
        </p>
        {r.grounding.warnings.length > 0 && (
          <ul className="mt-2 list-disc pl-5 text-xs text-warn">
            {r.grounding.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        )}
      </Section>
    </article>
  );
}
