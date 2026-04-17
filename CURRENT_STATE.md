# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-04-17T20-38Z — agentic inbound tick

---

## Deployed / running state
- **Type**: multi-agent harness for building products (Python)
- **Runtime**: tested — 39/39 tests pass via `.venv/bin/python -m unittest discover tests/`
- **Entry**: `src/skillfoundry_harness/` — CLI via `skillfoundry` command (pyproject.toml)

## What's in progress
- **Agentic inbound scaffolded**: All 3 probes have persona definitions, landing page content specs, blog queues, video scripts, telemetry channel specs in `skillfoundry-valuation-context/memory/venture/activation/`. None deployed — blocked on Evan's credentials.
- **Preflight landing page code_landed** (8e9bf50): GET `/` route with full SEO-optimized HTML added to `products/preflight/src/index.ts`. NOT DEPLOYED — requires `wrangler deploy`.
- **Watcher IGNORE_RE fixed** (8e9bf50): Mozilla/Linux added to IGNORE_RE, sourceType gate added. Service not restarted — needs `systemctl restart preflight-watcher`.
- **Preflight probe active through 2026-04-25**: activation metric MET (Apr 14 curl/8.5.0). Evidence quality: weak. Post-reclassification: 1 confirmed real user event, 188 Mozilla events correctly excluded.
- **sourceType code_landed**: still not deployed (4907d26). All telemetry events still lack sourceType field.

## Active probe status (as of 2026-04-17T20:38Z)
- **Launchpad Lint** (`launchpad-lint-agenticmarket-live-listing`): listing live, no external interactions. Activation spec: `memory/venture/activation/launchpad-lint-inbound-activation.md`.
- **Launch Compliance Intelligence** (`launch-compliance-intelligence-manual-offer`): no product infra. Requires Evan: intake form tool + price + hosting path. Spec: `memory/venture/activation/launch-compliance-intelligence-inbound-activation.md`.
- **Preflight** (`preflight-distribution-signal`): landing page code_landed, not deployed. 1 confirmed real user. Spec: `memory/venture/activation/preflight-inbound-activation.md`.

## Known broken or degraded
- **Tests require the venv**: use `.venv/bin/python -m unittest discover tests/` from project root.
- **wrangler not installed**: cannot deploy preflight from this server. Blocking landing page + sourceType.
- **fly not installed**: cannot deploy launchpad-lint from this server.
- **Watcher restart pending**: IGNORE_RE fix is in code but `preflight-watcher.service` not restarted.
- **latencyMs misunderstood**: `latencyMs` measures server processing time, NOT network round-trip. ADR-0019 latency-floor heuristic is wrong. See evidence reclassification in valuation-context.
- **Pre-fix slug in evidence raw body**: `2026-04-14-preflight-first-real-user-call.md` raw log emits `probeId: preflight-publish-readiness`. Canonical `probe_id` header is correct. Reclassification note now added to the file.

## Pending handoffs (in `.handoff/`)
- `skillfoundry-valuation-watcher-signal-discrimination-2026-04-17T15-30Z.md`: partially executed this tick (IGNORE_RE fix committed), but service restart pending. Watcher investigation complete (see evidence file). This handoff can be deleted — the remaining item (service restart) is noted in general escalation.
- `general-skillfoundry-agentic-inbound-credential-escalation-2026-04-17T20-38Z.md`: NEW — precise credential blockers table for all 3 probes. Targeted at general session.

## Recent decisions
- Six agent roles are fixed (builder, designer, growth, pricing, researcher, valuation)
- Context lineages are append-forward
- Keep harness generic — no business-specific ontology in runtime semantics
- Probe outreach constraint was a design misread: FINRA constraint is on Evan personally, not on agent-operated inbound surfaces (landing pages, content, personas)
- latencyMs = server processing time, NOT network round-trip — do not use for origin discrimination
- Mozilla/Linux UA proxy rule: conservative IGNORE_RE interim gate until sourceType deployed
- Evidence annotation added: reclassification note in 2026-04-14 evidence file (188 Mozilla events → IGNORED)

## What bit this session
- No TypeScript test suite for preflight — only typecheck available. Can verify compilation but not runtime behavior.
- wrangler and fly not installed on server — all deployment blocked on Evan's credentials.
- Adversarial review blocked: `codex exec` fails with EROFS (read-only file system, FR-0021). Not skipped — attempted and blocked.
- latencyMs premise in ADR-0019 and the watcher handoff was wrong. Discovered during investigation; corrected in both the fix and the evidence file.

## What the next agent must read first
1. Run tests: `.venv/bin/python -m unittest discover -v tests/` from project root
2. Read `general-skillfoundry-agentic-inbound-credential-escalation-2026-04-17T20-38Z.md` in `.handoff/` — routing needed
3. Credential gap: Evan must run `wrangler deploy` from products/preflight to land landing page + sourceType
4. `memory/venture/activation/` in valuation-context — per-probe inbound specs, all code_ready or spec_ready
5. Watcher handoff (`skillfoundry-valuation-watcher-signal-discrimination-2026-04-17T15-30Z.md`) — can be deleted; work executed, remaining item is service restart (in escalation)
