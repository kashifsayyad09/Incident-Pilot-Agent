"use client";

import Link from "next/link";
import { useMemo } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { selectIncident, useDefaultSelection, useIncidentState } from "@/lib/incidentStore";
import { useReveal } from "@/lib/useReveal";
import type { Level } from "@/lib/incidentStore";
import type { IncidentSummary, ServiceKind } from "@/lib/types";
import {
  AvailabilityPill,
  ErrorBanner,
  Loading,
  MetricCard,
  ModeBadge,
  PageHeader,
  Panel,
  SeverityPill,
} from "@/components/ui";

const COMPONENT_LABELS: Record<string, string> = {
  api: "Backend API",
  decider_2b: "Strands Decider 2B",
  bedrock_agent: "Bedrock agent",
  aws_diagnostics: "AWS diagnostics",
};

const SERVICES: { key: ServiceKind; label: string }[] = [
  { key: "alb", label: "Load balancer" },
  { key: "ec2", label: "EC2" },
  { key: "rds", label: "RDS" },
  { key: "cloudwatch", label: "CloudWatch" },
];

const LEVEL_UI: Record<Level, { text: string; cls: string; glyph: string }> = {
  none: { text: "Not flagged by this scenario", cls: "border-border text-text-dim", glyph: "○" },
  info: { text: "Info", cls: "border-cyan/40 text-cyan", glyph: "ℹ" },
  warning: { text: "Warning", cls: "border-warn/50 text-warn", glyph: "▲" },
  critical: { text: "Critical", cls: "border-crit/50 text-crit", glyph: "✖" },
};

export default function Dashboard() {
  const health = useApi(api.health);
  const incidents = useApi(api.incidents);
  const list = useMemo(
    () => (incidents.status === "ready" ? incidents.data.incidents : []),
    [incidents],
  );
  useDefaultSelection(list);
  const { selected, scene } = useIncidentState();
  const ref = useReveal<HTMLDivElement>([health.status, incidents.status]);

  return (
    <div ref={ref}>
      <PageHeader
        title="Operations Dashboard"
        description="Readiness, the selected incident, and where evidence will come from. Values that have not been measured are shown as “—”."
        right={health.status === "ready" ? <ModeBadge mode={health.data.mode} /> : undefined}
      />

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Status hero */}
        <Panel className="lg:col-span-12" title="Current incident">
          {incidents.status === "loading" && <Loading />}
          {incidents.status === "error" && <ErrorBanner error={incidents.error} />}
          {incidents.status === "ready" && !selected && (
            <p className="text-text-dim">{incidents.data.notice ?? "No incident selected."}</p>
          )}
          {selected && (
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 max-w-2xl">
                <div className="flex flex-wrap items-center gap-2">
                  <SeverityPill severity={selected.severity} />
                  <ModeBadge mode={selected.mode} />
                </div>
                <p className="mt-3 font-heading text-2xl font-semibold">{selected.title}</p>
                <p className="mt-1 text-text-dim">{selected.summary}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  href="/investigation"
                  className="inline-flex min-h-11 items-center rounded-btn border border-border px-4 text-sm hover:text-cyan"
                >
                  View timeline
                </Link>
                <Link
                  href="/decision-lab"
                  className="glow-cyan inline-flex min-h-11 items-center rounded-btn bg-cyan px-4 text-sm font-semibold text-[#031018] active:scale-[0.97]"
                >
                  Investigate in Decision Lab
                </Link>
              </div>
            </div>
          )}
        </Panel>

        {/* Resource health */}
        <Panel title="Resource health" className="lg:col-span-8">
          <ul className="grid gap-3 sm:grid-cols-2">
            {SERVICES.map((s) => {
              const ui = LEVEL_UI[scene[s.key]];
              return (
                <li key={s.key} data-reveal className="rounded-card border border-border bg-surface-2/70 p-4">
                  <p className="font-medium">{s.label}</p>
                  <span
                    className={`mt-2 inline-flex items-center gap-1.5 rounded-chip border px-2 py-0.5 font-mono text-[11px] ${ui.cls}`}
                  >
                    <span aria-hidden>{ui.glyph}</span>
                    {ui.text}
                  </span>
                </li>
              );
            })}
          </ul>
          <p className="mt-4 text-xs text-text-faint">
            Flags come from the selected simulation scenario&rsquo;s metadata. Live resource health arrives with
            the AWS diagnostics.
          </p>
        </Panel>

        {/* Metrics */}
        <Panel title="Key metrics" className="lg:col-span-4">
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="HTTP 5xx" value="—" caption="No evidence source yet" />
            <MetricCard label="EC2 CPU" value="—" caption="No evidence source yet" />
            <MetricCard label="DB connections" value="—" caption="No evidence source yet" />
            <MetricCard label="Memory" value="—" caption="Needs instrumentation" />
          </div>
        </Panel>

        {/* Recent incidents */}
        <Panel
          title="Incidents"
          className="lg:col-span-7"
          meta={incidents.status === "ready" ? <ModeBadge mode={incidents.data.mode} /> : undefined}
        >
          {incidents.status === "loading" && <Loading />}
          {incidents.status === "error" && <ErrorBanner error={incidents.error} />}
          {incidents.status === "ready" && list.length === 0 && (
            <p className="text-text-dim">{incidents.data.notice ?? "No incidents available."}</p>
          )}
          {list.length > 0 && <IncidentList list={list} selectedId={selected?.id ?? null} />}
        </Panel>

        {/* Agent activity */}
        <Panel title="Agent readiness" className="lg:col-span-5">
          {health.status === "loading" && <Loading />}
          {health.status === "error" && <ErrorBanner error={health.error} />}
          {health.status === "ready" && (
            <ul className="space-y-3">
              {health.data.components.map((c) => (
                <li key={c.name} className="border-b border-border pb-3 last:border-0">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium">{COMPONENT_LABELS[c.name] ?? c.name}</span>
                    <AvailabilityPill available={c.available} />
                  </div>
                  {c.detail && <p className="mt-1 text-sm text-text-dim">{c.detail}</p>}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}

function IncidentList({ list, selectedId }: { list: IncidentSummary[]; selectedId: string | null }) {
  return (
    <ul className="space-y-3">
      {list.map((i) => {
        const active = i.id === selectedId;
        return (
          <li key={i.id}>
            <button
              type="button"
              aria-pressed={active}
              onClick={() => selectIncident(i)}
              className={`w-full rounded-card border p-4 text-left transition-colors ${
                active ? "border-cyan/60 bg-cyan/5" : "border-border bg-surface-2/60 hover:border-cyan/30"
              }`}
            >
              <span className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold">{i.title}</span>
                <SeverityPill severity={i.severity} />
              </span>
              <span className="mt-1 block text-sm text-text-dim">{i.summary}</span>
              <span className="mt-2 block font-mono text-xs text-text-faint">
                {i.id} · {i.affected_services.join(", ")}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
