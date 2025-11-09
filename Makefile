.PHONY: help up down logs build restart shell migrate collectstatic test demo clean

# Default target
help:
	@echo "Native Language Market - Makefile Commands"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make up          - Start all services with Docker Compose"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Build Docker images"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-web    - View logs from web service only"
	@echo ""
	@echo "Django Commands (in container):"
	@echo "  make shell       - Open Django shell in container"
	@echo "  make bash        - Open bash shell in container"
	@echo "  make migrate     - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make collectstatic - Collect static files"
	@echo "  make createsuperuser - Create Django superuser"
	@echo ""
	@echo "Data Management:"
	@echo "  make demo        - Load demo users and default jobs"
	@echo "  make load-users  - Load demo users only"
	@echo "  make load-jobs   - Load default jobs only"
	@echo ""
	@echo "Development Commands (local, no Docker):"
	@echo "  make dev-install - Install Python dependencies with uv"
	@echo "  make dev-migrate - Run migrations locally"
	@echo "  make dev-run     - Run Django dev server locally"
	@echo "  make dev-test    - Run tests locally"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Remove generated files and containers"
	@echo "  make clean-db    - Remove SQLite database"

# Docker commands
up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

restart: down up

logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

# Django commands (run in container)
shell:
	docker compose exec web uv run python manage.py shell

bash:
	docker compose exec web bash

migrate:
	docker compose exec web uv run python manage.py migrate

makemigrations:
	docker compose exec web uv run python manage.py makemigrations

collectstatic:
	docker compose exec web uv run python manage.py collectstatic --noinput

createsuperuser:
	docker compose exec web uv run python manage.py createsuperuser

# Data management
demo: load-users load-jobs
	@echo "Demo data loaded successfully!"

load-users:
	docker compose exec web uv run python manage.py load_demo_users

load-jobs:
	docker compose exec web uv run python manage.py load_default_jobs

# Local development (without Docker)
dev-install:
	cd marketplace-py && uv sync

dev-migrate:
	cd marketplace-py && uv run python manage.py migrate

dev-collectstatic:
	cd marketplace-py && uv run python manage.py collectstatic --noinput

dev-run:
	cd marketplace-py && uv run python manage.py runserver

dev-test:
	cd marketplace-py && uv run python manage.py test

dev-shell:
	cd marketplace-py && uv run python manage.py shell

# Testing
test:
	docker compose exec web uv run python manage.py test

test-coverage:
	docker compose exec web uv run python -m pytest --cov=. --cov-report=html

# Maintenance
clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf marketplace-py/staticfiles/* 2>/dev/null || true
	@echo "Cleaned up containers and generated files"

clean-db:
	rm -f marketplace-py/db.sqlite3
	@echo "Database removed. Run 'make migrate' to recreate."
