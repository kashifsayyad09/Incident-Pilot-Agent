"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import {
  AvailabilityPill,
  ErrorBanner,
  Loading,
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

export default function Dashboard() {
  const health = useApi(api.health);
  const incidents = useApi(api.incidents);

  return (
    <>
      <PageHeader
        title="Operations Dashboard"
        description="System readiness and the incident catalogue. Metrics and resource health appear once diagnostics are implemented."
        right={health.status === "ready" ? <ModeBadge mode={health.data.mode} /> : undefined}
      />
      <div className="grid gap-6 lg:grid-cols-12">
        <Panel title="Component status" className="lg:col-span-5">
          {health.status === "loading" && <Loading />}
          {health.status === "error" && <ErrorBanner error={health.error} />}
          {health.status === "ready" && (
            <ul className="space-y-3">
              {health.data.components.map((c) => (
                <li key={c.name} className="flex flex-col gap-1 border-b border-border pb-3 last:border-0">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium">{COMPONENT_LABELS[c.name] ?? c.name}</span>
                    <AvailabilityPill available={c.available} />
                  </div>
                  {c.detail && <span className="text-sm text-text-dim">{c.detail}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title="Incidents"
          className="lg:col-span-7"
          meta={incidents.status === "ready" ? <ModeBadge mode={incidents.data.mode} /> : undefined}
        >
          {incidents.status === "loading" && <Loading />}
          {incidents.status === "error" && <ErrorBanner error={incidents.error} />}
          {incidents.status === "ready" && (
            <>
              {incidents.data.notice && (
                <p className="mb-3 text-sm text-text-dim">{incidents.data.notice}</p>
              )}
              {incidents.data.incidents.length === 0 ? (
                <p className="text-text-dim">No incidents available.</p>
              ) : (
                <ul className="space-y-3">
                  {incidents.data.incidents.map((i) => (
                    <li
                      key={i.id}
                      className="flex flex-wrap items-start justify-between gap-3 rounded-card border border-border bg-surface-2 p-4"
                    >
                      <div className="min-w-0">
                        <p className="font-semibold">{i.title}</p>
                        <p className="mt-1 text-sm text-text-dim">{i.summary}</p>
                        <p className="mt-2 font-mono text-xs text-text-faint">
                          {i.id} · {i.affected_services.join(", ")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <SeverityPill severity={i.severity} />
                        <Link
                          href={`/decision-lab?incident=${encodeURIComponent(i.id)}`}
                          className="inline-flex min-h-11 items-center rounded-btn border border-border px-3 text-sm text-cyan hover:bg-cyan/10"
                        >
                          Open in Decision Lab
                        </Link>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </Panel>
      </div>
    </>
  );
}
