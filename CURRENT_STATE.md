# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-17 — PM tick session

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 39/39 tests pass via `.venv/bin/python -m unittest discover tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Both commercial probes stalled**: zero external contact made since 2026-04-11. Outreach drafts exist (10 targets drafted) but have not been sent. This is a human-action gap — Evan must initiate outreach.
- **projects.conf update pending**: general session needs to add `skillfoundry-valuation` and `skillfoundry-researcher` to the reflection loop. Blocked by harness session's supervisor-repo boundary.

## Active probe status (as of 2026-04-17)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, runtime healthy. No external builder interactions. Design gap flagged: passive listing has no active conversion channel. See probe file for options.
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): 10 outreach drafts ready in researcher context. Priority targets named in probe file (achiya-automation-safari-mcp, barryw-immichmcp, goldentrii-agentrecall). Send one.

## Known broken or degraded
- **Tests require the venv**: `python` not available globally; `pytest` not installed; package not installed system-wide. Use `.venv/bin/python -m unittest discover tests/` — confirmed working.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Absence of signal is not typed evidence — record evidence gaps in `memory/findings/`, not `memory/venture/evidence/`

## What bit the last session
- Test execution is non-obvious: must use `.venv/bin/python -m unittest discover tests/` from project root. `python`, `python3 -m pytest`, and bare `python3 -m unittest` all fail in this environment.
- Valuation context changes require a separate git commit in `/opt/workspace/projects/skillfoundry/skillfoundry-valuation-context/`

## What the next agent must read first
1. Run tests first: `.venv/bin/python -m unittest discover -v tests/` from project root
2. PRINCIPLES.md and CLAUDE.md — multi-agent system with strong invariants
3. Valuation context: `memory/venture/probes/` and `memory/findings/2026-04-17-evidence-audit.md` for current commercial state
4. Reflection files at `/opt/workspace/runtime/.meta/skillfoundry-harness-reflection-*.md`
