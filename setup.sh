#!/usr/bin/env bash
# Idempotent environment setup for Case Study Maker.
# Installs backend (Python venv) and frontend (npm) dependencies and optional
# system tools (LibreOffice for PDF export, Tesseract for OCR).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> System dependencies (LibreOffice, Tesseract)"
if command -v apt-get >/dev/null 2>&1; then
  if ! command -v soffice >/dev/null 2>&1 || ! command -v tesseract >/dev/null 2>&1; then
    sudo apt-get update -qq || true
    sudo apt-get install -y -qq libreoffice tesseract-ocr python3-venv || \
      echo "WARN: could not install system packages (continuing; PDF/OCR may be limited)"
  fi
else
  echo "WARN: apt-get not found; skipping system packages"
fi

echo "==> Backend (Python venv)"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q --upgrade pip
# Base + dev by default. Set CSM_INSTALL_EXTRAS to add heavy providers, e.g.:
#   CSM_INSTALL_EXTRAS="embeddings,vectorstore,llm,ocr" ./setup.sh
EXTRAS="dev"
if [ -n "${CSM_INSTALL_EXTRAS:-}" ]; then
  EXTRAS="dev,${CSM_INSTALL_EXTRAS}"
fi
pip install -q -e ".[${EXTRAS}]"
deactivate
cd "$ROOT"

echo "==> Frontend (npm)"
cd "$ROOT/frontend"
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi
cd "$ROOT"

echo "==> Setup complete."
