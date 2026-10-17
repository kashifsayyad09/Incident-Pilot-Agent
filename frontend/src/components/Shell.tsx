"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { MM_FULL, gsap, useGSAP } from "@/lib/motion";
import { ModeBadge } from "./ui";
import { NAV_ITEMS, isActive } from "./nav";

const REPO = "https://github.com/kashifsayyad09/Incident-Pilot-Agent";

function Logo() {
  return (
    <Link href="/" className="font-heading text-lg font-bold tracking-tight">
      Incident<span className="text-cyan">Pilot</span> AI
    </Link>
  );
}

function StatusCluster() {
  const health = useApi(api.health);
  return (
    <div className="flex items-center gap-3" aria-live="polite">
      {health.status === "ready" && <ModeBadge mode={health.data.mode} />}
      {health.status === "error" && (
        <span className="rounded-full border border-crit/50 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-crit">
          ✖ API offline
        </span>
      )}
    </div>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border py-6 text-center text-sm text-text-faint">
      IncidentPilot AI · AWS Strands Decider Agent Hackathon ·{" "}
      <a className="text-text-dim underline hover:text-cyan" href={REPO}>
        GitHub
      </a>
    </footer>
  );
}

function Sidebar({ pathname }: { pathname: string }) {
  const root = useRef<HTMLElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const indicator = useRef<HTMLSpanElement>(null);

  // Entrance: once per browser session.
  useGSAP(
    () => {
      let seen = false;
      try {
        seen = sessionStorage.getItem("ip-sidebar") === "1";
        sessionStorage.setItem("ip-sidebar", "1");
      } catch {
        /* storage unavailable */
      }
      if (seen) return;
      const mm = gsap.matchMedia();
      mm.add(MM_FULL, () => {
        gsap.from(root.current, { x: -24, autoAlpha: 0, duration: 0.6, ease: "power3.out" });
        gsap.from("[data-nav-item]", { x: -12, autoAlpha: 0, stagger: 0.06, delay: 0.2, duration: 0.4 });
      });
    },
    { scope: root },
  );

  // Animated active-state indicator.
  useGSAP(
    () => {
      // Measure the <li>: offsetParent of the <a> can be the transformed <li> during the entrance.
      const active = list.current
        ?.querySelector<HTMLElement>('[aria-current="page"]')
        ?.closest<HTMLElement>("li");
      const ind = indicator.current;
      if (!ind) return;
      if (!active) {
        gsap.set(ind, { autoAlpha: 0 });
        return;
      }
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      gsap.to(ind, {
        autoAlpha: 1,
        y: active.offsetTop,
        height: active.offsetHeight,
        duration: reduce ? 0 : 0.35,
        ease: "power2.inOut",
      });
    },
    { dependencies: [pathname], scope: root },
  );

  return (
    <aside
      ref={root}
      className="glass fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border md:flex"
    >
      <div className="px-5 py-5">
        <Logo />
      </div>
      <nav aria-label="Primary" className="flex-1 px-3">
        <ul ref={list} className="relative space-y-1">
          <span
            ref={indicator}
            aria-hidden
            className="pointer-events-none absolute left-0 top-0 w-full rounded-btn bg-cyan/10 opacity-0 ring-1 ring-cyan/30"
          />
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <li key={item.href} data-nav-item>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`relative flex min-h-11 items-center gap-3 rounded-btn px-3 text-sm transition-colors ${
                    active ? "text-cyan" : "text-text-dim hover:text-text"
                  }`}
                >
                  <span aria-hidden className="w-4 text-center">
                    {item.glyph}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="border-t border-border p-4 text-xs text-text-faint">
        <a className="hover:text-cyan" href={REPO}>
          github.com/kashifsayyad09
        </a>
        <p className="mt-1">Read-only · advisory</p>
      </div>
    </aside>
  );
}

function MobileTabs({ pathname }: { pathname: string }) {
  return (
    <nav
      aria-label="Primary"
      className="glass fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-border md:hidden"
    >
      {NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] ${
              active ? "text-cyan" : "text-text-dim"
            }`}
          >
            <span aria-hidden className="text-base leading-none">
              {item.glyph}
            </span>
            {item.label.split(" ")[0]}
          </Link>
        );
      })}
    </nav>
  );
}

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/") {
    return (
      <>
        <header className="absolute inset-x-0 top-0 z-20">
          <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-4 md:px-8">
            <Logo />
            <nav aria-label="Primary">
              <ul className="flex items-center gap-1">
                {NAV_ITEMS.slice(1).map((item) => (
                  <li key={item.href} className="hidden md:block">
                    <Link
                      href={item.href}
                      className="inline-flex min-h-11 items-center rounded-btn px-3 text-sm text-text-dim hover:text-text"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
                <li>
                  <Link
                    href="/dashboard"
                    className="inline-flex min-h-11 items-center rounded-btn border border-cyan/40 px-4 text-sm font-medium text-cyan hover:bg-cyan/10"
                  >
                    Launch
                  </Link>
                </li>
              </ul>
            </nav>
          </div>
        </header>
        <main id="main">{children}</main>
        <Footer />
      </>
    );
  }

  return (
    <div className="md:pl-60">
      <Sidebar pathname={pathname} />
      <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border bg-bg/70 px-4 py-3 backdrop-blur md:px-8">
        <div className="md:hidden">
          <Logo />
        </div>
        <span className="hidden font-mono text-xs uppercase tracking-widest text-text-faint md:block">
          Command Center
        </span>
        <StatusCluster />
      </header>
      <main id="main" className="mx-auto max-w-[1440px] px-4 py-8 pb-24 md:px-8 md:pb-10">
        {children}
      </main>
      <Footer />
      <MobileTabs pathname={pathname} />
    </div>
  );
}
