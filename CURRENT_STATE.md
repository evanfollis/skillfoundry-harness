# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-23T17-37-15Z — tick session (discovery adapter fixes)

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 58/58 tests pass via `.venv/bin/python -m pytest tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Preflight Worker DEPLOYED** (2026-04-18): `https://preflight.skillfoundry.workers.dev/` — landing page + MCP endpoint + sourceType all live. Workers.dev subdomain: `skillfoundry`.
- **Blog DEPLOYED** (2026-04-18): `https://skillfoundry-blog.pages.dev/` — 3 posts live (one per probe). CF Pages project `skillfoundry-blog`.
- **LCI landing page DEPLOYED** (2026-04-18): LIVE at `https://lci.pages.dev/` — $99 pricing, Tally placeholder ("Intake form loading shortly"). Awaiting Tally embed code from Evan to complete. Escalation handoff written.
- **Watcher IGNORE_RE live** (2026-04-18): `preflight-watcher.service` restarted by Evan. Mozilla/Linux filtering active.
- **Preflight probe active through 2026-04-25**: activation metric MET (Apr 14 curl/8.5.0). Evidence quality: weak. Post-reclassification: 1 confirmed real user event, 188 Mozilla events correctly excluded.
- **Canon adapter FIXED + PUSHED** (2026-04-23 tick 17-37-15Z): `discovery_adapter/` 3 correctness bugs fixed at commit `2f63ae5`. See below.

## Canon adapter — fix status (2026-04-23)

All 3 adversarial-review findings from `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md` addressed:

1. **Finding 1 FIXED** (`parse_probe` phase bug): Closure event (probe→promotion) now only emits when `decision_kind="promote"` is passed by caller. `migrate.py` pre-pass builds probe_id→decision_kind map. Killed/pivoted probes produce no spurious promotion events.

2. **Finding 2 FIXED** (enum silent coercion): Unknown `evidence_class`, `supports`, and `decision_type` values now raise `AdapterParseError` instead of defaulting. `operational_readiness_only→neutral` alias added (unambiguous). `weakens_assumption` left as error — needs valuation-context source fix (handoff written).

3. **Finding 3 SPLIT** (filesystem coupling): ADR filed at `docs/adr-discovery-adapter-pure-parse-interface.md`. Structural refactor deferred. No defensive code change (partial measures add surface without reducing coupling; the ADR is the actionable artifact).

Backfill re-run on valuation-context:
- Before: 14 envelopes (2 evidence with silently-coerced wrong polarity)
- After: 13 OK envelopes + 1 stale (see below) + 2 friction events logged to stderr
- `2026-04-25-preflight-probe-close.json` stale in valuation-context/.canon/ (source has `weakens_assumption`; migrate.py doesn't prune; needs valuation-context session to fix source + re-run)

## Active probe status (as of 2026-04-18T12:45Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Blog post live. Render deploy pending (separate track).
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): landing page DEPLOYED at `https://lci.pages.dev/`. Blog post live. Tally embed placeholder live — escalation handoff written for Evan to create form.
- **Preflight** (`preflight-distribution-signal`): Worker deployed at `preflight.skillfoundry.workers.dev`. Landing page + sourceType + MCP endpoint all live. Blog post live. 1 confirmed real user (Apr 14).

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m pytest tests/` from project root.
- **fly not installed**: cannot deploy launchpad-lint from this server. Render deploy on separate track.
- **LCI Tally form needed**: Landing page is LIVE at `lci.pages.dev` but shows "Intake form loading shortly." Evan must: (1) create Tally form at tally.so, (2) return embed code → swap `<!-- TALLY_EMBED -->` in `products/lci/index.html`, (3) agent runs `CLOUDFLARE_API_TOKEN=$(cat /root/.cloudflare-token) WRANGLER_HOME=/tmp/wrangler-home npm --cache /tmp/npm-cache exec --yes wrangler -- pages deploy products/lci --project-name lci --commit-dirty=true`.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- **EROFS intermittent**: `adversarial-review.sh` failed at session 17-37-15Z with EROFS. Previously succeeded in the 2026-04-23 morning session. Root cause still uncharacterized. Capture error verbatim if it recurs. Error text this session: `Failed to initialize session: Read-only file system (os error 30)`.
- **`2026-04-25-preflight-probe-close.json` stale**: valuation-context `.canon/evidence/` has this file from before the fixing session. Source file uses `weakens_assumption` polarity (non-canonical). Valuation-context session must fix source + re-run migrate. Handoff written: `general-skillfoundry-valuation-evidence-fix-2026-04-23T17-37-15Z.md`.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. Now emits explicit friction error to stderr. Source file needs reformat into canonical backtick key-value format.
- **migrate.py emits no telemetry**: 6 reflection cycles flagged this. Workspace rule requires structured telemetry for active runtime systems. No audit trail for migration runs.
- **Agentic inbound deploy**: primary tick task (skillfoundry-agentic-inbound-deploy) was escalated — requires cross-repo edits to `skillfoundry-products` that this session cannot make. Escalation at `general-skillfoundry-inbound-escalation-2026-04-23T17-37-15Z.md`.

## Pending handoffs (in `.handoff/`)
- `general-skillfoundry-tally-form-needed-2026-04-18.md`: LCI deploy blocked on Tally form creation. Evan ~5 min manual step.
- `general-skillfoundry-valuation-evidence-fix-2026-04-23T17-37-15Z.md`: valuation-context evidence file has `weakens_assumption` polarity. Needs domain decision (contradicts vs neutral) + source fix + backfill re-run.
- `general-skillfoundry-inbound-escalation-2026-04-23T17-37-15Z.md`: agentic inbound deploy requires cross-repo authority this session doesn't have.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Canon adapter (2f63ae5): unknown enums raise `AdapterParseError`; probe closure only on `decision_kind="promote"`; Finding 3 ADR filed
- **CLAUDE.md rules landed (2026-04-20)**: advisor-gate and URL-verification rules added verbatim
- **pyproject.toml declared (2026-04-21)**: `jsonschema>=4.20` and `referencing>=0.30` — only 2 deps

## What bit this session (tick 2026-04-23T17-37-15Z)
- **Boundary conflict with primary tick task**: agentic-inbound-deploy requires editing `skillfoundry-products` and `skillfoundry-valuation-context` — both out of scope for harness session. Escalated cleanly.
- **EROFS intermittent again**: adversarial review blocked. Second known occurrence (first resolved on its own earlier today). Still no root cause.
- **`weakens_assumption` is a real semantic gap**: the valuation-context author used a polarity that's not in the canon model. Neither "contradicts" nor "neutral" is obviously correct without domain context. Left as error, wrote handoff.

## What the next agent must read first
1. **Stale evidence envelope**: `valuation-context/.canon/evidence/2026-04-25-preflight-probe-close.json` has coerced-neutral polarity from before the fix. Needs valuation-context session to decide `weakens_assumption` → (contradicts|neutral), fix source, re-run migrate.
2. **Adversarial review still needed for 2f63ae5**: EROFS blocked this session. The 3-finding fix landed without adversarial pressure on the diff. Flag for next session that hits codex without EROFS.
3. **Agentic inbound deploy**: escalated to general. Needs re-routing to a session with cross-repo authority or explicit boundary relaxation.
4. **migrate.py telemetry**: 6 cycles flagged, still unimplemented. Add one jsonl append per run.
5. **preflight-distribution-signal.md reformat**: still untracked PM item.
