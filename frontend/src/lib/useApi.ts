"use client";

import { useEffect, useState } from "react";
import type { ApiResult } from "./api";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: string }
  | { status: "ready"; data: T };

/** Fetch once on mount. The fetcher must be a stable module-level function. */
export function useApi<T>(fetcher: () => Promise<ApiResult<T>>): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  useEffect(() => {
    let cancelled = false;
    fetcher().then((r) => {
      if (cancelled) return;
      setState(r.ok ? { status: "ready", data: r.data } : { status: "error", error: r.error });
    });
    return () => {
      cancelled = true;
    };
  }, [fetcher]);
  return state;
}
