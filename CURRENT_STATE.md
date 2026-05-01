# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-05-01T02-29-18Z — reflection pass

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 59/59 tests pass via `.venv/bin/python -m pytest tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Preflight Worker DEPLOYED** (2026-04-18): `https://preflight.skillfoundry.workers.dev/` — landing page + MCP endpoint + sourceType all live. Verified live 2026-04-24T12:25Z.
- **Blog DEPLOYED** (2026-04-18): `https://skillfoundry-blog.pages.dev/` — 3 posts live (one per probe). CF Pages project `skillfoundry-blog`.
- **LCI landing page DEPLOYED** (2026-04-18): LIVE at `https://lci.pages.dev/` — $99 pricing, Tally placeholder ("Intake form loading shortly"). Awaiting Tally embed code from Evan to complete. Escalation handoff written.
- **Watcher IGNORE_RE live** (2026-04-18): `preflight-watcher.service` restarted by Evan. Mozilla/Linux filtering active.
- **sourceType gate VERIFIED LIVE** (2026-04-24T12:25Z): `x-source-type: system` test calls to `/mcp` correctly excluded from real-user alert log. Last real-user alert entry: 2026-04-18T08:58Z.
- **Preflight probe active through 2026-04-25**: activation metric MET (Apr 14 curl/8.5.0). Evidence quality: weak. Post-reclassification: 1 confirmed real user event, 188 Mozilla events correctly excluded.
- **Canon adapter FIXED + PUSHED** (2026-04-23 tick 17-37-15Z): `discovery_adapter/` 3 correctness bugs fixed at commit `2f63ae5`. See below.

## Canon adapter — fix status (2026-04-23)

All 3 adversarial-review findings from `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md` addressed:

1. **Finding 1 FIXED** (`parse_probe` phase bug): Closure event (probe→promotion) now only emits when `decision_kind="promote"` is passed by caller.
2. **Finding 2 FIXED** (enum silent coercion): Unknown enum values now raise `AdapterParseError`. `operational_readiness_only→neutral` alias added. `weakens_assumption` left as error.
3. **Finding 3 SPLIT**: ADR at `docs/adr-discovery-adapter-pure-parse-interface.md`. Structural refactor deferred.

Post-fix Codex review (`supervisor/.reviews/discovery-adapter-2f63ae5-post-fix-2026-04-23T17-59Z.md`) found 3 more findings, addressed in `664aba5`:

- **Finding A** (3 claims per assumption collapsed to 1): Proposal doc at `docs/claims-per-assumption-options.md` routed to context-repo. No code change. Harness preference: Option 1 (emit 3 Claim envelopes) > 3 > 2.
- **Finding B** (pre-pass swallowed decision-header parse failures): FIXED. `migrate.py` now logs `[PREPASS-DECISION]` to stderr with loss-of-edge framing + returns non-zero. Test added. 59/59.
- **Finding C** (parse-file boundary leaking via cross-directory join): ADR upgraded from `proposed` → `accepted, pending scheduling`. Interim rule: new cross-file dependencies are ADR-class until refactor lands.

Backfill re-run on valuation-context:
- Before: 14 envelopes (2 evidence with silently-coerced wrong polarity)
- After: 13 OK envelopes + 1 stale (see below) + 2 friction events logged to stderr
- `2026-04-25-preflight-probe-close.json` **RESOLVED** in valuation-context (commit `39e5778` 2026-04-23T17:47Z): polarity changed to `contradicts_assumption`; envelope regenerated. See valuation-context completion handoff 2026-04-24T12:35Z.

