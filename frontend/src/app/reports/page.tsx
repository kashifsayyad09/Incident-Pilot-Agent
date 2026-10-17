"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ModeBadge, PageHeader, Panel } from "@/components/ui";

export default function Reports() {
  const health = useApi(api.health);
  const bedrock =
    health.status === "ready" ? health.data.components.find((c) => c.name === "bedrock_agent") : null;

  return (
    <>
      <PageHeader
        title="Reports"
        description="Structured incident reports with probable root causes, recommended actions and export options."
        right={health.status === "ready" ? <ModeBadge mode={health.data.mode} /> : undefined}
      />
      <Panel title="Investigation history">
        <p className="text-text-dim">No reports have been generated yet.</p>
        <p className="mt-2 text-sm text-text-faint">
          {bedrock && !bedrock.available
            ? (bedrock.detail ?? "The report generator is not available.")
            : "Run an investigation to create a report."}
        </p>
      </Panel>
    </>
  );
}
