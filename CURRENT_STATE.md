# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-20T02-23-32Z — reflection pass

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 51/51 tests pass via `.venv/bin/python -m pytest tests/` (or unittest discover)
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Preflight Worker DEPLOYED** (2026-04-18): `https://preflight.skillfoundry.workers.dev/` — landing page + MCP endpoint + sourceType all live. Workers.dev subdomain: `skillfoundry`.
- **Blog DEPLOYED** (2026-04-18): `https://skillfoundry-blog.pages.dev/` — 3 posts live (one per probe). CF Pages project `skillfoundry-blog`.
- **LCI landing page DEPLOYED** (2026-04-18): LIVE at `https://lci.pages.dev/` — $99 pricing, Tally placeholder ("Intake form loading shortly"). Awaiting Tally embed code from Evan to complete. Escalation handoff written.
- **Watcher IGNORE_RE live** (2026-04-18): `preflight-watcher.service` restarted by Evan. Mozilla/Linux filtering active.
- **Preflight probe active through 2026-04-25**: activation metric MET (Apr 14 curl/8.5.0). Evidence quality: weak. Post-reclassification: 1 confirmed real user event, 188 Mozilla events correctly excluded.
- **Canon adapter SHIPPED** (2026-04-19 04:31 UTC): `discovery_adapter/` in commit `4d6050d`. Converts skillfoundry markdown → L1 discovery-framework envelopes. 51/51 tests pass. **Not pushed to origin yet.**

## Active probe status (as of 2026-04-18T12:45Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Blog post live. Render deploy pending (separate track).
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): landing page DEPLOYED at `https://lci.pages.dev/`. Blog post live. Tally embed placeholder live — escalation handoff written for Evan to create form.
- **Preflight** (`preflight-distribution-signal`): Worker deployed at `preflight.skillfoundry.workers.dev`. Landing page + sourceType + MCP endpoint all live. Blog post live. 1 confirmed real user (Apr 14).

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m pytest tests/` or `unittest discover tests/` from project root.
- **fly not installed**: cannot deploy launchpad-lint from this server. Render deploy on separate track.
- **LCI Tally form needed**: Landing page is LIVE at `lci.pages.dev` but shows "Intake form loading shortly." Evan must: (1) create Tally form at tally.so, (2) return embed code → swap `<!-- TALLY_EMBED -->` in `products/lci/index.html`, (3) agent runs `CLOUDFLARE_API_TOKEN=$(cat /root/.cloudflare-token) WRANGLER_HOME=/tmp/wrangler-home npm --cache /tmp/npm-cache exec --yes wrangler -- pages deploy products/lci --project-name lci --commit-dirty=true`.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- **pyproject.toml deps undeclared**: `jsonschema>=4.20`, `referencing>=0.30`, `pyyaml>=6.0` are in `.venv` but not in `[project.dependencies]`. Fresh clone → broken `discovery_adapter`. Commit `4d6050d` names this as known gap.
- **Canon adapter commit not pushed**: branch is 1 ahead of `origin/main`. Push required before any consumer can install from git.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. PM action item: reformat to canonical backtick-key-value header. Named in commit `4d6050d` message but not filed as tracked action.
- **/review not invoked** for 1,088-line canon adapter addition. Adversarial review is mandatory per CLAUDE.md for this class of change.
- **CURRENT_STATE.md uncommitted**: modified on disk, not at HEAD. Next user session: `git add CURRENT_STATE.md && git commit` before writing new state.
- **URGENT INBOX backlog**: 12 URGENT tick-escalation files accumulated (2026-04-19T02:47Z through 2026-04-20T00:47Z) plus proposals handoff — all unread. Executive session appears inactive. Total: 13 URGENT files in INBOX.
- ~~**CLAUDE.md proposals at 5-cycle carry-forward**~~ RESOLVED 2026-04-20: both rules landed verbatim in harness `CLAUDE.md` per executive handoff.

## Pending handoffs (in `.handoff/`)
- `general-skillfoundry-tally-form-needed-2026-04-18.md`: LCI deploy blocked on Tally form creation. Evan ~5 min manual step.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Probe outreach constraint was a design misread: FINRA constraint is on Evan personally, not on agent-operated inbound surfaces
- latencyMs = server processing time, NOT network round-trip — do not use for origin discrimination
- Mozilla/Linux UA proxy rule: conservative IGNORE_RE interim gate until sourceType deployed
- Evidence annotation added: reclassification note in 2026-04-14 evidence file (188 Mozilla events → IGNORED)
- CF deploy batch (2026-04-18): Preflight Worker + Blog + LCI all deployed
- wrangler deploy workaround: EROFS on `/root/.npm` and `/root/.config`; use `npm --cache /tmp/npm-cache exec --yes wrangler --` with `WRANGLER_HOME=/tmp/wrangler-home`
- 401 hook fix (cd2879d6): `$SUP` → `$WORKSPACE_SUPERVISOR_HANDOFF_INBOX`. Advisor caught the bug.
- Canon adapter (4d6050d): skillfoundry markdown → L1 discovery-framework envelopes. Additive. decision_type squeeze (`tighten/pause → continue`) is acknowledged lossy mapping — MAPPING.md documents it.
- **CLAUDE.md rules landed (2026-04-20)**: advisor-gate and URL-verification rules added verbatim to harness `CLAUDE.md` Active Decisions per executive handoff `skillfoundry-advisor-gate-and-url-verify-2026-04-20T13-11Z`. Closes 5-cycle carry-forward from reflection 2026-04-19T02:21:47Z (URGENT `URGENT-skillfoundry-harness-proposals-3cycle-2026-04-19T02-21-47Z.md`).

## What bit the last session
- **EROFS on `/root/.npm/_cacache`** — wrangler workaround required for all npm/npx invocations
- **CURRENT_STATE URL flip-flop** — session verified wrong URL (`lci.skillfoundry.pages.dev` vs `lci.pages.dev`). Rule: verify the exact URL from the completion report, not a guessed variant.
- **401 hook dead-code bug** (now fixed): tick runner used `$SUP` (undefined). Advisor caught it.
- **Adversarial review blocked**: `codex exec` fails with EROFS. Deployments and adapter shipped without `/review`.
- **pyproject.toml not updated**: new deps installed in venv but not declared — known gap named in commit message, not yet fixed.

## What the next agent must read first
1. **Process INBOX (executive action)**: 13 URGENT files in `/opt/workspace/supervisor/handoffs/INBOX/` — tick escalations + proposals handoff. Executive session must clear this before harness work can proceed.
2. **Commit CURRENT_STATE.md**: `git add CURRENT_STATE.md && git commit -m "Update CURRENT_STATE: reflection pass 2026-04-20"` before writing further state
3. **Fix pyproject.toml**: add `jsonschema>=4.20`, `referencing>=0.30`, `pyyaml>=6.0` to `[project.dependencies]`; add `pytest` to `[project.optional-dependencies.dev]`
4. **Push canon adapter**: `git push` — branch is 1 ahead of origin
5. **Run /review on discovery_adapter/**: adversarial review of emit.py + migrate.py + MAPPING.md
6. ~~**Decide on CLAUDE.md proposals**~~ DONE 2026-04-20 — advisor-gate + URL-verification rules landed in harness CLAUDE.md.
7. **LCI Tally form**: Evan creates form, returns embed code → redeploy
