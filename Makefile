# Murimi OS — common developer tasks.
# On Windows use Git Bash, or run the underlying commands directly.

VENV_BIN := .venv/Scripts
ifeq ($(OS),Windows_NT)
  PY := $(VENV_BIN)/python.exe
else
  PY := .venv/bin/python
endif

.PHONY: help venv install dev-services migrate seed run worker beat lint test fmt

help:
	@echo "venv          - create virtual environment (.venv)"
	@echo "install       - install dev dependencies"
	@echo "dev-services  - start postgres + redis via docker compose"
	@echo "migrate       - alembic upgrade head"
	@echo "seed          - load demo tenants/users/farms + RAG knowledge"
	@echo "run           - start API (uvicorn, reload)"
	@echo "worker        - start Celery worker"
	@echo "beat          - start Celery beat scheduler"
	@echo "lint / fmt    - ruff check / ruff format"
	@echo "test          - run pytest"

venv:
	py -3.11 -m venv .venv || python -m venv .venv

install:
	$(PY) -m pip install --upgrade pip wheel setuptools
	$(PY) -m pip install -r requirements-dev.txt

dev-services:
	docker compose -f docker-compose.dev.yml up -d

migrate:
	$(PY) -m alembic upgrade head

seed:
	$(PY) -m scripts.seed

run:
	$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	$(PY) -m celery -A app.notifications.celery_app worker --loglevel=info -P solo

beat:
	$(PY) -m celery -A app.notifications.celery_app beat --loglevel=info

lint:
	$(PY) -m ruff check app tests

fmt:
	$(PY) -m ruff format app tests

test:
	$(PY) -m pytest
