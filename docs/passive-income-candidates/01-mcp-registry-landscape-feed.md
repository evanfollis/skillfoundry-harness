# Candidate: MCP Registry Landscape Feed (data/API product, sleeve = data/API)

**Date**: 2026-05-21
**Author**: skillfoundry session, 65447b9d-3cb7-4584-bcf2-c058fd025791
**Sleeve**: Data/API products (ADR-0033)
**Source synthesis**: `/opt/workspace/runtime/.handoff/skillfoundry-passive-income-portfolio-update-2026-05-21.md`

---

## What it is

A periodic, machine-readable feed of agent-platform landscape signals derived from Skillfoundry's existing harvest pipeline:

- new MCP server listings across AgenticMarket, Smithery, and GitHub
- churned / disappeared listings
- creator-concentration shifts (e.g. "AgenticMarket-direct listings down 30% MoM")
- per-creator activity deltas (which builders are shipping, which are dormant)
- aggregate stats: listing count by platform, growth rate by source, repeat-creator rate

Distribution shape: paid API endpoint (`/v1/landscape/diff?since=YYYY-MM-DD`), per-request payment via x402 or subscription via RapidAPI, downloadable historical archive.

## Why this is the first candidate (vs. the others ADR-0033 names)

The portfolio strategy doc names four candidate types for the data/API sleeve: marketplace diffs, launch-readiness metadata, compliance feeds, structured observations. **All four would be speculative new products if proposed cold.** Marketplace diffs is the only one where Skillfoundry already has:

1. **Working harvest pipeline code** at `skillfoundry-researcher-context/scripts/` and elsewhere (the `19281a7` "Wire automated foundry loop: harvest → enrich → score → draft outreach" commit). Pulls from `agenticmarket-sitemap`, `smithery-registry`, `github-mcp-repos`.
2. **One baseline snapshot** at `memory/reports/launch_compliance_harvest_report.md` dated `2026-04-11T20:58:58Z`. 101 targets, 3 sources, creator concentration distribution.
3. **Concrete output schema** demonstrated by 28 enriched target profiles in `memory/signals/target_profiles/`. Machine-readable, hash-bound dossiers.

A diff product requires `N+1` snapshots. We have one. The path from one to two is "schedule the existing pipeline to re-run." That's tractable; the other three candidate types in the strategy doc would require new sourcing pipelines.

## What is grounded vs. what is speculation (read this first)

### Grounded

- Harvest pipeline code exists and produced one successful run.
- 3 source surfaces are validated (no errors in `launch_compliance_harvest_report.md` §Errors).
- 101-target snapshot proves the output shape and validates that 3 sources merge cleanly.
- Creator concentration distribution (13 agenticmarket + 8 unattributed + long tail of 1-target creators) confirms a real long-tail builder market exists — the underlying market shape that would make landscape signals interesting.

### Speculation (named honestly so it's not buried)

