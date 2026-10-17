"use client";

import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { useIncidentState, type Level } from "@/lib/incidentStore";
import type { ServiceKind } from "@/lib/types";

const N = 40;
const PULSES = 40;
const NAMED: Record<ServiceKind, number> = { alb: 3, ec2: 12, rds: 24, cloudwatch: 33 };
const LEVEL_COLOR: Record<Level, string> = {
  none: "#00d8ff",
  info: "#00d8ff",
  warning: "#f59e0b",
  critical: "#ef4444",
};

function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildGraph() {
  const rng = mulberry32(7);
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const th = i * 2.399963;
    const s = 4.2 * (0.8 + rng() * 0.5);
    pos.set([Math.cos(th) * r * s, y * s, Math.sin(th) * r * s], i * 3);
  }
  const key = new Set<string>();
  const edges: [number, number][] = [];
  for (let i = 0; i < N; i++) {
    const d: [number, number][] = [];
    for (let j = 0; j < N; j++) {
      if (j === i) continue;
      const dx = pos[i * 3] - pos[j * 3];
      const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
      const dz = pos[i * 3 + 2] - pos[j * 3 + 2];
      d.push([dx * dx + dy * dy + dz * dz, j]);
    }
    d.sort((a, b) => a[0] - b[0]);
    for (const [, j] of d.slice(0, 2)) {
      const k = i < j ? `${i}-${j}` : `${j}-${i}`;
      if (!key.has(k)) {
        key.add(k);
        edges.push([i, j]);
      }
    }
  }
  const edgePositions = new Float32Array(edges.length * 6);
  edges.forEach(([a, b], i) => {
    edgePositions.set([pos[a * 3], pos[a * 3 + 1], pos[a * 3 + 2]], i * 6);
    edgePositions.set([pos[b * 3], pos[b * 3 + 1], pos[b * 3 + 2]], i * 6 + 3);
  });
  return { pos, edges, edgePositions };
}

type Graph3D = ReturnType<typeof buildGraph>;

interface PulseState {
  edge: Uint16Array;
  t: Float32Array;
  speed: Float32Array;
  pos: Float32Array;
}

function createPulses(edgeCount: number): PulseState {
  return {
    edge: Uint16Array.from({ length: PULSES }, (_, i) => (i * 7) % edgeCount),
    t: Float32Array.from({ length: PULSES }, (_, i) => (i * 0.137) % 1),
    speed: Float32Array.from({ length: PULSES }, (_, i) => 0.15 + ((i * 29) % 10) / 60),
    pos: new Float32Array(PULSES * 3),
  };
}

function stepPulses(p: PulseState, g: Graph3D, delta: number) {
  for (let i = 0; i < PULSES; i++) {
    p.t[i] += p.speed[i] * delta;
    if (p.t[i] > 1) {
      p.t[i] -= 1;
      p.edge[i] = (p.edge[i] + 13) % g.edges.length;
    }
    const [a, b] = g.edges[p.edge[i]];
    const t = p.t[i];
    for (let k = 0; k < 3; k++) {
      p.pos[i * 3 + k] = g.pos[a * 3 + k] * (1 - t) + g.pos[b * 3 + k] * t;
    }
  }
}

