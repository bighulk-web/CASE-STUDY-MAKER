.PHONY: help setup dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend build clean

PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip

help:
	@echo "Targets: setup, dev, test, lint, build, clean"

setup:
	./setup.sh

dev-backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8756

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in two terminals (or 'npm run dev' from frontend which spawns both)."

test-backend:
	cd backend && .venv/bin/python -m pytest

test-frontend:
	cd frontend && npm run test -- --run

test: test-backend test-frontend

lint-backend:
	cd backend && .venv/bin/ruff check app tests && .venv/bin/mypy app || true

lint-frontend:
	cd frontend && npm run lint

lint: lint-backend lint-frontend

build:
	cd frontend && npm run build:app

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist frontend/dist-electron
