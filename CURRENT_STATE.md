# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-17T16-44-08Z — preflight sourceType tick

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 39/39 tests pass via `.venv/bin/python -m unittest discover tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Both commercial probes stalled on human action**: probes are running but require Evan to initiate external contact. Agents cannot do this.
  - Launch Compliance Intelligence: 10 drafts ready, none sent. Evan must send first message.
  - Launchpad Lint: passive listing, no external interactions. Evan must promote in MCP builder communities.
- **Preflight probe active through 2026-04-25**: activation metric MET (1 qualifying user on Apr 14), probe continues. Evidence quality: weak.
- **Preflight now emits `sourceType` (S1-P2 satisfied)**: as of 4907d26, all MCP handler telemetry events carry `sourceType`. Defaults to `"user"`; automated callers self-identify via `X-Source-Type` request header.

## Active probe status (as of 2026-04-17T16-44-08Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, runtime healthy. No external builder interactions.
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): 10 outreach drafts ready. None sent.
- **Preflight** (`preflight-distribution-signal`): Activation metric MET. Slug IDs aligned as of 2026-04-17T09:16:26Z. Service now emits `sourceType` per S1-P2.

## Known broken or degraded
- **Tests require the venv**: `python` not available globally; use `.venv/bin/python -m unittest discover tests/` from project root.
- **401 auth failure mitigation absent**: Tick sessions that fail with 401 exit silently. No escalation hook in tick runner. Flagged in 3+ consecutive reflection cycles — carry-forward escalation threshold MET. URGENT.
- **Pre-fix slug in evidence raw body**: `2026-04-14-preflight-first-real-user-call.md` body contains `"probeId": "preflight-publish-readiness"` (historical pre-fix value). Canonical `probe_id` header is correct. Annotation needed.
- **Watcher misclassifying 161/162 sessions as REAL-USER**: all Mozilla/0ms loopback traffic counted as external. Handoff `skillfoundry-valuation-watcher-signal-discrimination-2026-04-17T15-30Z.md` unexecuted — targets `skillfoundry-products` watcher, out of harness boundary for this tick. Needs dedicated tick.

## Pending handoffs (not executed this tick — boundary/scope blocked)
- `skillfoundry-valuation-watcher-signal-discrimination-2026-04-17T15-30Z.md`: HIGH priority. Fix watcher classification logic in `skillfoundry-products`. Left in place.
- `skillfoundry-activate-agentic-inbound-2026-04-17T14-55Z.md`: HIGH priority, large scope. Build landing pages, blog posts, personas for all 3 probes. Spans multiple repos and external systems. Left in place for general session routing.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Absence of signal is not typed evidence — record evidence gaps in `memory/findings/`, not `memory/venture/evidence/`
- Preflight real-user signal (Apr 14) is `external_conversation / weak` evidence — recorded in valuation-context
- Watcher slug alignment: venture files are the truth source; watcher config conforms to them (not the reverse)
- Tick sessions that cross repo boundary (valuation-context, products) should note boundary override in completion report — established precedent, not yet formalized
- S1-P2 (`sourceType`) is now live in preflight: `"user"` default, `X-Source-Type` header override for automated callers

## What bit this session
- Preflight code lives in `skillfoundry-products/products/preflight/`, not in the harness. The handoff referenced `tools/preflight/` which doesn't exist. Required boundary override with noted precedent.
- No test suite for preflight TypeScript — only typecheck available. No way to verify runtime behavior without deploying.
- Two high-priority handoffs arrived mid-tick but are out of harness boundary scope. Filed as pending above.

## What the next agent must read first
1. Run tests: `.venv/bin/python -m unittest discover -v tests/` from project root
2. 401 escalation URGENT: write handoff to `supervisor/handoffs/INBOX/` — carry-forward threshold met 3+ cycles
3. Watcher discrimination: `skillfoundry-valuation-watcher-signal-discrimination-2026-04-17T15-30Z.md` in `.handoff/` — HIGH priority, needs execution
4. Agentic inbound: `skillfoundry-activate-agentic-inbound-2026-04-17T14-55Z.md` in `.handoff/` — HIGH priority, large scope, general session to route
5. Evidence annotation needed: `skillfoundry-valuation-context/memory/venture/evidence/2026-04-14-preflight-first-real-user-call.md` — add raw-slug-mismatch note
6. Preflight service NOT redeployed this tick — `sourceType` change is code_landed but not deployed. Deployment step: `npm run deploy` from `skillfoundry-products/products/preflight/` (runs `wrangler deploy`) or via the project deploy script.
