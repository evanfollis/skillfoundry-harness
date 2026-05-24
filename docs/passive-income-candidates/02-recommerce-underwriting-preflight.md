# Candidate: High-Friction Recommerce Underwriting (preflight plan)

**Date**: 2026-05-24
**Author**: skillfoundry session, 65447b9d-3cb7-4584-bcf2-c058fd025791
**Sleeve**: candidate **high-friction market underwriting** (new sleeve under ADR-0033 portfolio; adjacent to Data/API and Market-modeling but distinct from both)
**Source idea**: `/opt/workspace/supervisor/ideas/IDEA-0007-intimidation-market-arbitrage-high-friction-underwriting.json`
**Source handoff**: `/opt/workspace/runtime/.handoff/skillfoundry-recommerce-underwriting-preflight-2026-05-24.md`
**Strategy doc**: `/opt/workspace/supervisor/docs/passive-income-portfolio-strategy.md`
**Review deadline**: 2026-06-07 (14 days; per IDEA-0007 `review_after`)

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
| 4–10 | Schema + formula scaffold | `tools/recommerce_underwriting/` — Python module with `Lot` model, `all_in_cost()`, `expected_recovery()`, `max_bid()`, written against synthetic test data. Tests. |
| 7–12 | Comp-data source identification | For each category planned, identify a permitted comp source. If no permitted comp source exists for any category, halt. |
| 10–13 | First live lot pull (only if access permitted) | N=10 lots from the permitted source(s). Manual paper underwriting against the scaffold. Discrepancies noted. |
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
