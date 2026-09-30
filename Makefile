.PHONY: up down build logs test lint migrate seed shell secrets-check frontend-build

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f backend

test:
	cd backend && pytest

lint:
	cd backend && ruff check .

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m scripts.seed_demo_data

shell:
	docker compose exec backend bash

secrets-check:
	cd backend && python -m pytest tests/unit/test_no_hardcoded_secrets.py -q

frontend-build:
	cd frontend && npm ci && npm run build
