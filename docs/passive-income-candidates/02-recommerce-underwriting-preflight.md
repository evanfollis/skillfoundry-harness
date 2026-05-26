# Candidate: High-Friction Recommerce Underwriting (preflight plan)

**Date**: 2026-05-24
**Author**: skillfoundry session, 65447b9d-3cb7-4584-bcf2-c058fd025791
**Sleeve**: candidate **high-friction market underwriting** (new sleeve under ADR-0033 portfolio; adjacent to Data/API and Market-modeling but distinct from both)
**Source idea**: `/opt/workspace/supervisor/ideas/IDEA-0007-intimidation-market-arbitrage-high-friction-underwriting.json`
**Source handoff**: `/opt/workspace/runtime/.handoff/skillfoundry-recommerce-underwriting-preflight-2026-05-24.md`
**Strategy doc**: `/opt/workspace/supervisor/docs/passive-income-portfolio-strategy.md`
**Review deadline**: 2026-06-07 (14 days; per IDEA-0007 `review_after`)

> **AUTHORIZATION GATE — read before treating any milestone date below as scheduled work.** Phase 1 (including the Day-1–3 source-access outreach to GovDeals / B-Stock / GSA Auctions partnerships teams) is **contingent on principal authorization**. The "Verdict requested from principal / executive" section at the foot of this document is the gate. Until that verdict lands, the milestone schedule is a **conditional plan**, not an in-flight project. As of 2026-05-26, authorization had not been received and no outreach had been sent. Reflection / synthesis layers should not interpret the table below as work-in-progress that has slipped — it is work that has not started because the prerequisite verdict has not been given.

---

## TL;DR — what this preflight is and isn't

This is a **paper underwriting** preflight for a no-inventory recommerce signal product. The asset is the underwriting model + max-bid recommendation feed + outcome tracking. **It is explicitly not a flipping operation.**

- Phase 1 buys, stores, ships, repairs, lists, and resells **zero** inventory. No exceptions.
- Permitted monetization in Phase 1: paid feed/API, report, subscription dashboard, data licensing, or affiliate **only where the affiliate fee is paid by the source surface to the signal publisher, not earned by Skillfoundry taking a buying action**.
- Excluded monetization in Phase 1: consulting on individual lots, brokering buyers and sellers, taking commission on a deal we facilitated, or any path that requires us to participate in the actual transaction.

## Why this is a separate sleeve, not a data/API extension

ADR-0033 names three current Skillfoundry sleeves: agent/developer tooling, data/API products, market-modeling assets, and research/content licensing. This candidate is technically a Data/API product in shipping form, but its **risk profile and evidence ladder are different enough** that conflating it with the MCP-registry-landscape-feed candidate would be a category error:

- Source surfaces are commercial 3rd-party platforms with restrictive terms (vs. MCP registry feeds which are designed for machine consumption).
- The signal value is bid-discipline against a real auction outcome (vs. landscape data which is read-only state).
- The evidence ladder requires tracking a synthetic portfolio's would-be outcomes against actual hammer prices, not just attributed paid API calls.
- The buyer hypothesis is different: enterprise resellers / asset-recovery analysts / private-equity surplus-asset desks vs. MCP builders.

Naming this a new sleeve also forces the question "is this within the portfolio's frame or outside it?" honestly. The principal verdict is: **inside, if it stays paper-underwriting in Phase 1**.

## Source surfaces — 2-3 candidates, with explicit access-mechanism notes

The handoff named GovDeals and B-Stock. Both have Terms of Use that restrict automated collection. Phase 1 cannot proceed against a source whose terms forbid the access path — that is one of the named kill criteria. **For each source, the first preflight task is to verify the access mechanism is permitted, not to start collecting.**

### Source 1: GovDeals (US government surplus)

- **Why it's a fit**: highly heterogeneous lot types, structured pickup/payment constraints, transparent buyer-premium and fee disclosure, public hammer-price history, large enough volume for statistical baseline.
- **Access mechanism (verification required)**: GovDeals offers RSS feeds per saved search and saved-search exports for registered accounts. Programmatic collection for commercial republication is NOT clearly permitted by their published Terms of Use. **The first preflight check is to email/contact GovDeals product / partnerships about a data-licensing path for the paid-feed use case.** If denied, this source is killed for Phase 1 regardless of how good the signal would have been.
- **Status**: ⚠ access path UNVERIFIED. Do not collect without verification.

