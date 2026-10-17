"use client";

import { useRef } from "react";
import { MM_FULL, gsap, useGSAP } from "./motion";

/**
 * Staggered reveal of every `[data-reveal]` descendant. Re-runs when `deps` change
 * (e.g. after async data lands). No-op under prefers-reduced-motion.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(deps: unknown[] = []) {
  const ref = useRef<T>(null);
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MM_FULL, () => {
        gsap.from("[data-reveal]", {
          autoAlpha: 0,
          y: 18,
          duration: 0.6,
          stagger: 0.07,
          ease: "power3.out",
          clearProps: "transform,opacity,visibility",
        });
      });
    },
    { scope: ref, dependencies: deps, revertOnUpdate: true },
  );
  return ref;
}
