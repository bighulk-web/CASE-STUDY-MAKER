"""Standalone backend entry point (used by PyInstaller for packaged builds).

Reads the port from ``CSM_PORT`` (set by the Electron main process) and starts uvicorn.
"""

from __future__ import annotations

import os

import uvicorn

from app.main import app


def main() -> None:
    host = os.environ.get("CSM_HOST", "127.0.0.1")
    port = int(os.environ.get("CSM_PORT", "8756"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
