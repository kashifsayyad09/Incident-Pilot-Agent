import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "IncidentPilot AI — From Cloud Chaos to Clarity",
  description:
    "Read-only AWS incident investigation. Strands Decider 2B selects the next diagnostic tool; Amazon Bedrock explains the evidence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-btn focus:bg-cyan focus:px-4 focus:py-2 focus:text-[#031018]"
        >
          Skip to content
        </a>
        <NavBar />
        <main id="main" className="mx-auto max-w-[1440px] px-4 py-10 md:px-8">
          {children}
        </main>
        <footer className="border-t border-border py-6 text-center text-sm text-text-faint">
          IncidentPilot AI · AWS Strands Decider Agent Hackathon ·{" "}
          <a
            className="text-text-dim underline hover:text-cyan"
            href="https://github.com/kashifsayyad09/Incident-Pilot-Agent"
          >
            GitHub
          </a>
        </footer>
      </body>
    </html>
  );
}
