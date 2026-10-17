"use client";

import dynamic from "next/dynamic";
import { useState, useSyncExternalStore } from "react";

const Scene3D = dynamic(() => import("./Scene3D"), { ssr: false });

function detectWebGL(): boolean {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

let webglCache: boolean | null = null;
const webglSnapshot = () => (webglCache ??= detectWebGL());
const noSubscribe = () => () => {};

function useMedia(query: string): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(query);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia(query).matches,
    () => false,
  );
}

/** Fixed, decorative backdrop. Carries no information that isn't also present as text. */
export default function SceneBackground() {
  const webgl = useSyncExternalStore(noSubscribe, webglSnapshot, () => false);
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const mobile = useMedia("(max-width: 640px)");
  const [lost, setLost] = useState(false);

  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-bg">
      <div className="absolute inset-0 backdrop-grid" />
      {webgl && !lost && <Scene3D animate={!reduced} mobile={mobile} onContextLost={() => setLost(true)} />}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,#060b16_100%)]" />
    </div>
  );
}
