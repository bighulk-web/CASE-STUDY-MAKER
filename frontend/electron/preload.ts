import { contextBridge } from "electron";

// The renderer talks to the backend over HTTP directly; we only expose a small,
// safe surface here for environment info.
contextBridge.exposeInMainWorld("csm", {
  backendPort: Number(process.env.CSM_PORT ?? 8756),
  platform: process.platform,
});
