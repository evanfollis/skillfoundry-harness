# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-05-06T14-20-45Z — reflection pass

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 61/61 tests pass via `.venv/bin/python -m pytest tests/` (`8fcf2d1` added conftest.py telemetry isolation)
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
- **EROFS / codex-not-installed scope expanded [CRITICAL, cycle 14]**: `adversarial-review.sh` fails with "codex not installed" in both unattended tick sessions AND attended sessions (session `65447b9d` 2026-05-04 03:34Z was Evan-initiated and still hit this). Fourteen consecutive reflection cycles without adversarial review. Root cause undiagnosed. No attended diagnosis has been attempted.
- **Finding A (3 claims) unanchored at context-repo**: proposal doc committed in `664aba5` but no handoff written to context-repo session. 14+ days deferred.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. Now emits explicit friction error to stderr. Source file needs reformat into canonical backtick key-value format.
- **CURRENT_STATE.md uncommitted [cycle 14]**: on-disk version diverges from HEAD. Cold-start sessions read HEAD; stale as of 2026-05-05T02:21Z. URGENT queue items consuming this list for 4+ cycles.

## Pending handoffs (in `.handoff/`)
- `general-skillfoundry-tally-form-needed-2026-04-18.md`: LCI deploy blocked on Tally form creation. Evan ~5 min manual step.
- `general-skillfoundry-agentic-inbound-root-scope-complete-2026-04-24T12-50Z.md`: completion report from root-scope verification session — all reversible work done, credential blockers remain.
- `general-skillfoundry-valuation-evidence-supports-fix-complete-2026-04-24T12-35Z.md`: confirmation that valuation polarity fix was already done at `39e5778`.
- `general-skillfoundry-synthesis-test-telemetry-isolation-conftest-complete-2026-05-04T15-10Z.md`: conftest fix completion report — telemetry isolation shipped at `8fcf2d1`, adversarial review deferred.

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
- **migrate.py telemetry wired (531946f, 2026-05-03)**: 12-cycle URGENT resolved. `_emit_telemetry` emits S1-P2 events per run (success + all failure paths). `--source-type` CLI flag for cron self-classification. Tests: 61/61.
- **Test telemetry isolation (8fcf2d1, 2026-05-04)**: conftest.py autouse fixture (synthesis Proposal 5b). Two-layer fix: env var + module-level constant (`migrate.TELEMETRY_PATH`). Env-var-only was confirmed insufficient (import-time binding). 61/61. No-pollution check verified.

## What bit recent sessions (reflection 2026-05-06T14-20-45Z)
- **No human-initiated sessions this window** (02:23Z–14:20Z): only automated reflection sessions. No new bugs, no new fixes.
- **Write-tool bypass still unpatched (cycle 15)**: `URGENT-reflect-sh-write-bypass-2026-05-03T15-23Z.md` is now 84h old. Fix is one line in `reflect.sh:112`. Exploit confirmed live in supervisor repo; continues to apply every 12h.
- **URGENT queue all FR-class (cycle 15)**: `URGENT-reflect-sh-write-bypass` (84h+), `URGENT-supervisor-reflection-mutated-head` (83h+), `URGENT-supervisor-reflection-dirty-tree` (12h). None consumed.
- **Carry-forward items FR-class (cycle 15)**: EROFS/codex and CURRENT_STATE uncommitted both 15 cycles without fix, decision, or verified pointer.

## What the next agent must read first
1. **reflect.sh Write patch** [CRITICAL, 84h+]: `URGENT-reflect-sh-write-bypass-2026-05-03T15-23Z.md`. Fix: `reflect.sh:112` — add `"Write"` to `--disallowedTools`. Mark URGENT `.done` after applying.
2. **EROFS / codex root cause** [CRITICAL, cycle 15]: Run `which codex` in attended session. 15 cycles of adversarial review missing. If absent: document decision to use Claude-based `/review` fallback in `supervisor/decisions/`.
3. **Commit CURRENT_STATE.md** [HIGH, immediate]: `git add CURRENT_STATE.md && git commit -m "Update CURRENT_STATE: reflection cycle 15"` — unstaged for 15+ consecutive windows.
4. **Triage URGENT queue**: Read `URGENT-supervisor-reflection-mutated-head.md` + `URGENT-supervisor-reflection-dirty-tree.md`. If deprioritizing, record decision in `supervisor/decisions/`.
5. **Finding A handoff to context-repo**: write `runtime/.handoff/context-repo-canon-3claims-per-assumption-2026-05-06.md` — 14+ days deferred, proposal doc at `docs/claims-per-assumption-options.md`.
