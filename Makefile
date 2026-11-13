# Common tasks. Run `make help` to list them.
PYTHON ?= python3
SOURCE_CSV ?= ../UTSA-flood-images/image_metadata.csv

.PHONY: help install dev test lint format check data page gauges replay docker

help:  ## List available commands
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

install:  ## Install the app and developer tools into the active environment
	$(PYTHON) -m pip install -e ".[dev,data]"
	pre-commit install || true

dev:  ## Run the website locally with auto-reload (http://localhost:8080)
	$(PYTHON) -m uvicorn highground.web.main:app --reload --reload-dir src --reload-dir templates \
		--reload-dir content --reload-include '*.yaml' --reload-include '*.html' --port 8080

test:  ## Run the test suite
	$(PYTHON) -m pytest

lint:  ## Check code style
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:  ## Fix code style automatically
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

check: lint test  ## Run everything CI runs

data:  ## Rebuild data/hill_country_sites.csv from the dataset (set SOURCE_CSV=...)
	$(PYTHON) scripts/extract_sites.py --source "$(SOURCE_CSV)" --out data/hill_country_sites.csv

page:  ## Rebuild docs/index.html, the one-page site for GitHub Pages
	$(PYTHON) scripts/build_simple_page.py

gauges:  ## Fill gauge coordinates in content/gauges.yaml from USGS (needs internet)
	$(PYTHON) scripts/fetch_gauge_locations.py

replay:  ## Download July 2025 river levels for the Night Watch replay (needs internet)
	$(PYTHON) scripts/build_replay.py --start 2025-07-03 --end 2025-07-06

docker:  ## Build and run the site in Docker
	docker build -t highground .
	docker run --rm -p 8080:8080 --env-file .env highground
