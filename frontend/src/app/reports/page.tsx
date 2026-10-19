"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useReveal } from "@/lib/useReveal";
import { downloadText, reportToMarkdown } from "@/lib/reportExport";
import { ReportView } from "@/components/ReportView";
import { ErrorBanner, Loading, ModeBadge, PageHeader, Panel, UnavailableBanner } from "@/components/ui";

export default function Reports() {
  const health = useApi(api.health);
  const reports = useApi(api.reports);
  const [picked, setPicked] = useState<string | null>(null);
  const ref = useReveal<HTMLDivElement>([health.status, reports.status]);

  const list = reports.status === "ready" ? reports.data : [];
  const current = list.find((r) => r.id === picked) ?? list[0] ?? null;
  const bedrock =
    health.status === "ready" ? health.data.components.find((c) => c.name === "bedrock_agent") : null;

  return (
    <div ref={ref}>
      <PageHeader
        title="Reports"
        description="Stored incident reports: Decider 2B decision, confirmed facts versus hypotheses, and advisory recovery steps. Every report is AI-generated and labelled with its data mode."
        right={health.status === "ready" ? <ModeBadge mode={health.data.mode} /> : undefined}
      />
      <div className="grid gap-6 lg:grid-cols-12">
        <Panel title="Investigation history" className="lg:col-span-4">
          {reports.status === "loading" && <Loading />}
          {reports.status === "error" && <ErrorBanner error={reports.error} />}
          {reports.status === "ready" && list.length === 0 && (
            <div className="space-y-3">
              <p className="text-text-dim">No reports have been generated yet.</p>
              {bedrock && !bedrock.available && (
                <UnavailableBanner title="Report generator unavailable" reason={bedrock.detail ?? "Not configured."} />
              )}
              <Link className="text-cyan underline" href="/investigation">
                Run an investigation
              </Link>
            </div>
          )}
          {list.length > 0 && (
            <ul className="space-y-2">
              {list.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    onClick={() => setPicked(r.id)}
                    aria-current={current?.id === r.id}
                    className={`min-h-11 w-full rounded-card border p-3 text-left transition ${
                      current?.id === r.id ? "border-cyan/60 bg-surface-2" : "border-border hover:border-cyan/40"
                    }`}
                  >
                    <span className="block text-sm font-semibold">{r.incident.title}</span>
                    <span className="block font-mono text-[11px] text-text-faint">
                      {new Date(r.created_at).toLocaleString()} · {r.mode} · {r.status}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title={current ? "Report" : "What a report contains"}
          className="lg:col-span-8"
          meta={
            current ? (
              <div className="flex gap-2">
                <button
                  type="button"
                  className="min-h-11 rounded-btn border border-border px-3 text-sm hover:text-cyan"
                  onClick={() => downloadText(`${current.id}.json`, JSON.stringify(current, null, 2), "application/json")}
                >
                  Export JSON
                </button>
                <button
                  type="button"
                  className="min-h-11 rounded-btn border border-border px-3 text-sm hover:text-cyan"
                  onClick={() => downloadText(`${current.id}.md`, reportToMarkdown(current), "text/markdown")}
                >
                  Export Markdown
                </button>
              </div>
            ) : undefined
          }
        >
          {current ? (
            <ReportView report={current} />
          ) : (
            <ul className="list-disc space-y-2 pl-5 text-sm text-text-dim">
              <li>Decider 2B decision trail with confidence and latency</li>
              <li>Numbered evidence the analysis could cite</li>
              <li>Probable root causes, facts separated from hypotheses</li>
              <li>Advisory recovery steps and risk</li>
              <li>Simulation or Live AWS label</li>
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}
