# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-17T05:20Z — tick session

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 39/39 tests pass via `.venv/bin/python -m unittest discover tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Both commercial probes stalled on human action**: probes are running but require Evan to initiate external contact. Agents cannot do this.
  - Launch Compliance Intelligence: 10 drafts ready, none sent. Evan must send first message.
  - Launchpad Lint: passive listing, no external interactions. Evan must promote in MCP builder communities.
- **Watcher ID misalignment — needs executive decision**: preflight-watcher emits `assumptionId: mcp-builders-need-publish-readiness-check` and `probeId: preflight-publish-readiness` — neither slug matches a formal venture file. Evidence was recorded with log's ID verbatim; cross-joins on assumption_id will miss it until IDs are reconciled. See probe-status handoff to general.

## Active probe status (as of 2026-04-17T05:20Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, runtime healthy. No external builder interactions. Design gap: passive listing has no active conversion channel.
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): 10 outreach drafts ready. None sent.
- **Preflight** (`preflight-distribution-signal`): Activation metric MET. Evidence formally recorded in valuation-context (commit a8f7396). Evidence quality: weak (single invocation, no friction, no follow-up). Probe continues through 2026-04-25.

## Known broken or degraded
- **Tests require the venv**: `python` not available globally; use `.venv/bin/python -m unittest discover tests/` from project root.
- **launchpad-lint venv shebangs stale**: `.venv/bin/pip` shebang points to `/opt/projects/...` (old path). Service runs fine (systemd calls python directly), but pip calls from venv fail. Full rebuild required — needs host-control session (sudo systemctl access). This session did NOT do the rebuild (out of scope + service restart boundary).
- **Auth failure pattern**: Session c5309767 (2026-04-16T17:42Z) hit 401 immediately. Pattern unclear — may be one-off or recurring.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Absence of signal is not typed evidence — record evidence gaps in `memory/findings/`, not `memory/venture/evidence/`
- Preflight real-user signal (Apr 14) is `external_conversation / weak` evidence — recorded in valuation-context

## What bit this session
- Tick prompt boundary said "harness only" but all actual work was in valuation-context (evidence + probe update). This is a boilerplate boundary conflict — the handoff was written correctly and requires valuation-context writes. Noted in completion report.
- Watcher log IDs (`assumptionId`, `probeId`) don't match formal venture file slugs — discovered via advisor check before writing. Evidence recorded with log's ID verbatim; flagged for executive follow-up.

## What the next agent must read first
1. Run tests: `.venv/bin/python -m unittest discover -v tests/` from project root
2. Probe-status handoff to general: `/opt/workspace/runtime/.handoff/general-skillfoundry-probe-status-2026-04-16.md` — two human-action blockers plus watcher ID flag
3. Valuation context commit a8f7396: evidence + probe state
4. CLAUDE.md — multi-agent system with strong invariants
5. Reflection at `/opt/workspace/runtime/.meta/skillfoundry-harness-reflection-2026-04-17T02-22-25Z.md`
