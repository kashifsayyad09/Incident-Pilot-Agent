import type { DecisionResult, DecisionStatus, HealthResponse, IncidentList } from "./types";

// Same-origin: nginx (docker) or Next.js rewrites (npm run dev) route to the backend.
export const API_BASE = "";

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number | null; error: string };

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = (await res.json()) as { detail?: unknown };
        if (typeof body.detail === "string") detail = body.detail;
      } catch {
        /* non-JSON error body */
      }
      return { ok: false, status: res.status, error: detail || `HTTP ${res.status}` };
    }
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return {
      ok: false,
      status: null,
      error: `Cannot reach the API. Is the backend running?`,
    };
  }
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  incidents: () => request<IncidentList>("/api/v1/incidents"),
  decisionStatus: () => request<DecisionStatus>("/api/v1/decision/status"),
  runDecision: (incident_id: string) =>
    request<DecisionResult>("/api/v1/decision/run", {
      method: "POST",
      body: JSON.stringify({ incident_id }),
    }),
};
