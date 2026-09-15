.PHONY: setup build run test lint format test-ui

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.lock
	.venv/bin/python -m pip install -e . --no-deps
	pnpm --dir frontend install --frozen-lockfile

build:
	pnpm --dir frontend run build

run:
	.venv/bin/python -m opentrons_ai serve

test:
	.venv/bin/python -m pytest tests/test_dashboard.py -q

test-ui: build
	pnpm --dir frontend test

lint:
	.venv/bin/ruff check src/opentrons_ai tests/test_dashboard.py
	.venv/bin/ruff format --check src/opentrons_ai tests/test_dashboard.py
	pnpm --dir frontend exec prettier --check src tests scripts '*.{json,ts}' pnpm-workspace.yaml

format:
	.venv/bin/ruff format src/opentrons_ai tests/test_dashboard.py
	pnpm --dir frontend exec prettier --write src tests scripts '*.{json,ts}' pnpm-workspace.yaml
