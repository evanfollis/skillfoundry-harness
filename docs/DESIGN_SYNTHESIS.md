# External Design Synthesis

This document captures the strongest transferable ideas mined from public material
and from the earlier `maf-harness` docs. It exists to keep Skillfoundry aligned with
high-leverage design choices rather than drifting into ad hoc runtime glue.

## What Survived Across Sources

Several ideas appeared repeatedly across otherwise different systems:

- Current-state files should be the primary memory surface.
- History should remain available through diffs, commits, and event logs, but stay
  secondary to current canon.
- Agents need a small front door and progressive disclosure, not giant manuals.
- Runtime safety is better expressed as explicit capabilities, approvals, hooks, and
  validation than as prompt nagging.
- Parallel agent work requires isolated worktrees or branches and explicit merge
  paths.
- Runs need inspectable lifecycle primitives and traceability back to durable state.

## Source-Mined Ideas

### OpenAI: Harness Engineering

Source: [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)

Transferred ideas:

- Optimize the repository for agent legibility, not just human taste.
- Treat repository knowledge as the system of record; keep `AGENTS.md` short and use
  it as a table of contents into a structured docs corpus.
- Expose the app, UI, logs, metrics, and traces directly to the agent so it can
  validate its own work.
- Prefer worktree-local environments so one task can boot, inspect, and tear down an
  isolated copy of the world.
- Push review and iteration into explicit feedback loops rather than relying on one
  prompt pass.

### OpenAI: App Server

Source: [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/)

Transferred ideas:

- Separate durable conversation containers from individual work units.
- Model execution with stable primitives: thread, turn, and item.
- Stream item lifecycles explicitly (`started`, `delta`, `completed`) so UIs and
  logs can render partial state faithfully.
- Pause turns for approvals instead of smuggling approvals into unstructured text.

### OpenAI: Agent Loop

Source: [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

Transferred ideas:

- Keep requests stateless when possible and preserve exact prompt prefixes to
  maximize caching.
- Represent context as ordered items appended over time instead of mutating hidden
  runtime state.
- Treat compaction as a first-class lifecycle boundary with its own artifact, not as
  an ad hoc summarization hack.
- When environment or permission state changes mid-run, append a new explicit item
  describing the change instead of rewriting older context.

### Letta: Context Repositories

Source: [Introducing Context Repositories](https://www.letta.com/blog/context-repositories)

Transferred ideas:

- Filesystem-backed memory is a strong primitive because both humans and agents can
  inspect and manipulate it directly.
- Git-backed memory enables divergence, offline processing, and merge-based
  reconciliation.
- Progressive disclosure should be encoded in the tree structure and file metadata.
- Reflection, initialization, and defragmentation are better run as background or
  side worktrees than inline with the main task loop.
- Memory maintenance can be delegated to subagents that merge back into canon.

### DiffMem

Source: [Growth-Kinetics/DiffMem](https://github.com/Growth-Kinetics/DiffMem)

Transferred ideas:

- Separate surface from depth: default reads should hit current-state files, with
  targeted dives into git history only when needed.
- Markdown plus git is often enough; avoid introducing vector stores or opaque
  storage unless a real retrieval bottleneck appears.
- Retrieval should use the same primitives a human would use: index files, targeted
  file reads, diffs, commit logs, and blame/history when necessary.
- Commits should remain explicit and atomic.

### Public Claude Code Docs

Sources:

- [How Claude remembers your project](https://code.claude.com/docs/en/memory)
- [Slash commands / skills](https://code.claude.com/docs/en/slash-commands)
- [Hooks reference](https://code.claude.com/docs/en/hooks)

Transferred ideas:

- Layer project instructions by scope and load path-specific rules lazily.
- Keep top-level instruction files concise; break larger policy into modular rules.
- Skills should be structured artifacts with metadata about invocation, tool access,
  and execution context.
- Hook surfaces should support decision control before and after actions, including
  allow, deny, ask, defer, and context injection.
- Subagents should have explicit start/stop hooks and their own scoped memory or
  transcripts instead of silently sharing all state.

### `maf-harness`

Local source:

- PRINCIPLES.md (maf-harness, historical predecessor)
- architecture.md (maf-harness, historical predecessor)
- context-model.md (maf-harness, historical predecessor)

Transferred ideas:

- Current-state canon beats transcript memory.
- Validation and promotion are the main safety boundary.
- The runtime should remain thin and legible.
- Operational evidence is not memory.
- Initialization, work, and handoff should be explicit lifecycle phases.
- Durable changes should carry trace identifiers back to the run that produced them.

## What Not To Copy Forward

- SQL as the mandatory system of record. That was a constraint of the earlier
  architecture, not obviously an advantage here.
- Any runtime behavior that only exists in prompt glue.
- Any design that turns transcripts or run logs into a second canon.
- Any agent memory model that requires loading the entire workspace eagerly.

## Implications For Skillfoundry

The next harness primitives should be:

1. A front-door manifest for context repos that pins a small set of always-loaded
   files plus discoverable directories and summaries.
2. A run model with explicit `thread`, `turn`, `item`, and `run` semantics.
3. A promotion model that distinguishes branch-local work from accepted canon.
4. A worktree-based subagent model for reflection, review, and maintenance.
5. A hook/policy layer for approvals, bounded writes, and post-action validation.
6. A compaction protocol so continuity survives long-running work without bloating
   startup context.

All six primitives are now implemented in the harness.
