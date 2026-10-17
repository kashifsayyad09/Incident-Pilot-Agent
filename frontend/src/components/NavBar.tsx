"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ModeBadge } from "./ui";

export const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/investigation", label: "Investigation" },
  { href: "/decision-lab", label: "Decision Lab" },
  { href: "/reports", label: "Reports" },
] as const;

export default function NavBar() {
  const pathname = usePathname();
  const health = useApi(api.health);

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 md:px-8">
        <Link href="/" className="font-heading text-lg font-bold tracking-tight">
          Incident<span className="text-cyan">Pilot</span> AI
        </Link>
        <nav aria-label="Primary" className="order-3 w-full md:order-none md:w-auto">
          <ul className="flex flex-wrap gap-1">
            {NAV_ITEMS.map((item) => {
              const active =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`inline-flex min-h-11 items-center rounded-btn px-3 text-sm transition-colors ${
                      active ? "bg-cyan/10 text-cyan" : "text-text-dim hover:text-text"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-3" aria-live="polite">
          {health.status === "ready" && <ModeBadge mode={health.data.mode} />}
          {health.status === "error" && (
            <span className="rounded-full border border-crit/50 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-crit">
              API offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
