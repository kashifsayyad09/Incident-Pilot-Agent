import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";
import SceneBackground from "@/components/SceneBackground";
import Shell from "@/components/Shell";

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
        <SceneBackground />
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
