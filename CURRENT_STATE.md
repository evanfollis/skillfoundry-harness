# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-16 — PM tick session

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 39/39 tests pass via `.venv/bin/python -m unittest discover tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
Nothing active. All known issues resolved:
- Reflection loop stdin bug fixed in supervisor (`reflect-all.sh` now has `< /dev/null` guard)
- 3 reflection files now exist for this project (the latter two skipped for inactivity — expected)
- Workspace path migration reflected: `/opt/projects/` → `/opt/workspace/projects/` in CLAUDE.md and scripts/hooks/install.sh

## Known broken or degraded
- **Tests require the venv**: `python` not available globally; `pytest` not installed; package not installed system-wide. Use `.venv/bin/python -m unittest discover tests/` — confirmed working.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics

## What bit the last session
- Test execution is non-obvious: must use `.venv/bin/python -m unittest discover tests/` from project root. `python`, `python3 -m pytest`, and bare `python3 -m unittest` all fail in this environment.

## What the next agent must read first
1. Run tests first: `.venv/bin/python -m unittest discover -v tests/` from project root
2. PRINCIPLES.md and CLAUDE.md — multi-agent system with strong invariants
3. Reflection files at `/opt/workspace/runtime/.meta/skillfoundry-harness-reflection-*.md`
