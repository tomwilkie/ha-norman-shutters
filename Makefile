VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: all setup lint format format-check test clean

all: lint format-check test

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --quiet ruff pytest pytest-asyncio

setup: $(VENV)/bin/activate

lint: setup
	$(VENV)/bin/ruff check custom_components/ tests/

format-check: setup
	$(VENV)/bin/ruff format --check custom_components/ tests/

format: setup
	$(VENV)/bin/ruff format custom_components/ tests/

test: setup
	$(VENV)/bin/pytest tests/ -v

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache __pycache__
