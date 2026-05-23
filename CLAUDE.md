# Skillfoundry Harness

## What This Is
Installable Python package that creates and runs Skillfoundry agents against git-backed context lineages. The orchestration layer for the entire Skillfoundry agent system.

## Architecture
- Python package (pyproject.toml)
- Agents operate on git-backed context repos (builder, designer, growth, pricing, researcher, valuation)
- Each context repo has a skillfoundry.toml config
- Agent coordination tracked in skillfoundry-agents repo

## Active Decisions

- **Agents operate on git-backed context repos.** Each agent role has its own context lineage. The harness reads `skillfoundry.toml` from each context repo.
- **Six agent roles are fixed.** Builder, designer, growth, pricing, researcher, valuation. Don't add new roles without explicit discussion.
- **Context lineages are append-forward.** Similar to recruiter — don't rewrite history, write new entries.
- **Advisor gate**: Any session that crosses a repo boundary OR edits a running production service source file MUST call `advisor()` before writing code. Evidence: session `4a3fa01e` (2026-04-18) edited CURRENT_STATE across a repo boundary without advisor, produced a false intermediate state, and required 3 commits to correct. Session `cd2879d6` called advisor organically and caught a live dead-code bug in the tick runner.
- **URL verification before claiming a URL is live or dead**: fetch the URL stated in the most-recent completion report before committing a state claim. Evidence: a session checked `lci.skillfoundry.pages.dev` (DNS fails), concluded "not deployed," committed, then discovered the correct URL is `lci.pages.dev`. Three commits to correct one factual claim.
- **CURRENT_STATE.md commit discipline**: every session's first repo-touching action is to commit any pending `CURRENT_STATE.md` edits before proceeding to other work. Uncommitted state from prior reflection passes is the expected accumulation pattern between sessions; this rule ensures it never persists across a human or executive interaction. Evidence: HEAD/disk drift accumulated to 12+ reflection cycles on this repo (cycle 15 / `3798d7d` was the last attended commit, with reflection-pass edits continuing to accumulate on disk). Pattern lifted from synaplex's resolution of the same class of drift (commits `808ee8c`, `44deac1`, `5f4f7c7`), per synthesis Proposal 1 in `runtime/.meta/cross-cutting-2026-05-13T15-26-05Z.md`.
- **`discovery_adapter.migrate` must run via the harness venv, not system python.** The system python3 on this server does NOT have `jsonschema` / `referencing` installed; the harness `.venv/` does. Invocations against system python fail with `ModuleNotFoundError: No module named 'referencing'`, telemetrying as `migrate.failure` with no useful counts. The `skillfoundry` console script does NOT expose `migrate` as a subcommand. Canonical invocation: `.venv/bin/python -m skillfoundry_harness.discovery_adapter.migrate --venture <path> [--dry-run] [--source-type system|user|cron|smoke]`. Evidence: 2026-05-23T14:26Z user-attended `migrate.failure` event traced to system-python invocation; venv invocation works cleanly (`531946f` telemetry verified).

## Related Repos
All under /opt/workspace/projects/skillfoundry/:
- `skillfoundry-agents` — Agent registry and coordination
- `skillfoundry-*-context` — Git-backed context lineages per agent role
- `skillfoundry-products` — Software artifact output

## Review Expectation

Use `/review` periodically as an adversarial review.

In the Skillfoundry workspace this means using Codex adversarial pressure to test:

- contract drift,
- hidden coupling,
- missing failure modes,
- and false confidence from internal coherence.
