"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { DecisionResult } from "@/lib/types";
import {
  AvailabilityPill,
  ErrorBanner,
  Loading,
  ModeBadge,
  PageHeader,
  Panel,
  SeverityPill,
  UnavailableBanner,
} from "@/components/ui";

type RunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "unavailable"; reason: string }
  | { status: "error"; error: string }
  | { status: "done"; result: DecisionResult };

export default function DecisionLab() {
  const params = useSearchParams();
  const incidents = useApi(api.incidents);
  const decider = useApi(api.decisionStatus);
  const [picked, setPicked] = useState<string | null>(params.get("incident"));
  const [run, setRun] = useState<RunState>({ status: "idle" });

  const list = incidents.status === "ready" ? incidents.data.incidents : [];
  const selectedId = picked ?? list[0]?.id ?? null;
  const selected = list.find((i) => i.id === selectedId) ?? null;

  async function trigger() {
    if (!selectedId) return;
    setRun({ status: "running" });
    const r = await api.runDecision(selectedId);
    if (r.ok) setRun({ status: "done", result: r.data });
    else if (r.status === 503) setRun({ status: "unavailable", reason: r.error });
    else setRun({ status: "error", error: r.error });
  }

  return (
    <>
      <PageHeader
        title="Decision Lab"
        description="Pick an incident, then ask Strands Decider 2B which diagnostic tool to run next. Only real model output is shown."
        right={incidents.status === "ready" ? <ModeBadge mode={incidents.data.mode} /> : undefined}
      />
      <div className="grid gap-6 lg:grid-cols-12">
        <Panel title="1 · Select incident" className="lg:col-span-5">
          {incidents.status === "loading" && <Loading />}
          {incidents.status === "error" && <ErrorBanner error={incidents.error} />}
          {incidents.status === "ready" && list.length === 0 && (
            <p className="text-text-dim">{incidents.data.notice ?? "No incidents available."}</p>
          )}
          {list.length > 0 && (
            <fieldset>
              <legend className="sr-only">Incident</legend>
              <ul className="space-y-2">
                {list.map((i) => (
                  <li key={i.id}>
                    <label
                      className={`flex min-h-11 cursor-pointer items-start gap-3 rounded-card border p-3 ${
                        i.id === selectedId ? "border-cyan/60 bg-cyan/5" : "border-border hover:bg-surface-2"
                      }`}
                    >
                      <input
                        type="radio"
                        name="incident"
                        className="mt-1 accent-cyan"
                        checked={i.id === selectedId}
                        onChange={() => {
                          setPicked(i.id);
                          setRun({ status: "idle" });
                        }}
                      />
                      <span className="min-w-0">
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{i.title}</span>
                          <SeverityPill severity={i.severity} />
                        </span>
                        <span className="mt-1 block text-sm text-text-dim">{i.summary}</span>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </fieldset>
          )}
        </Panel>

        <div className="space-y-6 lg:col-span-7">
          <Panel
            title="2 · Decider 2B"
            meta={decider.status === "ready" ? <AvailabilityPill available={decider.data.available} /> : undefined}
          >
            {decider.status === "loading" && <Loading />}
            {decider.status === "error" && <ErrorBanner error={decider.error} />}
            {decider.status === "ready" && (
              <div className="space-y-4">
                {!decider.data.available && (
                  <UnavailableBanner
                    title="Decider 2B is unavailable"
                    reason={decider.data.reason ?? "No reason reported."}
                  />
                )}
                <div>
                  <p className="text-sm text-text-dim">Typed option set</p>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {decider.data.options.map((o) => (
                      <li
                        key={o}
                        className="rounded-chip border border-border px-2 py-1 font-mono text-xs text-text-dim"
                      >
                        {o}
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="text-sm text-text-dim tabular">
                  Escalation threshold:{" "}
                  <span className="font-mono text-text">{decider.data.confidence_threshold.toFixed(2)}</span>
                </p>
                <button
                  type="button"
                  onClick={trigger}
                  disabled={!selected || run.status === "running"}
                  className="inline-flex min-h-11 items-center rounded-btn bg-cyan px-5 font-semibold text-[#031018] transition-transform active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {run.status === "running" ? "Running…" : "Run Decider 2B inference"}
                </button>
              </div>
            )}
          </Panel>

          <Panel title="3 · Result">
            <div aria-live="polite">
              {run.status === "idle" && (
                <p className="text-text-dim">Select an incident and run inference to see the decision.</p>
              )}
              {run.status === "running" && <Loading label="Waiting for the model…" />}
              {run.status === "unavailable" && (
                <UnavailableBanner title="No decision was produced" reason={run.reason} />
              )}
              {run.status === "error" && <ErrorBanner error={run.error} />}
              {run.status === "done" && <ResultView result={run.result} />}
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}

function ResultView({ result }: { result: DecisionResult }) {
  return (
    <dl className="grid gap-3 text-sm sm:grid-cols-2">
      <Row label="Question" value={result.question} wide />
      <Row label="Selected option" value={result.selected ?? "—"} mono />
      <Row
        label="Confidence"
        value={result.confidence === null ? "— (not reported)" : result.confidence.toFixed(3)}
        mono
      />
      <Row
        label="Latency"
        value={result.latency_ms === null ? "— (not measured)" : `${result.latency_ms.toFixed(1)} ms`}
        mono
      />
      <Row label="Outcome" value={result.outcome} mono />
      <Row label="Tool invoked" value={result.tool_invoked ?? "—"} mono />
    </dl>
  );
}

function Row({
  label,
  value,
  mono,
  wide,
}: {
  label: string;
  value: string;
  mono?: boolean;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <dt className="text-text-faint">{label}</dt>
      <dd className={mono ? "font-mono" : undefined}>{value}</dd>
    </div>
  );
}
