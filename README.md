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
