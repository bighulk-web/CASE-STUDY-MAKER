# Case Study Maker

An AI-powered proposal automation desktop app for consulting teams. Upload hundreds of
case studies (PowerPoint, Word, PDF, or text), let the app extract and analyze them into
structured metadata with embeddings for semantic search, then generate polished PowerPoint
presentations from your own templates — preserving formatting exactly.

## Highlights
- **Document library**: upload, organize (folders), version history, duplicate detection, preview.
- **AI processing**: 23-field structured metadata, summaries, keywords, tagging, classification.
- **Hybrid search**: semantic + metadata + keyword + tag, fused and ranked.
- **Presentation builder**: natural-language prompt → ranked case studies → template population
  → editable PPTX + PDF.
- **Offline-first**: works with no API keys (local embeddings + heuristic analysis); plug in
  OpenAI / Anthropic / Gemini when you want.

## Tech stack
- **Frontend**: React, TypeScript, TailwindCSS, shadcn UI, Electron.
- **Backend**: Python, FastAPI, SQLAlchemy/SQLite, ChromaDB, python-pptx / PyMuPDF / python-docx.

## Getting started
See [AGENTS.md](./AGENTS.md) for setup, run, and test instructions.

```bash
./setup.sh
make dev-backend    # terminal 1
make dev-frontend   # terminal 2
```

## Architecture

```
Electron (main)  ──spawns──►  Python FastAPI backend (sidecar, localhost)
      │                                   │
   React renderer ──HTTP + WebSocket──────┘
```

- **Backend** (`backend/app`) is fully modular: `services/ingestion`, `services/extraction`,
  `services/metadata`, `services/embeddings`, `services/vectorstore`, `services/search`,
  `services/prompt`, `services/template`, `services/pptx`, `services/llm`, `services/jobs`.
- **AI pipeline rule**: the LLM only (a) extracts case-study metadata, (b) parses the
  user's prompt into a structured search intent, and (c) optionally rewrites structured
  snippets. **Deck assembly is deterministic** placeholder population — the LLM never
  generates a whole PowerPoint.
- **Offline-first**: defaults to a heuristic analyzer + local hashing embeddings + a
  numpy vector store, so everything works with no API keys or heavy models. Optional
  upgrades: OpenAI/Anthropic/Gemini LLMs, BGE-large embeddings, ChromaDB — all
  auto-detected and configurable in Settings.

## Packaging

```bash
make package        # PyInstaller-bundle the backend + electron-builder installer
```

This produces a self-contained desktop app (the backend is bundled as a sidecar binary).
`electron-builder` is configured for Windows (NSIS), Linux (AppImage), and macOS (dmg).
Building/validating a signed **Windows** binary requires a Windows/CI host.
