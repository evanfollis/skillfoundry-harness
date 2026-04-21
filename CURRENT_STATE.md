# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-21T00-57-20Z — tick (pyproject fix + push)

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
- **Canon adapter SHIPPED + PUSHED** (2026-04-21): `discovery_adapter/` commits `4d6050d` + `b8a724f` + `5ad37e7` all at origin/main. Converts skillfoundry markdown → L1 discovery-framework envelopes. 51/51 tests pass.

## Active probe status (as of 2026-04-18T12:45Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Blog post live. Render deploy pending (separate track).
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): landing page DEPLOYED at `https://lci.pages.dev/`. Blog post live. Tally embed placeholder live — escalation handoff written for Evan to create form.
- **Preflight** (`preflight-distribution-signal`): Worker deployed at `preflight.skillfoundry.workers.dev`. Landing page + sourceType + MCP endpoint all live. Blog post live. 1 confirmed real user (Apr 14).

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m pytest tests/` or `unittest discover tests/` from project root.
- **fly not installed**: cannot deploy launchpad-lint from this server. Render deploy on separate track.
- **LCI Tally form needed**: Landing page is LIVE at `lci.pages.dev` but shows "Intake form loading shortly." Evan must: (1) create Tally form at tally.so, (2) return embed code → swap `<!-- TALLY_EMBED -->` in `products/lci/index.html`, (3) agent runs `CLOUDFLARE_API_TOKEN=$(cat /root/.cloudflare-token) WRANGLER_HOME=/tmp/wrangler-home npm --cache /tmp/npm-cache exec --yes wrangler -- pages deploy products/lci --project-name lci --commit-dirty=true`.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- **STRUCTURAL: codex exec EROFS** — adversarial review for discovery_adapter (mandatory per harness CLAUDE.md) is blocked on every session. `codex exec` fails with EROFS at session init. `adversarial-review.sh` wraps codex and inherits the failure. This is not transient; it has persisted across 3+ ticks. Executive must resolve or authorize alternative review path.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. PM action item: reformat to canonical backtick-key-value header. Named in commit `4d6050d` message but not filed as tracked action.

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
- **CLAUDE.md rules landed (2026-04-20)**: advisor-gate and URL-verification rules added verbatim to harness `CLAUDE.md` Active Decisions per executive handoff.
- **pyproject.toml declared (2026-04-21)**: `jsonschema>=4.20` and `referencing>=0.30` added. `pyyaml` was incorrectly listed in CURRENT_STATE — it has no import anywhere in the package. Only 2 deps needed, not 3.

## What bit the last session (2026-04-21T00-57-20Z)
- **pyyaml false positive**: CURRENT_STATE.md claimed pyyaml was needed. Grep confirmed it is not imported anywhere. Only jsonschema + referencing are real deps.
- **EROFS still structural**: `codex exec` fails at session init (cannot write models cache). `adversarial-review.sh` wraps codex and inherits the same failure. Not fixable at the project level.
- **Tick instructions vs acceptance criteria conflict**: Tick instructions said write review to `/opt/workspace/supervisor/.reviews/<project>-<slug>-*.md`; handoff acceptance criteria said `.reviews/<commit>-discovery-adapter-*.md` in the harness repo. Chose the handoff location (more specific, it's what acceptance criteria checks).

## What the next agent must read first
1. **EROFS adversarial review** is a structural blocker — executive must resolve. Review for discovery_adapter (>48h overdue) cannot proceed until codex can write its models cache. Do not attempt to re-run `adversarial-review.sh`; it will fail the same way.
2. **LCI Tally form**: Evan creates form, returns embed code → redeploy.
3. **preflight-distribution-signal.md reformat**: still untracked — file a handoff or track it explicitly.
4. All commits are at origin/main as of 2026-04-21. Branch is clean.
