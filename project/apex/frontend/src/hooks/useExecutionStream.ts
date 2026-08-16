import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Execution, ExecutionEvent } from "../api/types";

export function useExecutionStream(executionId: string | null) {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const seenEventIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!executionId) return;

    let cancelled = false;
    let socket: WebSocket | null = null;
    let pollHandle: number | null = null;

    seenEventIds.current = new Set();
    setEvents([]);
    setExecution(null);

    async function refreshFromRest() {
      try {
        const detail = await api.getExecution(executionId!);
        if (cancelled) return;
        setExecution(detail.execution);
        setEvents((prev) => {
          const merged = [...prev];
          for (const event of detail.events) {
            if (!seenEventIds.current.has(event.id)) {
              seenEventIds.current.add(event.id);
              merged.push(event);
            }
          }
          return merged;
        });
      } catch {
        // execution may not exist yet; ignore and let polling retry
      }
    }

    function startPolling() {
      refreshFromRest();
      pollHandle = window.setInterval(refreshFromRest, 1500);
    }

    try {
      socket = new WebSocket(api.streamUrl(executionId));

      socket.onopen = () => {
        if (cancelled) return;
        setConnected(true);
      };

      socket.onmessage = () => {
        if (cancelled) return;
        // The socket is a low-latency "something happened" signal;
        // REST (deduped by real DB event id) remains the single
        // source of truth for event content and ordering.
        refreshFromRest();
      };

      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
      };

      socket.onerror = () => {
        socket?.close();
      };
    } catch {
      socket = null;
    }

    // REST polling runs alongside the socket regardless, since it's
    // the source of truth for `Execution.status`/`result` and is a
    // reliable fallback if the socket never connects.
    startPolling();

    return () => {
      cancelled = true;
      socket?.close();
      if (pollHandle !== null) window.clearInterval(pollHandle);
    };
  }, [executionId]);

  return { execution, events, connected };
}
