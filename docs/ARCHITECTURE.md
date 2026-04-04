# Harness Architecture

## Topology

The system is split into three layers:

1. `skillfoundry-harness`
   The pip-installable package and runtime machinery.
2. `skillfoundry-agents`
   The coordination hub that tracks which agents exist.
3. `agents/<agent>/context`
   A mounted checkout of a per-agent git-backed context lineage.

## Ownership

`skillfoundry-harness` owns:

- Canonical schemas and validation.
- `Runtime` and repository interfaces.
- CLI entrypoints and runtime semantics.
- Safety boundaries for repository mutation, including approved write roots.
- Managed worktree orchestration for isolated branch execution.

`skillfoundry-agents` owns:

- Agent registry and manifests.
- Reusable declarative role/profile overlays referenced by agent manifests.
- Shared orchestration metadata.
- The workspace topology linking agents to their context repos.
- The workspace topology linking agents to their mounted context checkouts.

Each agent `context/` repo owns:

- Goals, memory, bundles, and artifacts for that specific agent.
- Repo-local configuration consumed by the harness.

## Expected Flow

1. An agent is declared in `skillfoundry-agents`.
2. A git-backed context lineage is initialized, forked, or otherwise mounted at
   `agents/<agent>/context`.
3. The harness is installed in an environment.
4. The harness opens the context repo through `Runtime.open(path)`.
5. Validation and execution happen against explicit repository surfaces.

## Repository Contract

The harness treats an agent context repo as data plus declared layout. The
contract is:

- `skillfoundry.toml` at the repository root.
- One `[repository]` table with `schema_version`, `name`, and `agent_id`.
- One optional `[layout]` table naming relative directories.
- One required `[frontdoor]` table naming pinned files and discoverable roots.
- Four resolved roots: `bundles/`, `memory/`, `artifacts/`, and `runs/`.

The harness may read from `bundles/` and may write only to `artifacts/` and `runs/`
directly. Canonical `memory/` is writable only through explicit promotion apply.
Those roots must remain inside the repository root.

## Target Runtime Model

Skillfoundry should converge on explicit runtime primitives:

- `thread`: durable conversation or workstream container.
- `turn`: one unit of requested agent work inside a thread.
- `item`: one atomic observable event or artifact inside a turn.
- `run`: one concrete execution instance that processes a turn against one branch or
  worktree.

Approvals, compaction, and subagent delegation should appear as explicit lifecycle
events, not hidden prompt conventions.

Repository writes should also be explicit. Runtime code should mutate context only
through bounded repository surfaces such as artifact writes, run event appenders, and
promotion apply, not by open-coded path joins scattered through the runtime.

## Context Strategy

The harness should assemble context from:

- a short front door,
- typed bundles loaded from `bundles/`,
- pinned canonical files,
- targeted reads discovered during the run,
- compacted summaries or opaque continuation artifacts when the context window must
  shrink.

The default should be progressive disclosure. Full-workspace prompt dumps should be
treated as an architectural smell.

## Promotion Strategy

Branch- or worktree-local work should remain free until promotion. Promotion into
shared canon should be explicit, attributable, reviewable, and validator-backed.

At the current repository level, that means canonical `memory/` updates should flow
through explicit proposal artifacts stored under `artifacts/promotions/` before they
are applied into current-state canon.

Branch-local drafts may live under `artifacts/branches/<branch>/...`, keeping the
distinction between draft state and canon visible in the tree structure itself.
When the task needs real filesystem and git isolation, the harness should prefer
managed git worktrees over in-repo draft namespaces.

Promotion policy should be repository-owned and explicit. The harness should enforce
it only at approval/apply boundaries so branch-local reasoning remains unconstrained
while canon changes still require reviewable evidence.

That evidence should be modeled as durable validation artifacts with kinds, status,
evidence pointers, and pinned hashes, not as loose string tags on proposals. Approval
should also be modeled as a durable artifact tied to an immutable proposal change,
rather than a transient field mutation.

Proposal artifacts should be review-complete: a reviewer should be able to inspect
the current snapshot, candidate snapshot, and diff without reconstructing the change
manually from canon files.

## Parallel Agent Work

Subagents should operate in isolated worktrees or branches. Shared context repos are
not safe for concurrent mutation without that isolation.

The harness now manages real git worktrees outside the repo root and records their
metadata under `artifacts/worktrees/`. That gives operators one reviewable place for
worktree intent while still using native git isolation.

When a run uses one of those worktrees, the worktree identity and head sha should be
captured directly in the corresponding turn and run records, and the managed
worktree metadata should point back to the latest thread/turn/run that used it.

## Constraints

- The harness must not import arbitrary workspace code.
- The hub must not become the canonical home of context semantics.
- Agent contexts must be independently versionable and reviewable.
- Git remotes are optional. A local git-backed context lineage is still a first-class
  agent substrate.
- Cross-agent interaction should happen through explicit harness APIs or shared artifacts,
  not by one agent mutating another agent's repo directly.
