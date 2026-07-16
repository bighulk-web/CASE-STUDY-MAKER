# AGENTS.md — Case Study Maker

AI-powered proposal automation desktop app. Upload case studies (PPTX/DOCX/PDF/TXT),
auto-extract + LLM-analyze into structured metadata, search semantically, and generate
polished PowerPoint decks from templates with `{{placeholders}}` — preserving formatting.

## Layout
- `backend/` — Python 3.12 + FastAPI service (ingestion, extraction, metadata, embeddings, search, PPTX generation). The "brain".
- `frontend/` — Electron + React + TypeScript + Tailwind + shadcn UI desktop app.
- `setup.sh` — one-shot environment setup. `Makefile` — common tasks.

## Setup
```bash
./setup.sh                       # backend venv + npm install + system tools
# Optional heavy providers (local embeddings, chroma, cloud LLMs, OCR):
CSM_INSTALL_EXTRAS="embeddings,vectorstore,llm,ocr" ./setup.sh
```

## Run (dev)
```bash
make dev-backend    # terminal 1: uvicorn on 127.0.0.1:8756
make dev-frontend   # terminal 2: Vite (5273) + Electron
```
The backend is offline-first: it works with **no API keys** (heuristic LLM + local/hashing
embeddings). Enter provider keys in Settings to enable OpenAI/Anthropic/Gemini.

## Test & lint
```bash
make test           # backend pytest + frontend vitest
make lint           # ruff + mypy (backend), eslint (frontend)
cd backend && .venv/bin/python -m pytest        # backend only
cd frontend && npx vitest run                    # frontend only
```

## Conventions
- **Backend**: strict typing (Pydantic v2, mypy), ruff-formatted, tests in `backend/tests`.
  All runtime state lives under a single data dir (`~/.case-study-maker`, override with
  `CSM_DATA_DIR`). Tests always use an isolated temp data dir.
- **Frontend**: strict TS, ESLint, functional React + hooks, shadcn UI, zustand stores.
- **AI rule**: never ask the LLM to generate a whole deck. LLM only extracts metadata,
  parses prompt intent, and (optionally) rewrites structured snippets. Deck assembly is
  deterministic template population.
- Optional dependencies (chromadb, sentence-transformers, cloud SDKs, tesseract, libreoffice)
  are detected at runtime via `/api/capabilities`; the app degrades gracefully without them.

## Data dir override
Set `CSM_DATA_DIR=/path` to sandbox all state (DB, storage, chroma, presentations).
