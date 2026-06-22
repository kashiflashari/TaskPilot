.PHONY: install dev test lint run serve docker-up docker-down

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

# Usage: make run GOAL="Summarise #general on Slack and email it to me@corp.com"
run:
	taskpilot run "$(GOAL)"

serve:
	uvicorn taskpilot.api.main:app --reload --port 8000

docker-up:
	docker compose up --build

docker-down:
	docker compose down
