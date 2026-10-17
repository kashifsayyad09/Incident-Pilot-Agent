"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useReveal } from "@/lib/useReveal";
import { ModeBadge, PageHeader, Panel } from "@/components/ui";

export default function Reports() {
  const health = useApi(api.health);
  const bedrock =
    health.status === "ready" ? health.data.components.find((c) => c.name === "bedrock_agent") : null;
  const ref = useReveal<HTMLDivElement>([health.status]);

  return (
    <div ref={ref}>
      <PageHeader
        title="Reports"
        description="Structured incident reports: probable root causes, confirmed facts versus hypotheses, and advisory recovery steps."
        right={health.status === "ready" ? <ModeBadge mode={health.data.mode} /> : undefined}
      />
      <div className="grid gap-6 lg:grid-cols-12">
        <Panel title="Investigation history" className="lg:col-span-8">
          <p className="text-text-dim">No reports have been generated yet.</p>
          <p className="mt-2 text-sm text-text-faint">
            {bedrock && !bedrock.available
              ? (bedrock.detail ?? "The report generator is not available.")
              : "Run an investigation to create a report."}
          </p>
        </Panel>
        <Panel title="What a report contains" className="lg:col-span-4">
          <ul className="list-disc space-y-2 pl-5 text-sm text-text-dim">
            <li>Decider 2B decision trail with confidence and latency</li>
            <li>Evidence from the diagnostic tool</li>
            <li>Probable root causes, facts separated from hypotheses</li>
            <li>Advisory recovery steps and risk</li>
            <li>Simulation or Live AWS label</li>
          </ul>
          <p className="mt-4 text-xs text-text-faint">Export becomes available once reports exist.</p>
        </Panel>
      </div>
    </div>
  );
}
