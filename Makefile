VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: all setup lint format format-check test clean

all: lint format-check test

PYTHON_VERSION ?= python3.14

$(VENV)/.installed: requirements_test.txt
	test -x $(PYTHON) || $(PYTHON_VERSION) -m venv $(VENV)
	$(PIP) install --quiet -r requirements_test.txt
	touch $@

setup: $(VENV)/.installed

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
