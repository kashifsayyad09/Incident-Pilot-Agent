"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { MM_FULL, gsap, useGSAP } from "@/lib/motion";

const REPO = "https://github.com/kashifsayyad09/Incident-Pilot-Agent";

const STAGES = [
  {
    id: "incident",
    label: "Incident",
    tone: "text-cyan",
    title: "Structured incident state",
    body: "HTTP 5xx rate, load balancer health, EC2 CPU, RDS connections, CloudWatch alarms and relevant log lines are packaged into one typed state object.",
  },
  {
    id: "decider",
    label: "Decider 2B",
    tone: "text-indigo",
    title: "One meaningful decision",
    body: "Strands Decider 2B receives a typed question and picks the next diagnostic tool from five options. Its confidence is passed through unmodified. Below the threshold, the agent collects more evidence or asks a human.",
  },
  {
    id: "tool",
    label: "Diagnostic tool",
    tone: "text-cyan",
    title: "Read-only AWS diagnostics",
    body: "The chosen tool queries CloudWatch, ALB target health, EC2 or RDS using scoped read-only IAM permissions. Nothing is restarted, scaled or deleted.",
  },
  {
    id: "bedrock",
    label: "Bedrock",
    tone: "text-violet",
    title: "Grounded analysis",
    body: "Amazon Bedrock, through the Strands Agents SDK, separates confirmed facts from hypotheses and drafts advisory recovery steps from the evidence collected.",
  },
  {
    id: "report",
    label: "Report",
    tone: "text-cyan",
    title: "Structured incident report",
    body: "Root-cause hypotheses, impact, recommended actions and the full decision trail, clearly labeled Simulation or Live AWS.",
  },
] as const;

const OPTIONS = [
  "investigate_load_balancer",
  "investigate_ec2",
  "investigate_database",
  "investigate_cloudwatch_logs",
  "collect_more_evidence",
];

const FEATURES = [
  { t: "Typed tool selection", d: "A reusable decision pattern: state, typed question, option set, confidence gate." },
  { t: "Confidence-aware", d: "Low confidence never forces a guess. It escalates to more evidence or a human." },
  { t: "Read-only by design", d: "Scoped IAM policies. Recommendations are advisory and never auto-applied." },
  { t: "Simulation and Live", d: "Five realistic sample incidents, always labeled, strictly separated from live AWS." },
  { t: "Decision timeline", d: "Every step of the path from incident to report is inspectable." },
  { t: "No fabricated output", d: "If a component is unavailable, the UI says so instead of faking a result." },
];

