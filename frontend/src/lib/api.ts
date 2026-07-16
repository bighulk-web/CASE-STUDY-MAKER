import axios from "axios";

// Resolve the backend base URL. In Electron the preload exposes the port; in a
// browser dev context we fall back to the default dev port.
function backendBase(): string {
  const port =
    (typeof window !== "undefined" && (window as any).csm?.backendPort) || 8756;
  return `http://127.0.0.1:${port}/api`;
}

export const api = axios.create({
  baseURL: backendBase(),
  timeout: 120000,
});

export function wsUrl(path: string): string {
  const port =
    (typeof window !== "undefined" && (window as any).csm?.backendPort) || 8756;
  return `ws://127.0.0.1:${port}${path}`;
}
