"use client";

import { useEffect, useSyncExternalStore } from "react";
import type { IncidentSummary, ServiceKind, Severity } from "./types";

/** "none" = the selected scenario does not flag this service. It is NOT a health claim. */
export type Level = "none" | Severity;
export type SceneState = Record<ServiceKind, Level>;

const NONE: SceneState = { alb: "none", ec2: "none", rds: "none", cloudwatch: "none" };

interface State {
  selected: IncidentSummary | null;
  scene: SceneState;
}

let state: State = { selected: null, scene: NONE };
const listeners = new Set<() => void>();

export function selectIncident(incident: IncidentSummary | null) {
  if (state.selected?.id === incident?.id) return;
  const scene: SceneState = { ...NONE };
  if (incident) for (const s of incident.affected_services) scene[s] = incident.severity;
  state = { selected: incident, scene };
  listeners.forEach((l) => l());
}

function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}
const getState = () => state;
const getServerState = () => state;

export function useIncidentState(): State {
  return useSyncExternalStore(subscribe, getState, getServerState);
}

/** Select the first incident when nothing is selected yet. */
export function useDefaultSelection(list: IncidentSummary[]) {
  const { selected } = useIncidentState();
  useEffect(() => {
    if (!selected && list.length > 0) selectIncident(list[0]);
  }, [selected, list]);
}

/** Non-React read access, for tests. */
export const getIncidentState = (): State => state;
