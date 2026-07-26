.PHONY: help setup check test lint typecheck

help:
	@printf '%s\n' \
		'make setup     Install the package and deterministic check dependencies' \
		'make check     Run declaration, hygiene, lint, and test gates' \
		'make test      Run pytest' \
		'make lint      Run Ruff' \
		'make typecheck Report the known mypy migration gap'

setup:
	python3 -m pip install -e ".[test]"

check:
	@python3 -c 'import pathlib,tomllib; r=pathlib.Path("."); d=tomllib.loads((r/"repo.toml").read_text()); assert d["schema_version"] == 1 and d["shape"] == "library"; [(_ for _ in ()).throw(AssertionError(f"missing {p}")) for p in ("README.md","repo.toml","Makefile","AGENTS.md","CLAUDE.md","docs/ARCHITECTURE.md") if not (r/p).exists()]'
	python3 scripts/check_repo_hygiene.py
	python3 -m ruff check src tests scripts
	python3 -m pytest -q
	git diff --check

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check src tests scripts

typecheck:
	@printf '%s\n' 'mypy is not yet a gate: 31 pre-existing typing findings are tracked in docs/ARCHITECTURE.md.'
	@exit 1
