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

## Related Repos
All under /opt/projects/skillfoundry/:
- `skillfoundry-agents` — Agent registry and coordination
- `skillfoundry-*-context` — Git-backed context lineages per agent role
- `skillfoundry-products` — Software artifact output
