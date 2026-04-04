# Principles

## Harness Owns The Law

Canonical contracts, validation rules, and execution semantics belong here. Agent
workspaces instantiate those rules; they should not redefine them piecemeal.

## Constrain Promotion, Not Internal Reasoning

The harness may strictly constrain write surfaces, approvals, validation, and
promotion into shared state. It should avoid brittle cognitive choreography inside
the agent loop unless integrity or safety requires it.

## Current-State Canon Is Primary

The system of record is the current file at a stable path. History matters, but it
is secondary and should remain navigable through diffs, commits, and evidence links
rather than replacing current-state canon.

## Small Front Door, Rich Discoverability

Agents should start from a short, stable front door and discover deeper material
progressively. Large monolithic instruction blobs rot, crowd out task context, and
are hard to validate.

## Context Is Data, Not Plugin Code

The harness should operate on repository state, not import arbitrary Python from an
agent workspace. That keeps evolution reviewable and prevents hidden execution paths.

## Stable Machinery, Mutable State

The harness should change when execution behavior changes. Agent context repos should
change when goals, memory, bundles, or artifacts change.

## Narrow Interfaces Beat Ambient Access

If the harness can mutate anything anywhere, the architecture has no real boundary.
Expose explicit repository surfaces and approved output locations instead.

## Operational Evidence Is Not Memory

Runs, transcripts, tool traces, and validation logs are operational evidence. They
improve observability and handoff, but they must not become shadow canon for the
agent's current beliefs, objectives, or state.

## The Runtime Should Stay Thin

Runtime glue should assemble context, expose tools, persist sessions, and emit
telemetry. Domain truth, memory policy, and promotion rules should live in explicit
repository contracts and validation layers, not in fragile prompt wording.

## Evented Execution Beats Opaque Control Flow

The harness should model execution with explicit lifecycle primitives such as
threads, turns, items, approvals, and compaction boundaries so clients, operators,
and agents can inspect what happened without reverse-engineering runtime behavior.

## Parallelism Requires Isolation

Subagents should work in isolated worktrees or branches with explicit merge paths,
not by writing concurrently into one mutable shared tree.

## Future-Model Compatibility Is Required

New structure should clarify canon, contracts, validation, lifecycle boundaries, or
observability. Avoid coping patterns that only make sense for today's weaker models.

## Standard Library First

Core validation and repository operations should stay dependency-light so local use,
CI, and pip installation remain simple and reliable.
