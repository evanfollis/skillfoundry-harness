# Skillfoundry → canon mapping (v1)

This document explains the skillfoundry-valuation-context markdown → L1
discovery-framework canon mapping implemented in `emit.py`.

Canon spec: **0.1.0** (`/opt/workspace/projects/context-repository/spec/discovery-framework/`).

## Object mappings

### CriticalAssumption → Claim

Skillfoundry assumptions carry three component claims
(`problem_claim`, `economic_claim`, `channel_claim`). Canon Claim has a
single `statement`. Mapping: **statement = problem_claim** (the falsifiable
commercial claim). The other two are preserved in the markdown artifact via
hash-bound ArtifactPointer — downstream consumers who need the full buyer
story re-parse the markdown.

| Markdown key | Canon Claim field | Transform |
|---|---|---|
| `assumption_id` | `id` | identity (prose slug) |
| `problem_claim` | `statement` | identity |
| `falsification_rule` | `falsification_criteria` | wrap as `[str]` |
| `created_at` | `emitted_at`, `role_declared_at` | ISO normalize |
| `status` | (not on Claim) | emitted as EventLogEntry.phase_transition |
| `economic_claim`, `channel_claim`, `buyer_role`, `owner`, `next_probe_id` | (not mapped) | preserved in artifact |

**Adapter-supplied canon fields:**
`spec_version=0.1.0`, `object_type=Claim`, `emitter=L3:skillfoundry`,
`layer=L3`, `roles=[Claim]`, `binding=binding`, `sources=[]`,
`exposure=_default_exposure()`, `artifact=ArtifactPointer` (sha256 of file),
`instance_id=skillfoundry-valuation-context`.

### Probe → EventLogEntry (multiple)

Skillfoundry probes are operational events, not canon objects. Each probe
emits up to three canon EventLogEntry envelopes:

1. `phase_transition` (draft → probe) at `started_at`
2. `methodology_log` with ArtifactPointer to the probe markdown (per
   canon.md Phase Invariants: "Methodology log entry required on entry to probe")
3. `phase_transition` (probe → promotion) at `ended_at`, only when `status=closed`

| Markdown key | Canon field | Notes |
|---|---|---|
| `probe_id` | event id prefix (`pt-<probe_id>-…`, `ml-<probe_id>`) | |
| `assumption_id` | `phase_transition.claim_id` + `subject_id` | |
| `started_at` | first event `emitted_at` + `role_declared_at` | |
| `ended_at` | second-transition `emitted_at` (if closed) | |
| `probe_type` | `methodology_log.summary` | free-form summary |

Probes fields not mapped (`probe_type` enum, `artifact_class`,
`offer_presented`, `target_persona`, `target_evidence_class`,
`minimum_evidence_quality`, `success_rule`, `falsification_rule`, `owner`)
live in the artifact body.

**Outlier**: `probes/preflight-distribution-signal.md` uses a prose/bold
format rather than the canonical backtick-key-value header and does NOT
parse. Skillfoundry PM action item: reformat that file to match the
canonical probe header shape used by
`probes/launch-compliance-intelligence-manual-offer.md` and
`probes/launchpad-lint-agenticmarket-live-listing.md`.

### Evidence → Evidence

Skillfoundry's `evidence_class` enum is **identical** to canon's `tier`
enum — canon inherited the 4-tier hierarchy from skillfoundry's earlier
work. Direct map.

| Markdown key | Canon Evidence field | Transform |
|---|---|---|
| `evidence_id` | `id` | identity |
| `assumption_id` | `claim_id` | identity |
| `evidence_class` | `tier` | identity (enum alias table in `_TIER_ALIASES`) |
| `source_type` | `evidence_type` | identity (domain-owned free-form string) |
| `supports` | `polarity` | `supports_assumption→supports`, `contradicts_assumption→contradicts`, `lane_activation_only→neutral`, else `neutral` |
| `observed_at` | `emitted_at`, `observed_at`, `role_declared_at` | ISO normalize |

Fields preserved in artifact only: `evidence_quality` (weak|moderate|
strong), `source_identity`, `summary`, `raw_pointer`, `confidence`.

### Decision → Decision

Skillfoundry's `decision_type` enum is richer than canon's; the mapping
folds skillfoundry-specific types into the closest canon kind and
prepends a `[skillfoundry-type=<raw>]` marker to `rationale` so the
nuance is mechanically discoverable.

| `decision_type` | canon `kind` |
|---|---|
| `continue` | `continue` |
| `tighten` | `continue` (rationale flagged `[skillfoundry-type=tighten]`) |
| `pivot` | `pivot` |
| `pause` | `continue` (rationale flagged `[skillfoundry-type=pause]`) |
| `kill` | `kill` |
| `promote` | `promote` |

| Markdown key | Canon Decision field | Transform |
|---|---|---|
| `decision_id` | `id` | identity |
| `assumption_id` | `candidate_claims[0]`, `chosen_claim_id` | identity |
| `decision_type` | `kind` | via table above |
| `evidence_refs` | `cited_evidence` | list pass-through |
| `rationale` | `rationale` | prepended with type-marker if lossy |
| `timestamp` | `emitted_at`, `role_declared_at` | ISO normalize |

Adapter-supplied: `policies_in_force` references the quality-note Policy
(`skillfoundry.evidence_quality_note` v1); `exposure` uses the default
envelope; `promotion_id` synthesized as `prom-<decision_id>` when
`kind=promote`.

## Policy: the quality-field note

Canon has no `quality` field on Evidence; skillfoundry's
`evidence_quality` (weak|moderate|strong) is preserved in the artifact
only. The adapter emits a Policy envelope documenting this so future
consumers find the semantic locus mechanically.

Rollback condition: canon spec gains a first-class quality field (spec
v0.2.0+), at which point this Policy is obsolete and the adapter is
updated to emit `Evidence.quality` directly.

## Things deliberately not mapped

- Skillfoundry's **promotion workflow** (`src/skillfoundry_harness/promotion.py`,
  367 LOC of cryptographic memory-promotion) — that's a separate subsystem
  (canonical-memory commit/approve/apply), distinct from canon Promotion.
  Not touched by this adapter.
- The **bundle layer** (`bundles/*.json`) — cross-repo coherence contracts;
  canon doesn't model these.
- `next_probe_id` and probe lineage — canon has no first-class
  "claim-to-claim next-probe" edge. Lineage stays in the markdown.

## Open questions (surfaced, not resolved)

- **Assumption-as-three-claims**. Emitting three canon Claims per
  skillfoundry assumption (problem/economic/channel) is architecturally
  cleaner but canon has no native parent-child Claim link. Current choice
  (one Claim with `statement=problem_claim`) is defensible but lossy. If
  canon gains `related_claims[]` in a future version, revisit.
- **Canon Promotion**. When a skillfoundry decision has `kind=promote`,
  should the adapter also emit a canon Promotion envelope? Canon's
  Promotion requires `external_validation` and `ceiling_check`; skillfoundry
  decisions today don't carry structured external-validation attestation.
  Deferred; see ADR-0026.
