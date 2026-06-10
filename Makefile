# Solidità 4.0 — dev shortcuts
COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: up down logs migrate revision test lint dev seed fmt

up:            ## start postgres + redis + backend
	$(COMPOSE) up -d

down:          ## stop stack
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f backend

migrate:       ## apply migrations (host -> local postgres)
	cd backend && alembic upgrade head

revision:      ## make a new autogenerate migration: make revision m="msg"
	cd backend && alembic revision --autogenerate -m "$(m)"

dev:           ## run backend locally with reload (needs local postgres)
	cd backend && uvicorn app.main:app --reload

test:          ## run backend tests
	cd backend && pytest -q

lint:
	cd backend && ruff check .

fmt:
	cd backend && ruff check --fix . && ruff format .

seed:          ## insert demo company + admin user
	cd backend && python -m app.scripts.seed
