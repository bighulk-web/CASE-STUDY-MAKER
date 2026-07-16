#!/usr/bin/env bash
# Bundle the Python backend into a standalone executable with PyInstaller.
# Output: backend/dist/csm-backend/csm-backend  (one-dir bundle)
# The Electron packaging step copies this into the app's resources/backend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q pyinstaller

pyinstaller \
  --noconfirm \
  --clean \
  --name csm-backend \
  --collect-all app \
  --collect-submodules pptx \
  --collect-submodules docx \
  --collect-submodules fitz \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan.on \
  run_backend.py

echo "Backend bundled at backend/dist/csm-backend/"
