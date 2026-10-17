import type { ReactNode } from "react";
import type { Mode, Severity } from "@/lib/types";

export function Panel({
  title,
  meta,
  children,
  className = "",
}: {
  title?: string;
  meta?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-card border border-border bg-surface p-5 ${className}`}>
      {(title || meta) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
          {meta}
        </header>
      )}
      {children}
    </section>
  );
}

export function ModeBadge({ mode }: { mode: Mode }) {
  const live = mode === "live";
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[11px] uppercase tracking-wider ${
        live ? "border-ok/50 text-ok" : "border-warn/50 text-warn"
      }`}
      aria-label={live ? "Mode: live AWS" : "Mode: simulation"}
    >
      <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${live ? "bg-ok" : "bg-warn"}`} />
      {live ? "Live AWS" : "Simulation"}
    </span>
  );
}

const SEVERITY_STYLE: Record<Severity, { cls: string; glyph: string; label: string }> = {
  info: { cls: "border-cyan/40 text-cyan", glyph: "ℹ", label: "INFO" },
  warning: { cls: "border-warn/50 text-warn", glyph: "▲", label: "WARNING" },
  critical: { cls: "border-crit/50 text-crit", glyph: "✖", label: "CRITICAL" },
};

export function SeverityPill({ severity }: { severity: Severity }) {
  const s = SEVERITY_STYLE[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-chip border px-2 py-0.5 font-mono text-[11px] ${s.cls}`}
    >
      <span aria-hidden>{s.glyph}</span>
      {s.label}
    </span>
  );
}

export function AvailabilityPill({ available }: { available: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-chip border px-2 py-0.5 font-mono text-[11px] ${
        available ? "border-ok/50 text-ok" : "border-warn/50 text-warn"
      }`}
    >
      <span aria-hidden>{available ? "●" : "○"}</span>
      {available ? "AVAILABLE" : "UNAVAILABLE"}
    </span>
  );
}

export function UnavailableBanner({ title, reason }: { title: string; reason: string }) {
  return (
    <div role="status" className="rounded-card border border-warn/50 bg-warn/10 p-4">
      <p className="font-semibold text-warn">{title}</p>
      <p className="mt-1 text-sm text-text-dim">{reason}</p>
    </div>
  );
}

export function ErrorBanner({ error }: { error: string }) {
  return (
    <div role="alert" className="rounded-card border border-crit/50 bg-crit/10 p-4">
      <p className="font-semibold text-crit">Request failed</p>
      <p className="mt-1 text-sm text-text-dim">{error}</p>
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <p className="text-sm text-text-dim" role="status">
      {label}
    </p>
  );
}

export function PageHeader({
  title,
  description,
  right,
}: {
  title: string;
  description: string;
  right?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold md:text-4xl">{title}</h1>
        <p className="mt-2 max-w-2xl text-text-dim">{description}</p>
      </div>
      {right}
    </div>
  );
}
