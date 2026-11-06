"use client";

import { useEffect, useSyncExternalStore } from "react";
import type { IncidentSummary, ServiceKind, Severity, ToolOption } from "./types";

/** "none" = the selected scenario does not flag this service. It is NOT a health claim. */
export type Level = "none" | Severity;
export type SceneState = Record<ServiceKind, Level>;

const NONE: SceneState = { alb: "none", ec2: "none", rds: "none", cloudwatch: "none" };

/** Service whose diagnostic Decider 2B pointed at. Display only; it is not a health claim. */
export const TOOL_SERVICE: Partial<Record<ToolOption, ServiceKind>> = {
  investigate_load_balancer: "alb",
  investigate_ec2: "ec2",
  investigate_database: "rds",
  investigate_cloudwatch_logs: "cloudwatch",
};

interface State {
  selected: IncidentSummary | null;
  scene: SceneState;
  focus: ServiceKind | null;
}

let state: State = { selected: null, scene: NONE, focus: null };
const listeners = new Set<() => void>();

export function selectIncident(incident: IncidentSummary | null) {
  if (state.selected?.id === incident?.id) return;
  const scene: SceneState = { ...NONE };
  if (incident) for (const s of incident.affected_services) scene[s] = incident.severity;
  state = { selected: incident, scene, focus: null };
  listeners.forEach((l) => l());
}

export function setFocus(tool: ToolOption | null) {
  const focus = tool ? (TOOL_SERVICE[tool] ?? null) : null;
  if (state.focus === focus) return;
  state = { ...state, focus };
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
