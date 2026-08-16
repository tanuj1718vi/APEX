import { useEffect, useState } from "react";
import { api } from "../api/client";

export type BackendHealth = "checking" | "ok" | "unreachable";

/**
 * Polls GET /api/health every few seconds. Used to drive the live
 * heartbeat indicator in the sidebar so "is the backend up" is
 * always current, not just checked once on page load.
 */
export function useBackendHealth(intervalMs = 5000): BackendHealth {
  const [health, setHealth] = useState<BackendHealth>("checking");

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const result = await api.health();
        if (!cancelled) {
          setHealth(result.status === "ok" ? "ok" : "unreachable");
        }
      } catch {
        if (!cancelled) {
          setHealth("unreachable");
        }
      }
    }

    check();
    const id = setInterval(check, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  return health;
}
