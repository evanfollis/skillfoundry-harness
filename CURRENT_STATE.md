# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-16 — seeded by executive (general session)

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: unknown — verify with `python -m pytest` or equivalent before assuming anything works
- **Entry**: `src/` — check `pyproject.toml` for entrypoints

## What's in progress
One handoff pending (`skillfoundry-harness-reflection-stale-2026-04-15T10-48-22Z.md`):

The reflect-all.sh loop has a stdin inheritance bug that causes it to only process the first project per run. skillfoundry-harness likely never received a reflection for this reason, not due to project inactivity.

**Requested action**:
1. Once `reflect-all.sh` stdin fix is applied (check supervisor INBOX), verify next reflection cycle produces a file
2. If not, manually trigger: `bash /opt/workspace/supervisor/scripts/lib/reflect.sh skillfoundry-harness /opt/workspace/projects/skillfoundry/skillfoundry-harness`
3. Report back via handoff to general if reflection still fails

## Known broken or degraded
- **Zero reflection history**: no reflection files exist for this project despite 3 commits in last 48h window (as of 2026-04-15)
- **Stdin bug in reflect-all.sh**: upstream issue in supervisor repo; may already be fixed — check before assuming it's still broken

## Blocked on
- `reflect-all.sh` stdin fix in supervisor repo

## Recent decisions
- Unknown — no reflection history to draw from

## What bit the last session
- Unknown (no prior tick session for this project)

## What the next agent must read first
1. Check if the reflect-all.sh stdin bug has been fixed before doing anything else
2. Run the test suite to confirm baseline before touching code
3. Read PRINCIPLES.md and CLAUDE.md — this is a multi-agent system with strong invariants
