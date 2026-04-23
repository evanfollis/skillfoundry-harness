# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-21T14-19-49Z — reflection pass

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
- **Canon adapter SHIPPED + PUSHED + REVIEWED** (2026-04-21 / 2026-04-23): `discovery_adapter/` all commits at origin/main. Converts skillfoundry markdown → L1 discovery-framework envelopes. 51/51 tests pass. Adversarial review completed 2026-04-23 via `adversarial-review.sh` against `src/skillfoundry_harness/discovery_adapter/` — artifact at `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md`. EROFS blocker was not reproducible today; either transient or resolved. Three substantive findings pending principal verdict (see Known broken).

## Active probe status (as of 2026-04-18T12:45Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Blog post live. Render deploy pending (separate track).
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): landing page DEPLOYED at `https://lci.pages.dev/`. Blog post live. Tally embed placeholder live — escalation handoff written for Evan to create form.
- **Preflight** (`preflight-distribution-signal`): Worker deployed at `preflight.skillfoundry.workers.dev`. Landing page + sourceType + MCP endpoint all live. Blog post live. 1 confirmed real user (Apr 14).

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m pytest tests/` or `unittest discover tests/` from project root.
- **fly not installed**: cannot deploy launchpad-lint from this server. Render deploy on separate track.
- **LCI Tally form needed**: Landing page is LIVE at `lci.pages.dev` but shows "Intake form loading shortly." Evan must: (1) create Tally form at tally.so, (2) return embed code → swap `<!-- TALLY_EMBED -->` in `products/lci/index.html`, (3) agent runs `CLOUDFLARE_API_TOKEN=$(cat /root/.cloudflare-token) WRANGLER_HOME=/tmp/wrangler-home npm --cache /tmp/npm-cache exec --yes wrangler -- pages deploy products/lci --project-name lci --commit-dirty=true`.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- ~~**STRUCTURAL: codex exec EROFS — 6 ticks, URGENT escalated**~~ EMPIRICALLY RESOLVED 2026-04-23: `adversarial-review.sh` ran discovery_adapter review end-to-end (codex returned 99,902 tokens, artifact saved to `.reviews/`). Prior reflections reported EROFS as structural across 6 ticks; today's invocation succeeded without special workaround. Root cause of the intermittency not characterized — could be host-state change, transient cache condition, or per-session environment variance. If a future session hits EROFS again, capture the error text verbatim in CURRENT_STATE so the pattern can be diagnosed rather than generalized from one failure. Related URGENT handoff deleted.
- **Adversarial review findings pending verdict (2026-04-23)**: review of `src/skillfoundry_harness/discovery_adapter/` flagged three issues:
  1. `parse_probe()` emits `promotion` phase transition on any closed probe regardless of Decision — silent semantic corruption;
  2. Unknown enums silently coerce to plausible defaults (`evidence_class → internal_operational`, `supports → neutral`, `decision_type → continue`) — adapter emits valid-looking lies on authoring drift;
  3. Adapter couples to filesystem mtime/layout of valuation-context rather than a stable boundary.
  Principal decision needed: address in code vs explicitly accept. Review artifact: `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md`.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. Untracked PM action item — no handoff written yet.
- **migrate.py emits no telemetry**: 5 reflection cycles flagged this. Workspace rule requires structured telemetry for active runtime systems. No audit trail for migration runs.

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

## What bit the last session (f83b96c3, tick 2026-04-21T00-57-20Z)
- **pyyaml false positive**: CURRENT_STATE.md claimed pyyaml was needed. Grep confirmed it is not imported anywhere. Only jsonschema + referencing are real deps. Advisor guidance to grep before assuming was followed correctly.
- **EROFS still structural**: `codex exec` fails at session init (cannot write models cache). `adversarial-review.sh` wraps codex and inherits the same failure. Not fixable at the project level. URGENT handoff written this reflection pass.
- **Tick instructions vs acceptance criteria conflict (prior session)**: Tick instructions said write review to supervisor path; handoff acceptance criteria said harness `.reviews/`. Chose handoff location (more specific).

## What the next agent must read first
1. **Adversarial review findings — principal verdict needed**: 3 findings in `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md` (phase-progression bug, enum silent coercion, filesystem coupling). Decide address-in-code vs accept before treating adapter as settled.
2. **LCI Tally form**: Evan creates form, returns embed code → redeploy.
3. **preflight-distribution-signal.md reformat**: write a PM handoff — currently untracked.
4. **migrate.py telemetry**: 5 cycles flagged, still unimplemented. Add one jsonl append per run.
5. **EROFS watch**: prior reflections claimed `adversarial-review.sh` was structurally blocked; it ran fine today. If a future invocation fails, capture stderr verbatim — don't generalize from a single historical failure.
