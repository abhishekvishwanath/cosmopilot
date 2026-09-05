.PHONY: install dev lint typecheck test build

install:
	npm install
	cd apps/api && python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt

dev: ## Run web + api together (two terminals recommended instead: `make dev-web`, `make dev-api`)
	@echo "Run in separate terminals: make dev-web | make dev-api"

dev-web:
	npm run web:dev

dev-api:
	cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000

lint:
	npm run web:lint
	cd apps/api && .venv/bin/ruff check .

typecheck:
	npm run web:typecheck
	cd apps/api && .venv/bin/mypy app tests

test:
	npm run web:test
	cd apps/api && .venv/bin/pytest

build:
	npm run web:build
