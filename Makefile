.PHONY: help install run-server migrate makemigrations shell test lint format update docker-up docker-down docker-logs clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

run-server: ## Start Django development server
	poetry run python src/manage.py runserver

migrate: ## Run database migrations
	poetry run python src/manage.py migrate

makemigrations: ## Create new migrations
	poetry run python src/manage.py makemigrations

shell: ## Open Django shell
	poetry run python src/manage.py shell

test: ## Run all tests
	poetry run pytest

test-v: ## Run tests with verbose output
	poetry run pytest -v

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=src --cov-report=html

lint: ## Run linting checks
	poetry run ruff check src/

format: ## Format code with ruff
	poetry run ruff format src/

pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

update: install migrate pre-commit ## Install dependencies, run migrations, and setup pre-commit

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker container logs
	docker-compose logs -f

docker-build: ## Build Docker images
	docker-compose build

docker-shell: ## Open shell in web container
	docker-compose exec web python src/manage.py shell

docker-test: ## Run tests in Docker
	docker-compose exec web poetry run pytest

clean: ## Clean up Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
