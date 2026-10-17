"use client";

import Link from "next/link";
import { useMemo, useRef } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { MM_FULL, gsap, useGSAP } from "@/lib/motion";
import { useDefaultSelection, useIncidentState } from "@/lib/incidentStore";
import { useReveal } from "@/lib/useReveal";
import {
  AvailabilityPill,
  ErrorBanner,
  Loading,
  ModeBadge,
  PageHeader,
  Panel,
  SeverityPill,
} from "@/components/ui";

const STEPS = [
  { key: "state", label: "Input state", note: "Evidence snapshot for the incident.", component: "aws_diagnostics", tone: "text-cyan", border: "border-cyan/40" },
  { key: "decision", label: "Decider 2B selection", note: "Typed question, options, selected option, confidence and latency.", component: "decider_2b", tone: "text-indigo", border: "border-indigo/50" },
  { key: "tool", label: "Diagnostic tool", note: "Read-only CloudWatch, ALB, EC2 or RDS call.", component: "aws_diagnostics", tone: "text-cyan", border: "border-cyan/40" },
  { key: "analysis", label: "Bedrock analysis", note: "Confirmed facts vs hypotheses and advisory recovery steps.", component: "bedrock_agent", tone: "text-violet", border: "border-violet/50" },
] as const;

export default function Investigation() {
  const health = useApi(api.health);
  const decider = useApi(api.decisionStatus);
  const incidents = useApi(api.incidents);
  const list = useMemo(
    () => (incidents.status === "ready" ? incidents.data.incidents : []),
    [incidents],
  );
  useDefaultSelection(list);
  const { selected } = useIncidentState();
  const page = useReveal<HTMLDivElement>([health.status, incidents.status]);
  const line = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (health.status !== "ready") return;
      const mm = gsap.matchMedia();
      mm.add(MM_FULL, () => {
        gsap.from(line.current, { scaleY: 0, transformOrigin: "top", duration: 0.9, ease: "power2.inOut" });
        gsap.from("[data-step]", { autoAlpha: 0, x: -16, stagger: 0.18, duration: 0.5, ease: "power3.out" });
      });
    },
    { dependencies: [health.status], scope: page, revertOnUpdate: true },
  );

  return (
    <div ref={page}>
      <PageHeader
        title="Incident Investigation"
        description="The path from incident to analysis. Each stage shows whether its component is available. No stage displays output that was not produced."
        right={selected ? <ModeBadge mode={selected.mode} /> : undefined}
      />

      <div className="grid gap-6 lg:grid-cols-12">
        <Panel title="Incident summary" className="lg:col-span-4">
          {incidents.status === "loading" && <Loading />}
          {incidents.status === "error" && <ErrorBanner error={incidents.error} />}
          {incidents.status === "ready" && !selected && (
            <p className="text-text-dim">{incidents.data.notice ?? "No incident available."}</p>
          )}
          {selected && (
            <div className="space-y-3">
              <SeverityPill severity={selected.severity} />
              <p className="font-heading text-xl font-semibold">{selected.title}</p>
              <p className="text-sm text-text-dim">{selected.summary}</p>
              <p className="font-mono text-xs text-text-faint">
                {selected.id} · {selected.affected_services.join(", ")}
              </p>
              <p className="text-sm text-text-dim">
                Change the incident on the{" "}
                <Link className="text-cyan underline" href="/dashboard">
                  dashboard
                </Link>
                .
              </p>
            </div>
          )}
          <p className="mt-4 border-t border-border pt-4 text-xs text-text-faint">
            Metrics and logs for this incident appear here once AWS diagnostics are implemented.
          </p>
        </Panel>

        <Panel title="Decision timeline" className="lg:col-span-8">
          {health.status === "loading" && <Loading />}
          {health.status === "error" && <ErrorBanner error={health.error} />}
          {health.status === "ready" && (
            <div className="relative pl-8">
              <div
                ref={line}
                aria-hidden
                className="absolute bottom-3 left-[11px] top-3 w-px bg-gradient-to-b from-cyan via-indigo to-violet"
              />
              <ol className="space-y-4">
                {STEPS.map((s, i) => {
                  const comp = health.data.components.find((c) => c.name === s.component);
                  const available = comp?.available ?? false;
                  return (
                    <li key={s.key} data-step className="relative">
                      <span
                        aria-hidden
                        className={`absolute -left-8 top-4 flex h-6 w-6 items-center justify-center rounded-full border bg-bg font-mono text-[10px] ${s.border} ${s.tone}`}
                      >
                        {i + 1}
                      </span>
                      <div className={`rounded-card border bg-surface-2/60 p-4 ${s.border}`}>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <h3 className={`font-semibold ${s.tone}`}>{s.label}</h3>
                          <AvailabilityPill available={available} />
                        </div>
                        <p className="mt-1 text-sm text-text-dim">
                          {available ? s.note : (comp?.detail ?? s.note)}
                        </p>
                        {s.key === "decision" && decider.status === "ready" && (
                          <div className="mt-3">
                            <p className="text-xs text-text-faint">
                              Option set · escalation threshold{" "}
                              <span className="font-mono text-text-dim">
                                {decider.data.confidence_threshold.toFixed(2)}
                              </span>
                            </p>
                            <ul className="mt-2 flex flex-wrap gap-2">
                              {decider.data.options.map((o) => (
                                <li
                                  key={o}
                                  className="rounded-chip border border-border px-2 py-1 font-mono text-[11px] text-text-dim"
                                >
                                  {o}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
          <p className="mt-6 text-sm text-text-dim">
            Try the decision step directly in the{" "}
            <Link className="text-cyan underline" href="/decision-lab">
              Decision Lab
            </Link>
            .
          </p>
        </Panel>
      </div>
    </div>
  );
}