export default function Landing() {
  const root = useRef<HTMLDivElement>(null);
  const [stage, setStage] = useState<(typeof STAGES)[number]["id"]>("decider");
  const current = STAGES.find((s) => s.id === stage) ?? STAGES[1];

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MM_FULL, () => {
        const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
        tl.from("[data-hero-eyebrow]", { autoAlpha: 0, y: 12, duration: 0.5 })
          .from("[data-hero-word]", { yPercent: 110, autoAlpha: 0, duration: 0.9, stagger: 0.12 }, "-=0.2")
          .from("[data-hero-sub]", { autoAlpha: 0, y: 16, duration: 0.6 }, "-=0.4")
          .from("[data-hero-copy]", { autoAlpha: 0, y: 16, duration: 0.6 }, "-=0.4")
          .from("[data-hero-cta]", { autoAlpha: 0, y: 12, duration: 0.5, stagger: 0.1 }, "-=0.3")
          .from("[data-hero-preview]", { autoAlpha: 0, y: 40, duration: 0.9 }, "-=0.5")
          .from("[data-preview-step]", { autoAlpha: 0, x: -12, duration: 0.45, stagger: 0.12 }, "-=0.4");

        gsap.utils.toArray<HTMLElement>("[data-scroll]").forEach((el) => {
          gsap.from(el.querySelectorAll("[data-item]"), {
            autoAlpha: 0,
            y: 28,
            duration: 0.7,
            stagger: 0.09,
            ease: "power3.out",
            scrollTrigger: { trigger: el, start: "top 82%", once: true },
          });
        });

        // Gentle float on three feature cards only (not everything, not forever on all).
        gsap.to("[data-float]", {
          y: -6,
          duration: 2.4,
          ease: "sine.inOut",
          yoyo: true,
          repeat: -1,
          stagger: 0.4,
        });

      });
    },
    { scope: root },
  );

  return (
    <div ref={root} className="mx-auto max-w-[1440px] space-y-28 px-4 pb-24 pt-32 md:px-8 md:pt-40">
      {/* HERO */}
      <section aria-labelledby="hero-title" className="grid items-center gap-12 lg:grid-cols-[1.15fr_1fr]">
        <div>
          <p data-hero-eyebrow className="font-mono text-xs uppercase tracking-widest text-cyan">
            AWS Strands Decider Agent Hackathon · Tool Selection
          </p>
          <h1
            id="hero-title"
            className="mt-5 text-[clamp(3rem,9vw,6rem)] font-bold leading-[1.02]"
            aria-label="IncidentPilot AI"
          >
            {["Incident", "Pilot", "AI"].map((w, i) => (
              <span key={w} className="mr-[0.25em] inline-block overflow-hidden align-bottom" aria-hidden>
                <span data-hero-word className={`inline-block ${i === 1 ? "text-cyan" : ""}`}>
                  {w}
                </span>
              </span>
            ))}
          </h1>
          <p data-hero-sub className="mt-4 font-heading text-2xl text-text-dim md:text-3xl">
            From Cloud Chaos to Clarity.
          </p>
          <p data-hero-copy className="mt-6 max-w-xl text-text-dim">
            An incident-response agent for AWS. <strong className="text-indigo">Strands Decider 2B</strong>{" "}
            decides which diagnostic tool to run next. <strong className="text-violet">Amazon Bedrock</strong>{" "}
            explains the evidence. Everything stays read-only and advisory.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              data-hero-cta
              href="/dashboard"
              className="glow-cyan inline-flex min-h-12 items-center rounded-btn bg-cyan px-6 font-semibold text-[#031018] transition-transform hover:-translate-y-0.5 active:scale-[0.97]"
            >
              Launch Command Center
            </Link>
            <a
              data-hero-cta
              href={REPO}
              className="inline-flex min-h-12 items-center rounded-btn border border-border px-6 text-text-dim transition-colors hover:border-cyan/50 hover:text-cyan"
            >
              View on GitHub
            </a>
          </div>
        </div>

        <aside
          data-hero-preview
          aria-label="Pipeline preview (layout only, no live data)"
          className="glass rounded-hero p-5"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-text-faint">
            Pipeline preview · layout only
          </p>
          <ol className="mt-4 space-y-3">
            {STAGES.map((s, i) => (
              <li
                key={s.id}
                data-preview-step
                className="flex items-center gap-3 rounded-card border border-border bg-surface-2/60 px-3 py-3"
              >
                <span className="font-mono text-xs text-text-faint">0{i + 1}</span>
                <span className={`font-medium ${s.tone}`}>{s.label}</span>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-xs text-text-faint">
            The live version of this path runs in the Decision Lab.
          </p>
        </aside>
      </section>

      {/* ARCHITECTURE */}
      <section aria-labelledby="arch" data-scroll>
        <h2 id="arch" data-item className="text-3xl font-semibold md:text-4xl">
          One pipeline, end to end
        </h2>
        <p data-item className="mt-3 max-w-2xl text-text-dim">
          Select a stage to see what happens there.
        </p>
        <div data-item className="mt-8 glass rounded-hero p-4 md:p-6">
          <div role="tablist" aria-label="Pipeline stages" className="flex flex-wrap gap-2">
            {STAGES.map((s) => (
              <button
                key={s.id}
                role="tab"
                id={`tab-${s.id}`}
                aria-selected={stage === s.id}
                aria-controls="stage-panel"
                onClick={() => setStage(s.id)}
                className={`min-h-11 rounded-btn border px-4 text-sm transition-colors ${
                  stage === s.id
                    ? "border-cyan/60 bg-cyan/10 text-cyan"
                    : "border-border text-text-dim hover:text-text"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <div id="stage-panel" role="tabpanel" aria-labelledby={`tab-${current.id}`} className="mt-6 min-h-36">
            <h3 className={`text-xl font-semibold ${current.tone}`}>{current.title}</h3>
            <p className="mt-2 max-w-3xl text-text-dim">{current.body}</p>
            {current.id === "decider" && (
              <ul className="mt-4 flex flex-wrap gap-2" aria-label="Decision options">
                {OPTIONS.map((o) => (
                  <li key={o} className="rounded-chip border border-indigo/40 px-2 py-1 font-mono text-xs text-text-dim">
                    {o}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section aria-labelledby="features" data-scroll>
        <h2 id="features" data-item className="text-3xl font-semibold md:text-4xl">
          Built to be trusted at 3 a.m.
        </h2>
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <li key={f.t} data-item>
              {/* Float lives on the inner wrapper so it never fights the li's reveal tween. */}
              <div
                {...(i < 3 ? { "data-float": true } : {})}
                className="glass h-full rounded-card p-5 transition-colors hover:border-cyan/40"
              >
                <h3 className="text-lg font-semibold">{f.t}</h3>
                <p className="mt-2 text-sm text-text-dim">{f.d}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* CTA */}
      <section data-scroll className="glass rounded-hero p-8 text-center md:p-14" aria-labelledby="cta">
        <h2 id="cta" data-item className="text-3xl font-semibold md:text-4xl">
          See the decision, not just the dashboard.
        </h2>
        <p data-item className="mx-auto mt-3 max-w-xl text-text-dim">
          Open the command center and walk an incident through the Decision Lab.
        </p>
        <div data-item className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href="/decision-lab"
            className="glow-cyan inline-flex min-h-12 items-center rounded-btn bg-cyan px-6 font-semibold text-[#031018] active:scale-[0.97]"
          >
            Open Decision Lab
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-12 items-center rounded-btn border border-border px-6 text-text-dim hover:text-cyan"
          >
            Operations Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}
