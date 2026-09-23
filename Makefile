.PHONY: up down build logs test lint migrate seed shell

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
	cd backend && alembic upgrade head

seed:
	cd backend && python -m scripts.seed_demo_data

shell:
	docker compose exec backend bash