function Graph({ animate, particleCount }: { animate: boolean; particleCount: number }) {
  const { scene } = useIncidentState();
  const invalidate = useThree((s) => s.invalidate);
  const g = useMemo(() => buildGraph(), []);
  const group = useRef<THREE.Group>(null);
  const nodes = useRef<THREE.InstancedMesh>(null);
  const glow = useRef<THREE.InstancedMesh>(null);
  const pulsePoints = useRef<THREE.Points>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const tmpColor = useMemo(() => new THREE.Color(), []);

  const particles = useMemo(() => {
    const rng = mulberry32(21);
    const a = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = 6 + rng() * 6;
      const th = rng() * Math.PI * 2;
      const ph = Math.acos(2 * rng() - 1);
      a.set([r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph), r * Math.sin(ph) * Math.sin(th)], i * 3);
    }
    return a;
  }, [particleCount]);

  const [pulseData] = useState(() => {
    const p = createPulses(g.edges.length);
    stepPulses(p, g, 0);
    return p;
  });

  const refreshPulses = (delta: number) => {
    stepPulses(pulseData, g, delta);
    const attr = pulsePoints.current?.geometry.getAttribute("position");
    if (attr) attr.needsUpdate = true;
  };

  const flaggedKey = (Object.keys(NAMED) as ServiceKind[]).map((k) => scene[k]).join("|");

  useLayoutEffect(() => {
    const n = nodes.current;
    const gl = glow.current;
    if (!n || !gl) return;
    const named = new Map<number, ServiceKind>(
      (Object.entries(NAMED) as [ServiceKind, number][]).map(([k, i]) => [i, k]),
    );
    for (let i = 0; i < N; i++) {
      const svc = named.get(i);
      dummy.position.set(g.pos[i * 3], g.pos[i * 3 + 1], g.pos[i * 3 + 2]);
      dummy.scale.setScalar(svc ? 1.7 : 1);
      dummy.updateMatrix();
      n.setMatrixAt(i, dummy.matrix);
      if (svc) tmpColor.set(LEVEL_COLOR[scene[svc]]);
      else tmpColor.set("#00d8ff").multiplyScalar(0.4);
      n.setColorAt(i, tmpColor);
    }
    n.instanceMatrix.needsUpdate = true;
    if (n.instanceColor) n.instanceColor.needsUpdate = true;
    (Object.entries(NAMED) as [ServiceKind, number][]).forEach(([k, idx], j) => {
      const flagged = scene[k] !== "none";
      dummy.position.set(g.pos[idx * 3], g.pos[idx * 3 + 1], g.pos[idx * 3 + 2]);
      dummy.scale.setScalar(flagged ? 2.2 : 0.0001);
      dummy.updateMatrix();
      gl.setMatrixAt(j, dummy.matrix);
      gl.setColorAt(j, tmpColor.set(LEVEL_COLOR[scene[k]]));
    });
    gl.instanceMatrix.needsUpdate = true;
    if (gl.instanceColor) gl.instanceColor.needsUpdate = true;
    refreshPulses(0);
    invalidate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flaggedKey]);

  useFrame(({ camera, pointer, clock }, delta) => {
    if (!animate) return;
    const d = Math.min(delta, 0.05);
    if (group.current) group.current.rotation.y += d * 0.02;
    camera.position.x += (pointer.x * 0.8 - camera.position.x) * 0.03;
    camera.position.y += (pointer.y * 0.5 - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);
    refreshPulses(d);
    const gl = glow.current;
    if (gl) {
      const pulse = 1 + Math.sin(clock.elapsedTime * 3) * 0.12;
      (Object.entries(NAMED) as [ServiceKind, number][]).forEach(([k, idx], j) => {
        if (scene[k] === "none") return;
        dummy.position.set(g.pos[idx * 3], g.pos[idx * 3 + 1], g.pos[idx * 3 + 2]);
        dummy.scale.setScalar(2.2 * pulse);
        dummy.updateMatrix();
        gl.setMatrixAt(j, dummy.matrix);
      });
      gl.instanceMatrix.needsUpdate = true;
    }
  });

  return (
    <group ref={group}>
      <instancedMesh ref={nodes} args={[undefined, undefined, N]}>
        <sphereGeometry args={[0.085, 12, 12]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={glow} args={[undefined, undefined, 4]}>
        <sphereGeometry args={[0.2, 12, 12]} />
        <meshBasicMaterial
          transparent
          opacity={0.3}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          toneMapped={false}
        />
      </instancedMesh>
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[g.edgePositions, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color="#6366f1" transparent opacity={0.4} />
      </lineSegments>
      <points ref={pulsePoints}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[pulseData.pos, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#00d8ff"
          size={0.16}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[particles, 3]} />
        </bufferGeometry>
        <pointsMaterial color="#8b5cf6" size={0.045} transparent opacity={0.6} depthWrite={false} />
      </points>
    </group>
  );
}

export default function Scene3D({
  animate,
  mobile,
  onContextLost,
}: {
  animate: boolean;
  mobile: boolean;
  onContextLost: () => void;
}) {
  return (
    <Canvas
      dpr={[1, 1.5]}
      frameloop={animate ? "always" : "demand"}
      camera={{ position: [0, 0, 11], fov: 50 }}
      gl={{ antialias: !mobile, alpha: true, powerPreference: "high-performance" }}
      onCreated={({ gl }) => {
        gl.domElement.addEventListener("webglcontextlost", (e) => {
          e.preventDefault();
          onContextLost();
        });
      }}
    >
      <fog attach="fog" args={["#060b16", 9, 20]} />
      <Graph animate={animate} particleCount={mobile ? 350 : 800} />
    </Canvas>
  );
}