- **Re-harvest cadence not proven**. The pipeline ran once on 2026-04-11 and not since (40+ days). Whether a daily/weekly cadence produces stable output is untested. Source rate-limits (especially GitHub's 30 req/min unauthenticated) may break a daily schedule.
- **Diff layer doesn't exist yet**. The current harvest emits a snapshot, not a diff between snapshots. The diff layer is the actual product surface and is not built.
- **No buyer signal**. Zero builder has asked for this feed. The closest validation is that competitive intelligence products in adjacent markets (`SimilarWeb`, `Crunchbase`, `BuiltWith`) do sell well — but that's analogy, not signal.
- **Pricing unknown**. x402 micro-pricing per request is a guess; RapidAPI freemium-with-paid-tier is another guess. No comparable in the MCP-builder market exists yet.
- **Distribution channel choice**. x402 vs. RapidAPI vs. direct subscription is undecided. Each has different fulfillment automation profiles.
- **Competitive landscape**. Smithery itself may already be planning a similar product as a registry-native feature, which would commoditize this candidate before it ships.

## How this fits the portfolio passive-income test

Per `supervisor/docs/passive-income-portfolio-strategy.md`, a data/API sleeve product must score on:

- **Self-serve acquisition**: paid endpoint discoverable via documentation page + RapidAPI directory + x402-aware crawler. Yes, if implemented.
- **Automated fulfillment**: re-harvest cadence runs on cron; diff endpoint serves from a cache; no human in the loop after deploy. Yes, by design.
- **Measured paid events**: each x402 / RapidAPI call is a paid event with channel attribution by construction. Yes.
- **Low-support fulfillment**: API surface is small (1–3 endpoints); API errors don't require human triage if monitored. Yes, if telemetry is wired (per the recent `migrate.py` `_emit_telemetry` precedent at commit `531946f`).
- **Net revenue after take-rate**: RapidAPI takes 20%; x402 takes a network fee that is typically much smaller. Unknown gross.
- **Compounding value to the rest of the system**: yes — the harvest pipeline is already an internal-research artifact; productizing its outputs adds an income loop without adding a new pipeline.

## Stage-1 controller mapping (for the per-probe layer)

If we choose to validate this candidate via a probe rather than ship-and-measure:

- **CriticalAssumption**: "There exists at least one buyer who will pay recurring fees for a periodic MCP-registry landscape diff feed."
  - `problem_claim`: MCP-builder analytics buyers (competitive intel teams, VC associates covering agent infra, marketplace ops at MCP platforms) currently rely on manual scraping or do not track this at all.
  - `economic_claim`: They will pay $X-Y/month or $Z/call for a maintained, diff-able machine-readable feed.
  - `channel_claim`: A RapidAPI listing or x402 endpoint with a 1-page documentation surface is sufficient for discovery; no manual outreach required.
- **Probe shape**: deploy a single read-only endpoint with the existing snapshot + a synthetic diff against a manually-curated "previous snapshot" stub. Document on a static page. Measure incoming requests by `X-Source-Type` to distinguish self-traffic. **No principal outreach.**
- **Falsification rule**: 30 days, zero external x402 calls or RapidAPI subscriptions = the discovery surface is not finding any buyer; reframe before iterating.
- **Portfolio-layer metric**: first passive paid event by channel. Stage-1 evidence and portfolio evidence are the same event in this case — the call IS the conversation.

## Concrete next steps if this is approved

In rough order, ~order-of-days each:

1. **Wire the re-harvest schedule** (skillfoundry-researcher-context). Add a systemd timer or cron entry that runs the existing harvest pipeline on a 24h cadence. Emit telemetry per run per the `_emit_telemetry` pattern in `discovery_adapter/migrate.py`. Watch one cycle to confirm sources are stable.
2. **Build the diff layer** (skillfoundry-harness or a new product dir under skillfoundry-products). Read N and N-1 snapshots from researcher-context, emit a `{ added: [...], removed: [...], changed: [...] }` JSON document. Idempotent. Validates against a new schema.
3. **Ship the API endpoint** (skillfoundry-products). Cloudflare Worker following the existing Preflight pattern: GET `/v1/landscape/snapshot/latest`, GET `/v1/landscape/diff?since=...`. Free read with low rate limit; paid via x402 header at higher rate.
4. **List on RapidAPI** for the second channel arm. Documentation page on skillfoundry.synaplex.ai.
5. **Telemetry + measurement**. `sourceType=user` on paid calls, `sourceType=system` on self-tests, separation enforced. First passive paid event is the activation metric.
6. **Honest probe close at 30 days**. Report Stage-1 evidence count AND portfolio activation events; do not conflate.

Estimated effort: 5–10 sessions to first deployed surface; another 30 days of observation for activation evidence. Most of the work is glue between existing pieces (harvest, Worker pattern, telemetry helper); the new work is the diff layer and the rate-limit / paywall logic.

## What this candidate is NOT

- Not a replacement for Launchpad Lint or Preflight. Those are agent/developer-tooling sleeve products; this is a data/API sleeve product. Per ADR-0033, they should co-exist as parallel sleeves, not compete.
- Not a substitute for the manual-offer LCI probe. LCI is a learning sample for whether builders pay for compliance review; this candidate tests whether they pay for landscape data. Different demand sources.
- Not an atlas-style market-modeling asset. Atlas's signal feeds operate in crypto market data; this operates in agent-platform metadata. Adjacent sleeves, not the same one.
- Not contingent on Tally / Render / Fly credentials that are currently blocking other work. Cloudflare credentials (already in the wrangler workflow) + GitHub API token (well-documented free tier) are enough.

## Where to file the principal-decision request

This doc is the candidate proposal. The principal verdict needed is:

- **Yes, prototype the diff layer + cron + Worker endpoint** (~5-10 sessions of harness/products work).
- **No, this isn't the right first candidate** (route a counter-proposal naming the alternative within the data/API sleeve).
- **Defer** (note in `supervisor/decisions/` why we're prioritizing something else first).

Route the verdict via a handoff into `runtime/.handoff/` with target `skillfoundry`. If yes, the next concrete action is to wire the re-harvest schedule and observe one cycle before any product work.
