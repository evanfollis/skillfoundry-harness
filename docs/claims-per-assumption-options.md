# Proposal: 3 Claims per Assumption — spec pressure-test

**Status**: routed to context-repo spec review
**Date**: 2026-04-23
**Author**: skillfoundry session, 65447b9d-3cb7-4584-bcf2-c058fd025791
**Review artifact**: `supervisor/.reviews/discovery-adapter-2f63ae5-post-fix-2026-04-23T17-59Z.md` Finding A
**Prior routing pattern**: `runtime/.handoff/context-repo-canon-schema-weakens-assumption-2026-04-23T18-45Z.md`

---

## Problem

A Skillfoundry `CriticalAssumption` markdown file has three semantic axes of the business thesis:

- `problem_claim` — what pain does the buyer have
- `economic_claim` — will they pay for a fix
- `channel_claim` — can we reach them in a repeatable way

The current discovery adapter (`emit.py:197-224`) emits **one** canon `Claim` envelope per `CriticalAssumption`, using `problem_claim` as the `statement` field. The other two claims are documented as artifact-only recovery in `MAPPING.md:12-17` and `:136-140` — i.e. downstream consumers who want them must re-parse the markdown.

## Why this matters

The canon store is positioned as the source of truth for semantic state. Every consumer (reasoning layer, cross-pod joins with atlas-ingest-canon, future agent-addressable protocol surface) reads canon. If `Claim` envelopes carry 1/3 of each assumption's thesis:

- Decisions and evidence look canonically valid while silently anchoring on partial thesis.
- Cross-pod commercial-prioritization reasoning can't distinguish "problem is real" from "buyer will pay" from "we can reach them" — all three are load-bearing in different ways, and commercial traction requires all three.
- If the choice is wrong, fixing it later requires a canon rewrite across all downstream repos.

## Options

### Option 1 — emit 3 Claim envelopes per Assumption

**Shape**: each assumption produces three envelopes with shared `assumption_id` linking them. Naming example: `<assumption_id>:problem`, `<assumption_id>:economic`, `<assumption_id>:channel`.

Pros:
- Most faithful to canon's "Claim = atomic semantic unit" semantics.
- Downstream consumers can join on `assumption_id` to reconstruct the assumption; or join on `Claim.id` directly for axis-specific reasoning.
- No canon schema change required (uses existing Claim shape).

Cons:
- Triples the Claim count in canon (13 → ~39 envelopes for valuation-context at current size; atlas has 253 envelopes, many of which are claims — impact TBD without a count).
- Evidence linkage becomes ambiguous: does `supports: supports_assumption` apply to the whole assumption or to one claim axis? Have to pick one (probably `problem_claim` as default with explicit `claim_axis` field on Evidence envelopes).
- Decisions reference an `assumption_id`, not a claim. New field needed on Decision to name the axis being decided on, OR decisions scope to the whole assumption cluster.
- Biggest refactor of the three options.

### Option 2 — one Claim, structured multi-field statement

**Shape**: `Claim.statement` becomes a structured block instead of a single string. Example:

```json
{
  "statement": {
    "problem": "Demo buyers need a thing",
    "economic": "They will pay",
    "channel": "Direct email works"
  }
}
```

Pros:
- One envelope per assumption preserved; count stays stable.
- All three axes present in canon.
- Minimal downstream schema churn (existing joins still work on `Claim.id`).

Cons:
- **Stretches canon schema v0.1.0**: `Claim.statement` is currently typed as `string`. Changing to `string | object` is either a schema bump or a type-tag-smuggling hack.
- Contradicts canon's "Claim = atomic semantic unit" framing — one envelope would carry three semantic units.
- Cross-pod consumers expecting `statement: string` break.

### Option 3 — acknowledge collapse, document loudly

**Shape**: No code change. Add a prominent section to `MAPPING.md` stating: "The canon `Claim` emitted per `CriticalAssumption` carries only `problem_claim`. Consumers needing `economic_claim` or `channel_claim` must re-parse the source markdown at `Claim.artifact.uri`."

Pros:
- Zero code churn.
- Explicit — breaks the "valid-looking lies" failure mode the prior review (Finding 2) already addressed for enums, by making the partial-thesis behavior visible.

Cons:
- Pushes the cost onto every downstream consumer, every time.
- The "re-parse markdown" escape hatch defeats the canon-as-source-of-truth property.
- If consumers forget to re-parse (likely), decisions downstream are made on 1/3 of the assumption's thesis while looking canonically complete.

## Recommendation

Routing to context-repo spec authority for decision. Skillfoundry perspective:

- Option 1 is the most faithful but the biggest refactor. Worth doing if the canon is going to be shared across pods (atlas ingesting skillfoundry claims, cross-pod reasoning layer) — partial thesis is more painful at scale than in a single-pod context.
- Option 2 is a compromise that stretches the Claim shape in a way that's hard to undo cleanly.
- Option 3 is honest about the current behavior but doesn't improve canon quality.

**Skillfoundry's preferred order**: 1 > 3 > 2. If Option 1 is too big to schedule this cycle, Option 3 is the cheapest honest fallback while Option 1 is planned. Option 2 would be hard to reverse and is the worst option to "just ship."

## Constraints from the handoff

- Canon schema v0.1.0 is frozen without explicit principal approval for a bump. Option 2 triggers a schema conversation; Option 1 does not; Option 3 does not.
- The reasoning-layer and atlas-ingest-canon work are in flight; a decision here should happen before they anchor on the current single-Claim behavior.

## Next step

Context-repo spec-review session to weigh in with a decision. This proposal + principal verdict lands as either an ADR in skillfoundry-harness (if fix target is harness-local) or a canon spec note (if schema-side).