### Source 2: B-Stock Solutions (B2B liquidation network)

- **Why it's a fit**: enterprise return / overstock / new-condition inventory from major retailers; explicit manifest data; per-lot freight estimates; closer to the high-friction "you must know the all-in cost" thesis than retail-buyer surfaces.
- **Access mechanism (verification required)**: B-Stock's marketplace is account-gated; meaningful lot data is behind login. Their robots.txt and Terms of Use restrict scraping. They do offer an enterprise data API for select partners. **First check: contact B-Stock's BD / API team about a data-licensing or co-marketing arrangement that lets the signal product cite their lot data with attribution.** Without that, this source is killed for Phase 1.
- **Status**: ⚠ access path UNVERIFIED. Do not collect without verification.

### Source 3 (alternate): public USGSA Auctions / GSAauctions.gov

- **Why it's a fit**: official US federal surplus disposal. Public-domain data publication norms. Bid history disclosure is part of the disposal process.
- **Access mechanism**: federal public-records context typically permits republication with attribution, but specific terms of use must still be read. Likely the most legally clean of the three.
- **Status**: ⚠ Terms-of-Use read REQUIRED before collection; provisional best-bet on the access-permission axis.

**Sequence**: do NOT collect anything from any source until at least one source's access path is verified in writing. The first preflight artifact is a written record of which source path was confirmed (or denied). This is the "data access depends on brittle scraping or violates source terms" kill criterion taken seriously.

## Minimum lot schema (normalized across sources)

Each lot record carries:

- `lot_id` (source-specific URL or auction reference)
- `source` (govdeals / bstock / gsaauctions)
- `category` (resale taxonomy — initially coarse: electronics, apparel, industrial-tools, vehicles, IT-equipment, returns-mixed, etc.)
- `hammer_price` and `current_bid` (running)
- `buyer_premium_rate` (percentage)
- `taxes_estimate` (jurisdiction-dependent; conservative upper bound when unknown)
- `pickup_deadline` (datetime; affects freight modeling)
- `pickup_location` (zip / region; affects freight rate)
- `freight_handling_estimate` (per-lot, derived from lot weight/volume + pickup location; uses a freight-rate lookup as the source-of-truth)
- `storage_default_fee_terms` (per-day-late fees, default penalties)
- `condition_class` (new / refurb / used-working / scratch-dent / salvage / mixed-returns)
- `manifest_quality` (full / partial / unmanifested / claimed — affects condition-class confidence)
- `resale_category` (where the lot would resell — e.g., direct retail, B2B wholesale, scrap)
- `comparable_sale_basis` (link to comp data — see speculation flag below)

## All-in landed cost formula

```
all_in_cost = hammer_price
            + (hammer_price * buyer_premium_rate)
            + taxes_estimate
            + freight_handling_estimate
            + packaging_handling_estimate
            + storage_default_reserve
            + platform_resale_fee_reserve
            + return_disposal_reserve
```

Each reserve is a **conservative upper-bound** in Phase 1. Reserves get tuned only against actual recovered evidence in later phases.

## Expected recovery formula

```
expected_recovery = (resale_comp_median
                    * condition_class_haircut
                    * manifest_confidence_factor
                    * sell_through_probability)
                  - (resale_shipping_burden + category_liquidity_penalty)
```

Where each factor in `[0, 1]` and starts at conservative defaults until real outcomes train them.

**Edge** = expected_recovery − all_in_cost. **Max-bid** is the hammer_price at which Edge equals the chosen hurdle rate (e.g., 25% of all_in_cost as paper margin).

## Tracking outcomes WITHOUT bidding

Before any bid would have been placed, the system records:
- max-bid recommendation
- hurdle-rate assumption
- input factor values (so post-hoc tuning is possible)

After auction close, the system records:
- actual hammer price
- whether the lot cleared the recommended max-bid
- (if observable) any follow-on resale signal — typically not visible without buyer cooperation, so this is the weakest data class

Phase 1 success: at the end of N tracked lots (target N=50–200), the paper-portfolio Edge ledger shows whether the recommendations would have generated positive Edge net of all reserves. **Not whether they did generate Edge — they aren't bid on.**

