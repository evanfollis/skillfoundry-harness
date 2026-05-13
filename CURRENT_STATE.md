# CURRENT_STATE — skillfoundry-harness

**Last updated**: 2026-05-13T14-19-48Z — reflection pass (cycle 28)

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

- **Finding A** (3 claims per assumption collapsed to 1): RESOLVED STEP 1. Context-repo spec authority issued verdict at `context-repo/1fcf0ad` (2026-05-07): Option 3 (loud MAPPING.md acknowledgment) immediately; Option 1 (3 envelopes via id-prefix) medium-term. Step 1 shipped at harness commit `81ea5b5` — MAPPING.md now names the collapse as "LOSSY by design choice" and names Option 1 as migration target. Step 2 awaits principal verdict on open questions — see `context-repository/docs/canon-3claims-per-assumption-verdict.md`. Finding A handoff (`general-context-repo-finding-a-complete-2026-05-07T12-38-05Z.md`) consumed by executive before 24h ADR-0020 deadline.
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
- **adversarial-review.sh PATH bug [CRITICAL, ~119h+, 71h PAST structural-blocker threshold]**: Codex IS installed at `/root/.nvm/versions/node/v22.22.0/bin/codex` (codex-cli 0.128.0). `adversarial-review.sh:42` fails because the unattended PATH omits NVM bin. Fix: Option B lookup chain in `adversarial-review.sh`. URGENT filed to executive: `URGENT-general-adversarial-review-path-fix-supervisor-2026-05-09T15-30Z.md`. Session 65447b9d proved the fix (ran real Codex review, 32,028 tokens). Crossed 48h structural-blocker threshold this window.
- **preflight-distribution-signal.md non-canonical**: probe file uses prose/bold format, excluded from migration runs. Emits explicit friction error to stderr. Source file needs reformat into canonical backtick key-value format — or a decision to leave it non-canonical must be documented. 14 cycles unresolved.
- **reflect.sh Write bypass unpatched [CRITICAL, ~277h+, TWO handoffs unconsumed since May 3 + May 12]**: Three confirmed exploitations: project repos (May 2, May 6) + supervisor HEAD advance (May 6 14:22Z, `2bdfdaf1`). `general-reflect-sh-write-bypass-fix-2026-05-12T04-49Z.md` written to `runtime/.handoff/` on May 12 04:49Z — 21h stale, no `.done`. Fix: one line in `supervisor/scripts/lib/reflect.sh:112` — add `"Write"` to `--disallowedTools`. Executive scope.
- **CURRENT_STATE.md HEAD/disk gap [STRUCTURAL, 12 cycles]**: Each reflection writes CURRENT_STATE.md but cannot commit. HEAD remains at cycle 15 (`3798d7d`, 2026-05-06T14:20:45Z). Disk now shows cycle 28. Cold-start sessions using `git show HEAD:CURRENT_STATE.md` get stale data. `general-reflect-sh-current-state-autocommit-2026-05-12T04-49Z.md` in `runtime/.handoff/` since May 12 04:49Z, unconsumed. Batch fix with reflect.sh Write bypass.
- **conftest.py Finding 2 [NEGLECTED COMMITMENT, 8 cycles]**: `tests/conftest.py:52` — `except Exception:` should be narrowed to `except (ImportError, ModuleNotFoundError):`. Called "safe to fix immediately, no ADR" since cycle 21. Still unactioned as of cycle 28. No dependency, no review required. Fix in next attended session before any other work.

## Pending handoffs (in `.handoff/`)
- `general-skillfoundry-tally-form-needed-2026-04-18.md`: LCI deploy blocked on Tally form creation. Evan ~5 min manual step.
- `general-skillfoundry-agentic-inbound-root-scope-complete-2026-04-24T12-50Z.md`: completion report from root-scope verification session — all reversible work done, credential blockers remain.
- `general-skillfoundry-valuation-evidence-supports-fix-complete-2026-04-24T12-35Z.md`: confirmation that valuation polarity fix was already done at `39e5778`.
- `general-skillfoundry-synthesis-test-telemetry-isolation-conftest-complete-2026-05-04T15-10Z.md`: conftest fix completion report — telemetry isolation shipped at `8fcf2d1`, adversarial review deferred.
- `general-context-repo-finding-a-complete-2026-05-07T12-38-05Z.md`: Finding A closure report — consumed by executive (`.done` marker present). Step 2 awaits principal verdict on Q1/Q2.

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
- **Finding A (3 claims) Step 1 (81ea5b5, 2026-05-07)**: context-repo spec authority verdict applied. MAPPING.md now explicitly names partial-thesis collapse as "LOSSY by design choice." Migration target: Option 1 (id-prefix `<assumption_id>:problem|economic|channel`). Step 2 on hold pending principal verdict.

## What bit recent sessions (reflection 2026-05-13T14-19-48Z, cycle 28)
- **Quiet window (cycle 28)**: No commits, no human-attended harness sessions. Only JSONL activity is current reflection job (5165b159, 14:19Z).
- **Infrastructure handoff consumption remains zero**: Three URGENT executive-scope handoffs unconsumed: write-bypass (May 3, ~240h+), mutated-head (May 6, ~192h+), adversarial-review PATH (May 9, ~119h+). 4 consecutive cycles with no infrastructure repair uptake.
- **adversarial-review.sh URGENT in runtime/.handoff/ since May 9T15:30Z**: Unconsumed. ~119h+ past filing, 71h past 48h structural-blocker threshold.
- **conftest Finding 2 now 8 cycles unactioned**: Zero new rationale. Eight consecutive deferral cycles with no attended harness sessions.
- **reflect.sh Write bypass now ~277h+**: TWO handoffs written (URGENT-reflect-sh-write-bypass-2026-05-03T15-23Z.md from May 3, and general-reflect-sh-write-bypass-fix-2026-05-12T04-49Z.md from May 12). Neither consumed. Highest-leverage unpatched gap in workspace.

## What the next agent must read first
1. **conftest Codex Finding 2 (neglected commitment, 8 cycles)**: `tests/conftest.py:52` — `except Exception:` -> `except (ImportError, ModuleNotFoundError):`. No ADR, no review, no dependency. Fix it before anything else.
2. **reflect.sh Write bypass handoffs** [CRITICAL, ~277h+]: TWO files — `URGENT-reflect-sh-write-bypass-2026-05-03T15-23Z.md` (May 3 original, 10 days old) AND `general-reflect-sh-write-bypass-fix-2026-05-12T04-49Z.md` (May 12). Fix: `supervisor/scripts/lib/reflect.sh:112` — add `"Write"` to `--disallowedTools`. Executive scope. Consume one, archive the other.
3. **adversarial-review.sh PATH fix** [CRITICAL, ~119h+, 71h past structural-blocker]: `URGENT-general-adversarial-review-path-fix-supervisor-2026-05-09T15-30Z.md`. NVM glob lookup chain. Executive scope.
4. **runtime/.handoff/ infrastructure handoffs systematically de-prioritized**: 4 consecutive cycles. 3 URGENT items from May 3/6/9 all unconsumed. Product-visible handoffs consumed same-day. Prioritization failure, not format failure.
5. **Context-repo Finding A Step 2**: Awaits principal verdict from `context-repository/docs/canon-3claims-per-assumption-verdict.md`.
6. **preflight-distribution-signal.md decision**: 15 cycles. Reformat (5 min) or document non-canonical by intent.