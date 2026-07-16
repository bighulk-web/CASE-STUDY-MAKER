import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { wsUrl } from "@/lib/api";

export interface JobEvent {
  job_id: number;
  type: string;
  ref_id: number | null;
  status: string;
  progress?: number;
  message?: string;
}

/**
 * Subscribe to backend job progress over WebSocket. Invalidates relevant queries
 * as jobs complete so the UI reflects background processing in real time.
 */
export function useJobStream(onEvent?: (e: JobEvent) => void) {
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl("/ws/jobs"));
        wsRef.current = ws;
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data) as JobEvent;
            onEvent?.(data);
            if (data.status === "done" || data.status === "error") {
              qc.invalidateQueries({ queryKey: ["documents"] });
              qc.invalidateQueries({ queryKey: ["presentations"] });
              qc.invalidateQueries({ queryKey: ["facets"] });
              qc.invalidateQueries({ queryKey: ["jobs"] });
            }
          } catch {
            /* ignore malformed */
          }
        };
        ws.onclose = () => {
          if (!closed) retry = setTimeout(connect, 3000);
        };
        ws.onerror = () => ws.close();
      } catch {
        retry = setTimeout(connect, 3000);
      }
    };
    connect();

    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