## Passive monetization route (Phase 1)

One angle per the strategy doc's `data/API products` sleeve criteria:

- **Primary**: subscription dashboard + paid API for daily lot recommendations (max-bid + uncertainty band) and post-close outcome tracking. Buyer hypothesis: small-to-mid recommerce operators who don't have their own underwriting team but can act on a recommendation list. Pricing model: $50–$500/month tiers depending on lot volume and category coverage.
- **Secondary (only if primary fails)**: data-licensing of the historical comp-and-outcome ledger to enterprise asset-recovery analysts or PE surplus desks. Larger contracts, fewer buyers, longer sales cycles.
- **Explicitly excluded**: any monetization route where Skillfoundry brokers a deal, takes commission on a transaction we facilitated, or earns affiliate fees on bids that an end-buyer placed because we recommended a lot. Those would all violate the no-manual-selling and no-inventory-operations constraints.

## What is grounded vs. what is speculation

Following the structure of `01-mcp-registry-landscape-feed.md`. Honesty about both halves prevents an authorized prototype from being built on hidden assumptions.

### Grounded

- The recommerce market is large and growing (eBay 2025 GMV $79.6B; OfferUp 2025 report projects $306.5B by 2030 per IDEA-0007 evidence; B-Stock describes itself as largest B2B liquidation network).
- High-friction recommerce has structural inefficiency: variable buyer premiums, freight constraints, condition uncertainty, and short pickup windows mean naive bidders systematically misprice.
- Skillfoundry already has the substrate for periodic harvest pipelines (`19281a7` in skillfoundry-researcher-context for the MCP-registry harvest baseline; reusable pattern for a recommerce harvest).
- Atlas has methodology vocabulary applicable here: hurdle-rate framing, paper-strategy ledger, drawdown / regime measurement. Borrowed, not depended on — Atlas does not own this.

### Speculation flagged honestly