## Active probe status (as of 2026-04-24T12:25Z live verification)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Backend stub live at `https://skillfoundry.synaplex.ai/products/launchpad-lint/` (39B plaintext). Render/Fly credential blocker for HTML landing.
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): landing page DEPLOYED at `https://lci.pages.dev/`. Blog post live. Tally embed placeholder live — Evan must create Tally form.
- **Preflight** (`preflight-distribution-signal`): Worker deployed at `preflight.skillfoundry.workers.dev`. Landing page + sourceType + MCP endpoint all live. Blog post live. 1 confirmed real user (Apr 14).

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m pytest tests/` from project root.
- **fly not installed**: cannot deploy launchpad-lint from this server. Render deploy on separate track.
- **LCI Tally form needed**: Landing page is LIVE at `lci.pages.dev` but shows "Intake form loading shortly." Evan must: (1) create Tally form at tally.so, (2) return embed code → swap `<!-- TALLY_EMBED -->` in `products/lci/index.html`, (3) agent runs `CLOUDFLARE_API_TOKEN=$(cat /root/.cloudflare-token) WRANGLER_HOME=/tmp/wrangler-home npm --cache /tmp/npm-cache exec --yes wrangler -- pages deploy products/lci --project-name lci --commit-dirty=true`.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- **EROFS structural blocker for tick adversarial review**: `adversarial-review.sh` fails in tick/unattended sessions with `Failed to initialize session: Read-only file system (os error 30)`. Four reflection cycles; root cause uncharacterized. Attended sessions succeed. URGENT handoff proposed. Until resolved, every tick session ships without adversarial pressure.
- **Finding A (3 claims) unanchored at context-repo**: proposal doc committed in `664aba5` but no handoff written to context-repo session. Without an explicit handoff, the proposal will sit. Reflection P3: write `context-repo-canon-3claims-per-assumption-2026-04-24.md` handoff.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. Now emits explicit friction error to stderr. Source file needs reformat into canonical backtick key-value format.
- **migrate.py emits no telemetry**: 8 reflection cycles flagged this. Workspace rule requires structured telemetry for active runtime systems. No audit trail for migration runs. P2 proposal: 1 jsonl append per run with `{ project, source, eventType, level, timestamp, sourceType, counts }`. Carry-forward escalation threshold (3 cycles) exceeded — needs owner.

## Pending handoffs (in `.handoff/`)
- `general-skillfoundry-tally-form-needed-2026-04-18.md`: LCI deploy blocked on Tally form creation. Evan ~5 min manual step.
- `general-skillfoundry-agentic-inbound-root-scope-complete-2026-04-24T12-50Z.md`: completion report from root-scope verification session — all reversible work done, credential blockers remain.
- `general-skillfoundry-valuation-evidence-supports-fix-complete-2026-04-24T12-35Z.md`: confirmation that valuation polarity fix was already done at `39e5778`.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Canon adapter (2f63ae5): unknown enums raise `AdapterParseError`; probe closure only on `decision_kind="promote"`; Finding 3 ADR filed
- **Post-fix review triage (664aba5)**: Finding B fixed (pre-pass no longer swallows parse errors); Finding A proposal routed to context-repo (no code change); Finding C ADR accepted-pending-scheduling + interim rule added
- **ADR pure-parse-interface**: accepted, pending scheduling; new cross-file dependencies are ADR-class until refactor lands
- **CLAUDE.md rules landed (2026-04-20)**: advisor-gate and URL-verification rules added verbatim
- **pyproject.toml declared (2026-04-21)**: `jsonschema>=4.20` and `referencing>=0.30` — only 2 deps
- **Valuation evidence polarity (39e5778 2026-04-23)**: `weakens_assumption` → `contradicts_assumption`; "weakens not falsifies" nuance preserved in narrative body; schema gap routed to context-repo

## What bit recent sessions (reflection 2026-05-01T02-29-18Z)
- **EROFS blocks adversarial gate**: four consecutive reflection cycles. Every unattended session ships without adversarial pressure. Diagnosis proposed (mount/findmnt in tick context) but never executed.
- **CURRENT_STATE.md uncommitted for 7 days**: Apr 24 reflection updated it but no session committed it. Cold-start agents see 2026-04-23 tick state. Add hook or first-task rule to commit CURRENT_STATE.md after reflection writes.
- **Harness session idle**: session 42e3727c-f12d-45f3-90dd-0d6cb9abf327 received 3 handoff dispatcher messages Apr 30 but consumed no work — session may be waiting for human prompt. Pending handoffs (agentic-inbound, valuation-evidence-fix) are for `general` not `skillfoundry` — may have been dispatched in error.
- **migrate.py telemetry at 8 cycles**: workspace carry-forward escalation gate should have filed URGENT at cycle 3; either misfired or suppressed. Verify LATEST_SYNTHESIS.

## What the next agent must read first
1. **EROFS root cause** [CRITICAL, unblocks adversarial gate]: four cycles unresolved. Run `mount | grep -E ro` and `findmnt -R /root` in a tick-equivalent context. Compare to attended session environment. Without this, adversarial gate is structurally bypassed for all unattended sessions.
2. **Commit CURRENT_STATE.md** [HIGH, immediate]: `git add CURRENT_STATE.md && git commit -m "Update CURRENT_STATE: post-review-triage state, reflection 2026-04-24"` — been uncommitted since 2026-04-24T14:22Z.
3. **migrate.py telemetry** [HIGH, 8-cycle carry-forward]: workspace rule violation, escalation threshold met at cycle 3. Implement `{ project, source, eventType, level, timestamp, sourceType, counts }` append per run. No owner assigned.
4. **Finding A handoff to context-repo**: write `runtime/.handoff/context-repo-canon-3claims-per-assumption.md` — proposal doc at `docs/claims-per-assumption-options.md`. Harness preference: Option 1 > 3 > 2.
5. **ADR pure-parse-interface**: change status to `deferred-indefinite` or add a milestone condition. "Pending scheduling" with no schedule is misleading.
6. **preflight-distribution-signal.md reformat**: probe file uses prose/bold format; excluded from migration runs. Reformat to canonical backtick key-value to clear friction error.
