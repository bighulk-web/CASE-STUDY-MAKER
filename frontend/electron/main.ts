/**
 * Electron main process.
 *
 * In development it loads the Vite dev server. In production it spawns the Python
 * FastAPI backend as a sidecar on a localhost port, waits for /health, then loads
 * the built renderer. The backend binary/venv is resolved from a few candidate
 * locations so it works both from source and from a packaged build.
 */
import { spawn, ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { app, BrowserWindow, shell } from "electron";

const isDev = process.env.NODE_ENV === "development";
const BACKEND_HOST = "127.0.0.1";
const BACKEND_PORT = Number(process.env.CSM_PORT ?? 8756);

let mainWindow: BrowserWindow | null = null;
let backend: ChildProcess | null = null;

function resolveBackend(): { cmd: string; args: string[]; cwd: string } | null {
  // 1) Packaged one-dir backend binary (produced by PyInstaller).
  const packaged = path.join(process.resourcesPath ?? "", "backend", "csm-backend");
  if (existsSync(packaged)) {
    return { cmd: packaged, args: [], cwd: path.dirname(packaged) };
  }
  // 2) Source checkout venv.
  const repoRoot = path.resolve(app.getAppPath(), "..", "..");
  const venvPython = path.join(repoRoot, "backend", ".venv", "bin", "python");
  if (existsSync(venvPython)) {
    return {
      cmd: venvPython,
      args: ["-m", "uvicorn", "app.main:app", "--host", BACKEND_HOST, "--port", String(BACKEND_PORT)],
      cwd: path.join(repoRoot, "backend"),
    };
  }
  return null;
}

function startBackend(): void {
  if (isDev) return; // in dev, run backend separately via `make dev-backend`
  const resolved = resolveBackend();
  if (!resolved) {
    console.error("Backend not found; the app requires the Python backend.");
    return;
  }
  backend = spawn(resolved.cmd, resolved.args, {
    cwd: resolved.cwd,
    env: { ...process.env, CSM_PORT: String(BACKEND_PORT) },
    stdio: "inherit",
  });
  backend.on("exit", (code) => console.log(`backend exited: ${code}`));
}

function waitForBackend(retries = 60): Promise<void> {
  return new Promise((resolve, reject) => {
    const attempt = (n: number) => {
      const req = http.get(
        { host: BACKEND_HOST, port: BACKEND_PORT, path: "/api/health", timeout: 1000 },
        (res) => {
          res.resume();
          resolve();
        },
      );
      req.on("error", () => {
        if (n <= 0) reject(new Error("backend did not start"));
        else setTimeout(() => attempt(n - 1), 500);
      });
      req.on("timeout", () => req.destroy());
    };
    attempt(retries);
  });
}

async function createWindow(): Promise<void> {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: "#0b0b0f",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  if (isDev) {
    await mainWindow.loadURL("http://localhost:5273");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    try {
      await waitForBackend();
    } catch (e) {
      console.error(e);
    }
    await mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  mainWindow.on("closed", () => (mainWindow = null));
}

app.whenReady().then(async () => {
  startBackend();
  await createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("quit", () => {
  if (backend) backend.kill();
});
