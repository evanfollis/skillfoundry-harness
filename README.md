# skillfoundry-harness

`skillfoundry-harness` is the installable Python package that creates and runs
Skillfoundry agents.

This repo owns the stable machinery: runtime semantics, repository contracts,
validation, CLI entrypoints, and the APIs used to operate on agent context repos.
It should be pip-installable and usable against any compliant context repository
without importing workspace-local Python code.

The harness is intentionally opinionated about the context repository boundary. A
valid agent context repo exposes one config file and four explicit roots:

- `bundles/` for reviewed context inputs.
- `memory/` for long-lived harness-managed state.
- `artifacts/` for durable generated outputs.
- `runs/` for execution-scoped output.
- a `[frontdoor]` manifest for progressive disclosure.

## Scope

- Python package and console entrypoints.
- Runtime construction and lifecycle.
- Canonical schemas and validation rules.
- Repository interfaces for agent context repos.
- Safety boundaries for how the harness reads and writes workspace state.

## Non-goals

- Long-lived agent memory or bundles.
- Agent registry and coordination hub concerns.
- Embedded agent-specific context content.

## Repository Layout

- `src/skillfoundry_harness/`: package source.
- `schemas/`: canonical machine-readable contracts.
- `tests/`: stdlib test suite and fixtures.
- `docs/`: architecture and policy documents.
- `scripts/`: repository enforcement.

## First Slice

The initial scaffold provides:

- `Runtime.open(path)` for opening a context repo.
- `skillfoundry validate <path>` for validating a context repo or bundle.
- `skillfoundry describe <path>` for printing the resolved repository contract.
- `skillfoundry frontdoor <path>` for rendering the pinned context front door.
- explicit `thread`, `turn`, and `run` records persisted under `runs/`.
- bounded branch-local draft workspaces under `artifacts/branches/<branch>/`.
- real managed git worktrees for isolated subagent execution.
- explicit proposal, approval, and apply flows for canonical memory updates.
- durable validation artifacts referenced by proposals and enforced by repository-owned promotion policy at apply time.
- durable approval artifacts for canon-entry authorization.
- proposal snapshot and diff artifacts for review legibility.
- content-pinned proposal, validation, and approval artifacts so apply gates a reviewed immutable change, not just mutable file paths.
- Canonical context bundle validation owned by the harness.
- typed bundle loading from `bundles/` for runtime-facing consumption.

See [docs/CONTEXT_REPOSITORY_CONTRACT.md](/Users/evanfollis/projects/skillfoundry/skillfoundry-harness/docs/CONTEXT_REPOSITORY_CONTRACT.md) for the
current repository contract.
See [docs/DESIGN_SYNTHESIS.md](/Users/evanfollis/projects/skillfoundry/skillfoundry-harness/docs/DESIGN_SYNTHESIS.md) for the external ideas that should
shape the next primitives.

## Local Setup

This package requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3.12 -m pip install -e .
python3.12 -m unittest discover -s tests
python3.12 -m skillfoundry_harness.cli validate tests/fixtures/minimal_context_repo
```

If `python3` already resolves to 3.12 on your machine, the same flow works with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m unittest discover -s tests
python3 -m skillfoundry_harness.cli validate tests/fixtures/minimal_context_repo
python3 -m skillfoundry_harness.cli list-bundles tests/fixtures/minimal_context_repo
```
