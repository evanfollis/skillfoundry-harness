.PHONY: help setup check test lint typecheck

PYTHON := $(shell test -x .venv/bin/python && printf '%s' .venv/bin/python || command -v python3)

help:
	@printf '%s\n' \
		'make setup     Install the package and deterministic check dependencies' \
		'make check     Run declaration, hygiene, lint, and test gates' \
		'make test      Run pytest' \
		'make lint      Run Ruff' \
		'make typecheck Report the known mypy migration gap'

setup:
	@test -x .venv/bin/python || python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[test]"

check:
	@$(PYTHON) -c 'import pathlib,tomllib; r=pathlib.Path("."); d=tomllib.loads((r/"repo.toml").read_text()); assert d["schema_version"] == 1 and d["shape"] == "library"; [(_ for _ in ()).throw(AssertionError(f"missing {p}")) for p in ("README.md","repo.toml","Makefile","AGENTS.md","CLAUDE.md","docs/ARCHITECTURE.md") if not (r/p).exists()]'
	$(PYTHON) scripts/check_repo_hygiene.py
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m pytest -q
	git diff --check

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests scripts

typecheck:
	@printf '%s\n' 'mypy is not yet a gate: 31 pre-existing typing findings are tracked in docs/ARCHITECTURE.md.'
	@exit 1
