import Link from "next/link";

const PIPELINE = [
  { step: "Incident", text: "Structured state: 5xx rate, target health, CPU, DB connections, alarms, logs.", tone: "text-cyan" },
  { step: "Decider 2B", text: "Picks the next diagnostic tool from a typed option set, with model confidence.", tone: "text-indigo" },
  { step: "Diagnostic tool", text: "Read-only CloudWatch, ALB, EC2 or RDS investigation.", tone: "text-cyan" },
  { step: "Bedrock analysis", text: "Separates confirmed facts from hypotheses and drafts advisory recovery steps.", tone: "text-violet" },
  { step: "Incident report", text: "Structured, labeled simulation or live, exportable.", tone: "text-cyan" },
];

export default function Landing() {
  return (
    <div className="space-y-24">
      <section className="pt-8 md:pt-16">
        <p className="font-mono text-xs uppercase tracking-widest text-cyan">
          AWS Strands Decider Agent Hackathon · Tool Selection
        </p>
        <h1 className="mt-4 text-5xl font-bold md:text-7xl">IncidentPilot AI</h1>
        <p className="mt-4 text-2xl text-text-dim md:text-3xl">From Cloud Chaos to Clarity.</p>
        <p className="mt-6 max-w-2xl text-text-dim">
          An incident-response agent for AWS. <strong className="text-indigo">Strands Decider 2B</strong>{" "}
          makes one meaningful decision: which diagnostic tool to run next.{" "}
          <strong className="text-violet">Amazon Bedrock</strong> then explains the evidence. Every
          recommendation is read-only and advisory.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex min-h-11 items-center rounded-btn bg-cyan px-5 font-semibold text-[#031018] transition-transform active:scale-[0.97]"
          >
            Launch Command Center
          </Link>
          <a
            href="https://github.com/kashifsayyad09/Incident-Pilot-Agent"
            className="inline-flex min-h-11 items-center rounded-btn border border-border px-5 text-text-dim hover:text-cyan"
          >
            View on GitHub
          </a>
        </div>
      </section>

      <section aria-labelledby="pipeline">
        <h2 id="pipeline" className="text-2xl font-semibold md:text-3xl">
          One pipeline, end to end
        </h2>
        <ol className="mt-6 grid gap-4 md:grid-cols-5">
          {PIPELINE.map((p, i) => (
            <li key={p.step} className="rounded-card border border-border bg-surface p-4">
              <span className="font-mono text-xs text-text-faint">0{i + 1}</span>
              <h3 className={`mt-1 text-lg font-semibold ${p.tone}`}>{p.step}</h3>
              <p className="mt-2 text-sm text-text-dim">{p.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="honesty" className="rounded-hero border border-border bg-surface p-6 md:p-8">
        <h2 id="honesty" className="text-2xl font-semibold">Honest by design</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-text-dim">
          <li>Decider confidence is shown exactly as the model returns it, or not at all.</li>
          <li>If Decider 2B is unavailable, the app says so. It never substitutes a fake decision.</li>
          <li>Simulation and live AWS data are always labeled.</li>
          <li>No automatic restarts, scaling, or deletes. Recommendations are advisory.</li>
        </ul>
      </section>
    </div>
  );
}