- **Source access permissions are unverified.** Both GovDeals and B-Stock have access paths whose commercial-republication terms are not confirmed. The plan above puts access verification as the first task; do not skip it.
- **Comparable-sale basis data does not yet have a source identified.** Resale comp data for variable-condition lots is expensive (eBay's Terminapi, Keepa for some categories, Kelley Blue Book for vehicles only) or absent (returns-mixed lots, scratch-and-dent industrial equipment). If a permitted comp source can't be identified for at least one category, that category is out of Phase 1 scope. If NO permitted comp source can be identified, Phase 1 cannot proceed at all.
- **Buyer demand for the signal product has zero validation.** No recommerce operator has been asked whether they would pay for max-bid recommendations. The buyer hypothesis (small-to-mid operators without underwriting teams) is plausible but unproven. A "would you pay $X/month for this" interview round is a separate validation; the paper-underwriting evidence is necessary but not sufficient for product/market fit.
- **Pricing is a guess.** $50–$500/month tiers are anchored on adjacent SaaS-tool benchmarks, not on validated willingness-to-pay.
- **Sell-through and condition-class haircut defaults are guesses.** The Phase 1 lot ledger needs enough volume + actual hammer-price closeouts to start tuning these against real distributions. With N=50 lots in 14 days against 2-3 sources, expect coarse calibration only — not statistical significance.
- **No competitive landscape mapped.** Whether Liquidity.io, B-Stock's own analytics, or a private fund already publishes this signal is unknown.

## Prediction ledger telemetry overlay

Per the workspace standard at `/opt/workspace/supervisor/docs/predictive-evidence-telemetry-loop.md`, every tracked lot must produce an **immutable prediction row** before the auction closes, then receive appended observations, score, and lessons after close. Reasoning prose does not substitute for scored predictions. Retrospective edits create a superseding row; the original row is never rewritten.

### Action-tier declaration

Phase 1 action tier is **`paper_trade`** for every row.

- `allowed_actions`: `record_recommendation`, `observe_outcome`, `score`, `append_lesson`.
- `blocked_actions`: `place_bid`, `pickup`, `store`, `ship`, `resell`, `broker_deal`, `take_commission`.

Any row whose `actual_action` is anything other than `record_recommendation` is a tier-escalation event and requires a separate principal decision under ADR-0033. The schema rejects writes where `actual_action ∉ allowed_actions` unless a paired `tier_escalation_decision_ref` is attached.

### Prediction row schema (recommerce specialization of the standard)

A row is written **once**, before `close_time` is known. Fields below are the standard's row shape with recommerce-specific value conventions.

**Identity + provenance**
- `row_id` — uuid4
- `candidate_id` — `recommerce-underwriting-2026-05-24` (this candidate's slug)
- `market_surface` — one of `govdeals` | `bstock` | `gsaauctions`
- `item_id` — source-stable lot id (URL or auction ref)
- `item_snapshot_ref` — relative path or hash of the saved lot snapshot at `snapshot_time`
- `snapshot_time` — ISO-8601 UTC
- `source_terms_status` — one of `permitted_written` | `permitted_implied` | `unverified` | `denied`. Rows with `unverified` or `denied` are written for audit purposes only and must not contribute to portfolio metrics.

**Agent + policy version**
- `agent_run_id` — uuid for the run that wrote this row
- `model_id` — exact model id (e.g., `claude-opus-4-7`)
- `tool_versions` — map: `recommerce_underwriting` module version + freight-rate-table version + comp-source version
- `prompt_or_policy_ref` — git ref to the policy version that produced the recommendation

**Action tier**
- `action_tier` — `paper_trade` (constant for Phase 1)
- `allowed_actions`, `blocked_actions` — as above
- `recommended_action` — `bid_up_to_max_bid` | `watch_only` | `ignore` | `kill_category`
- `actual_action` — for Phase 1, always `record_recommendation` (assert in schema validator)

**Hypothesis + prediction**
- `hypothesis` — one-line statement of the edge claim (e.g., "freight-uncertainty discount means hammer will close ≤60% of comp_median")
- `prediction_targets` — list of named targets (see below)
- `prediction_values` — value per target
- `confidence_or_distribution` — for point estimates, an 80% interval `[low, high]`; for probability targets, a calibrated probability in `[0, 1]` with the bucket the model is reporting against
- `decision_thresholds` — explicit numeric thresholds the recommended_action key off of (hurdle rate, minimum manifest_confidence_factor, etc.)
- `expected_value_metric` — `expected_edge_after_reserves`
- `risk_budget` — for Phase 1, `0` (no capital at risk; defines the policy if/when we ever ship pilot)

**Recommerce-specific prediction targets** (subset; not all need to be present on every row)
- `final_hammer_price` (point + 80% interval)
- `hammer_below_max_bid` (probability)
- `all_in_cost_estimate` (point + interval)
- `expected_recovery_estimate` (point + interval)
- `expected_edge_after_reserves` (point; signed)
- `category_liquidity_class` (categorical: high / medium / low / illiquid)
- `sell_through_probability_at_target_margin` (probability)
- `source_data_quality_failure` (probability — captures manifest/condition uncertainty risk)

**Reasoning + evidence**
- `reasoning_summary` — bounded structured text: premises, key uncertainty, dominant risk factor. Hard cap ~500 chars. **No unbounded chain-of-thought.**
- `evidence_refs` — list of `{type, ref, weight}` for comp data, freight quotes, prior similar lots
- `causal_assumptions` — list of named edges from the temporal causal map this row depends on
- `counterfactuals` — list of `{condition, predicted_change}` (e.g., "if pickup_deadline were 7d instead of 3d, expected_edge +X%")
- `known_unknowns` — explicit list of variables the model is not modeling and a tag for which kill criterion they map to

**Post-close (appended later; null at write-time)**
- `close_time` — ISO-8601 UTC; null until auction closes
- `outcome_observations` — list of `{target, observed_value, observation_source, observation_quality}`. Observation quality one of `verified` | `proxy` | `inferred`. Inferred resale outcomes never count as verified.
- `score` — per-target metric (absolute error / signed bias / Brier / log-loss / calibration-bucket-hit)
- `error_attribution` — one of `data` | `model` | `tool` | `policy` | `market_regime` | `execution`
- `lesson` — bounded structured text: one concrete reusable rule
- `future_policy_suggestion` — one of `change_threshold` | `change_source_weight` | `change_category_eligibility` | `change_reserve_default` | `add_evidence_class` | `no_change_with_reason`. Must include the specific parameter and proposed value.

**Supersession**
- `supersedes` — `row_id` of any row this one replaces (only for revised reviews of an already-closed item; never for editing a still-open prediction)
- `superseded_by` — backlink, written when a successor row appears

### Anti-theater clauses (binding for this candidate)

- No row is portfolio-relevant until `close_time` is appended and `score` is computed. Open rows are audit-only.
- A `lesson` field that does not name a specific threshold, source-weight, category, or reserve to change is rejected by the review tool — it must point at one parameter or carry `no_change_with_reason`.
- Aggregate metrics (median edge, category hit-rate, calibration curve) cannot be reported across <20 closed rows in a single category, or <50 closed rows across categories. Below those thresholds the candidate dashboard renders "insufficient data" instead of a number.
- `confidence_or_distribution` is required on every prediction value. A bare point estimate is rejected.
- Retrospective threshold movement is rejected at the storage layer. If a threshold needs to change, that creates a NEW policy version (`prompt_or_policy_ref` bump) which all subsequent rows reference; prior rows keep their original thresholds.

### Storage + immutability

- Rows are stored as append-only JSONL at `data/recommerce_underwriting/predictions.jsonl` inside whichever repo the loop runs in (TBD between `skillfoundry-harness` and a new sleeve-specific repo; flagged in the milestone schedule).
- Each row's `row_id` plus row body is also hashed and the hash logged separately, so a retrospective edit would be detectable.
- Telemetry events (`prediction.opened`, `prediction.closed`, `prediction.superseded`, `prediction.scored`) emit to `/opt/workspace/runtime/.telemetry/events.jsonl` using the workspace `sourceType` convention; `paper_trade` rows emit with `sourceType: system` for unattended runs and `sourceType: user` for attended scaffolding work.

### Post-close review artifact

For each closed row, the post-close review (per the standard's "Review After Close" section) writes a short markdown file under `docs/passive-income-candidates/recommerce-reviews/<close_date>/<row_id>.md` answering:

- what was predicted
- what happened
- where the gap came from
- whether the policy would have changed with better information
- error attribution
- one concrete future-policy suggestion (must match `future_policy_suggestion` field on the row)
- what should NOT change despite this outcome
- separation of luck from process quality

Reviews are bounded in length (target <30 lines each) — anti-theater applies.

### Companion schema artifact

A machine-checkable JSON Schema at `tools/recommerce_underwriting/prediction-row.schema.json` ships alongside the Phase-1 scaffold (Day-4–10 milestone). Until that exists, this section is the authoritative spec.

## Stage-1 controller mapping (per-probe layer)

If this candidate is authorized to graduate to a probe rather than ship-and-measure:

- **CriticalAssumption**: "A no-inventory paper-underwriting signal product for high-friction recommerce has at least one self-serve paying buyer."
  - `problem_claim`: small-to-mid recommerce operators systematically over-bid on high-friction lots because they don't model all-in landed cost and condition-adjusted recovery carefully.
  - `economic_claim`: those operators will pay $50–$500/month for a maintained max-bid + outcome-tracking dashboard or API.
  - `channel_claim`: a paid landing page + API listing on a developer marketplace (RapidAPI) or a referenced inclusion on liquidation operator forums is sufficient for discovery — no manual sales motion required.
- **Probe shape**: collect N=50 lots over 14 days from the access-verified source(s); publish max-bid recommendations on a dated, hash-bound page; track outcomes; offer a paid subscription button that pays a webhook on signup, **with no follow-up sales loop on the Skillfoundry side**.
- **Falsification rule**: 30 days post-launch, zero paid subscriptions AND zero external inbound inquiries via the published page → the buyer hypothesis is not supported; reframe before further iteration.
- **Portfolio-layer metric**: first passive paid subscription event, with channel attribution.

## Kill criteria (from the handoff, restated and operationalized)

Stop or reframe if any of these become true at any phase:

1. **Fees, freight, condition uncertainty, or resale liquidity erase the modeled edge.** Operationally: after N=50 tracked lots, the paper portfolio's median expected Edge is ≤0 net of all reserves with default factor values.
2. **Data access requires brittle scraping or violates source terms.** Operationally: no source's access path is verified in writing by Day 7. Phase 1 halts.
3. **The only viable monetization requires manual consulting or inventory operations.** Operationally: if every plausible buyer interviewed wants the signal embedded in a deal-brokerage service rather than a self-serve feed, the candidate is reframed or killed — not pursued as a manual service.
4. **The model cannot explain false positives and category-specific failures.** Operationally: at N=50 lots, if more than 20% of "max-bid clearly hit" cases produced losses (when looked at post-close) AND the model has no per-category explanation, the calibration loop has not converged and Phase 1 closes inconclusive.

## Atlas adjacency (acknowledgment, not dependency)

Methodology to **borrow** from atlas, where it's already mature there:
- hurdle-rate framing and paper-strategy ledger discipline
- regime-detection methodology for category-level signal-decay (does the underwriting edge hold across normal vs. high-supply recommerce regimes?)
- drawdown / streak measurement to avoid being fooled by short winning runs

Atlas **does not** become an owner or required dependency. The handoff is explicit on this; the candidate's success or failure must not require atlas-pod work to ship.

## Milestone schedule (must produce something paper by 2026-06-07)

Working back from the IDEA-0007 `review_after: 2026-06-07` — 14 days from this doc.

| Day | Milestone | Output |
|---|---|---|
| 1 (today) | Candidate doc filed | this file (committed) |
| 1–3 | Source-access-permission outreach | 3 emails/forms sent to GovDeals, B-Stock, GSA Auctions partnerships/legal/BD. Replies tracked. |
| 4–7 | Access-permission verdicts | For each source: written PERMITTED / NOT-PERMITTED / NO-REPLY status. If 0/3 permitted, halt and report. |
| 4–10 | Schema + formula scaffold | `tools/recommerce_underwriting/` — Python module with `Lot` model, `all_in_cost()`, `expected_recovery()`, `max_bid()`, prediction-row writer + immutability guard, JSON Schema at `prediction-row.schema.json`. Tests assert immutability + `actual_action ∈ allowed_actions`. |
| 7–12 | Comp-data source identification | For each category planned, identify a permitted comp source. If no permitted comp source exists for any category, halt. |
| 10–13 | First live lot pull (only if access permitted) | N=10 lots from the permitted source(s). Each lot produces ONE prediction row at write-time (immutable). Post-close review files appended as auctions close. |
| 14 (2026-06-07) | Review-after artifact | Short status doc at `docs/passive-income-candidates/02-recommerce-underwriting-preflight-status-2026-06-07.md` covering: access-permission state, comp-data state, scaffold state, lots underwritten so far, kill-criteria check, next-step recommendation. |

If the milestone schedule slips because no source permission is received in writing by Day 7, the Day-14 artifact still ships — its content just shifts from "first lots underwritten" to "halted by access verification gate" + recommendation (give up, try other sources, license a paid feed instead, or pursue a completely different recommerce angle).

## Reverse: what would I NOT recommend in this preflight

- I am **not** recommending Skillfoundry deploy a Worker or a public dashboard yet. That comes after Phase 1's paper-underwriting evidence is in.
- I am **not** recommending an atlas-side ADR or any atlas-pod work. Atlas methodology is borrowed lite.
- I am **not** recommending purchasing comp data (Terminapi, Keepa, etc.) before access permissions are verified. That spending is a sunk cost if the upstream source path is denied.
- I am **not** recommending creating CriticalAssumption / Probe / Decision artifacts in valuation-context yet. Phase 1 is preflight — the formal probe only opens if the access + comp + scaffold gates all clear and we have lot-level evidence to ground the probe in.

## Verdict requested from principal / executive

- **Authorize Phase 1** (source-access outreach + scaffold + first paper underwriting) as scoped above; review at 2026-06-07.
- **Defer** (reason).
- **Reframe** (specific direction; current framing is data/API-product on the underwriting signal, not inventory operations).
- **Kill** (specific reason; if the buyer hypothesis is implausible at this stage, that's a fine kill).

## Where this candidate doc lives going forward

If authorized: this doc stays the spec; the Day-14 status doc and any follow-up artifacts also live under `docs/passive-income-candidates/`. If the candidate graduates to a probe, formal artifacts move to `skillfoundry-valuation-context/memory/venture/` at that time.
