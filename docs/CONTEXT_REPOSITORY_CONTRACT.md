# Context Repository Contract

`skillfoundry-harness` runs against agent context repositories as external
workspaces. The runtime boundary is intentionally narrow.

The harness assumes a context repository is the durable reasoning substrate for an
agent. Individual runtime instances are disposable; the context lineage is not.

## Required Root Files

- `skillfoundry.toml`
- `bundles/`
- `memory/`
- `artifacts/`
- `runs/`

In practice these repos should be git-backed so they can be branched, forked, and
reviewed over time. A remote is optional.

## `skillfoundry.toml`

```toml
[repository]
schema_version = "1"
name = "Researcher Context"
agent_id = "researcher"

[layout]
bundles_dir = "bundles"
memory_dir = "memory"
artifacts_dir = "artifacts"
runs_dir = "runs"

[frontdoor]
pinned_paths = ["README.md", "memory/mission.md"]
discoverable_paths = ["bundles", "memory", "artifacts"]

[promotion_policy]
promotable_memory_roots = ["notes", "plans"]
required_validation_kinds = ["canon-safe", "frontdoor-reviewed"]
```

`[layout]` is optional. If omitted, the default directories above are assumed.

## Contract Rules

- Layout entries must be relative paths inside the repository root.
- Layout entries must resolve to distinct directories.
- `frontdoor.pinned_paths` must point to existing files.
- `frontdoor.discoverable_paths` must point to existing directories.
- `promotion_policy.promotable_memory_roots` must name canonical memory subtrees
  that may receive promoted updates.
- `promotion_policy.required_validation_kinds` defines the validation evidence kinds required
  before apply.
- The harness reads bundle files from `bundles/`.
- The harness exposes typed bundle loading from `bundles/` after validation.
- The harness may write directly only to `artifacts/` and `runs/`.
- Canonical `memory/` updates must flow through proposal approval and apply.
- The harness must not import workspace-local Python code.

## Run Artifacts

The harness writes explicit run artifacts under `runs/YYYY-MM-DD/<run_id>/`:

- `run.json`: durable run metadata.
- `items.jsonl`: append-only lifecycle items for the run.
- `compaction.md`: optional continuation artifact when the run performs compaction.

When a run executes inside a managed worktree, `run.json` and the corresponding
turn record also carry:

- `worktree_name`
- `worktree_path`
- `worktree_head_sha`

`runs/LATEST_RUN` may point to the most recent run id for convenience, but it is a
pointer, not canon.

The harness also persists lifecycle indexes under `runs/threads/<thread_id>/`:

- `thread.json`: thread-level status and latest turn pointer.
- `LATEST_TURN`: convenience pointer to the latest turn id.
- `turns/<turn_id>.json`: turn-level task, branch, status, and latest run pointer.

## Promotion Artifacts

Promotion proposals for canonical memory live under `artifacts/promotions/<proposal_id>/`:

- `proposal.json`: proposal metadata, status, reviewer, pinned validation references, and target path.
- `current.<ext>`: snapshot of the current canonical target at proposal creation time.
- `candidate.<ext>`: the candidate content to promote into `memory/`.
- `diff.patch`: unified diff between current canon and candidate content.

Proposal metadata also records content hashes for the current snapshot, candidate
snapshot, and diff, plus one proposal-level change hash. Apply must fail if any of
those artifacts drift or if canon no longer matches the captured current snapshot.

Validation artifacts live under `artifacts/validations/<validation_id>.json`:

- `kind`: the validation kind, such as `canon-safe` or `frontdoor-reviewed`.
- `status`: whether the validation passed or failed.
- `evidence_paths`: artifact-relative evidence used to justify the validation.
- `artifact_sha256`: integrity digest for the validation artifact itself.
- provenance fields such as reviewer, thread, or turn when available.

Approval artifacts live under `artifacts/approvals/<approval_id>.json`:

- `proposal_id`: the proposal being approved or rejected.
- `proposal_change_sha256`: immutable proposal change digest authorized by the approval.
- `status`: approval decision status.
- `reviewer`: the approving or rejecting identity.
- `artifact_sha256`: integrity digest for the approval artifact itself.
- optional notes and provenance fields.

Canonical memory should be updated through explicit proposal creation, approval, and
apply flows rather than ad hoc direct writes in higher-level runtime code.

The policy bar is enforced at promotion time, not during branch-local drafting. That
preserves reasoning freedom while still making canon changes hard to apply without
reviewable validation evidence and approval artifacts.

## Branch-Local Draft Work

Branch-local draft workspaces live under `artifacts/branches/<branch>/`:

- `memory/`: branch-local drafts that may later be proposed into canonical `memory/`.
- `artifacts/`: branch-local derived outputs.

Branch-local state is intentionally not canon. It exists to support free local work
before explicit promotion.

## Managed Git Worktrees

For true parallel execution, the harness may create managed git worktrees outside the
context repo root. Their metadata is recorded under `artifacts/worktrees/<name>.json`
and includes:

- `worktree_name`
- `branch`
- `path`
- `base_ref`
- `head_sha`
- lifecycle status such as `active` or `removed`
- latest attached `thread`, `turn`, and `run` identifiers when the worktree is used
  for execution provenance

These worktrees are the preferred isolation boundary for subagents that need real git
state, runnable environments, or concurrent filesystem mutation.

## Why This Boundary Exists

Without explicit roots, the harness can silently depend on ambient filesystem
state and the architecture collapses. Explicit layout keeps reviews tractable and
makes it possible for agent hubs to treat context repos as black-box workspaces.
