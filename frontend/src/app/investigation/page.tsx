"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { AvailabilityPill, ErrorBanner, Loading, PageHeader, Panel } from "@/components/ui";

const STEPS = [
  { key: "state", label: "Input state", note: "Evidence snapshot for the incident (Phase 4)", component: "aws_diagnostics", tone: "text-cyan" },
  { key: "decision", label: "Decider 2B selection", note: "Typed question, options, confidence, latency (Phase 2)", component: "decider_2b", tone: "text-indigo" },
  { key: "tool", label: "Diagnostic tool", note: "Read-only CloudWatch, ALB, EC2 or RDS call (Phase 4)", component: "aws_diagnostics", tone: "text-cyan" },
  { key: "analysis", label: "Bedrock analysis", note: "Facts vs hypotheses, advisory steps (Phase 3)", component: "bedrock_agent", tone: "text-violet" },
] as const;

export default function Investigation() {
  const health = useApi(api.health);

  return (
    <>
      <PageHeader
        title="Incident Investigation"
        description="The decision timeline for one incident. Each stage lights up as its component becomes available. Nothing here is simulated output."
      />
      <Panel title="Decision timeline">
        {health.status === "loading" && <Loading />}
        {health.status === "error" && <ErrorBanner error={health.error} />}
        {health.status === "ready" && (
          <ol className="space-y-4">
            {STEPS.map((s, i) => {
              const comp = health.data.components.find((c) => c.name === s.component);
              const available = comp?.available ?? false;
              return (
                <li key={s.key} className="flex gap-4 rounded-card border border-border bg-surface-2 p-4">
                  <span className="font-mono text-sm text-text-faint">0{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className={`font-semibold ${s.tone}`}>{s.label}</h3>
                      <AvailabilityPill available={available} />
                    </div>
                    <p className="mt-1 text-sm text-text-dim">{available ? s.note : (comp?.detail ?? s.note)}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
        <p className="mt-6 text-sm text-text-dim">
          To try the decision step directly, use the{" "}
          <Link className="text-cyan underline" href="/decision-lab">
            Decision Lab
          </Link>
          .
        </p>
      </Panel>
    </>
  );
}
