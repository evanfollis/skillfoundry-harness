# AGENTS.md

## Mission

Build the harness as the stable execution substrate for Skillfoundry agents. Own the
canonical contracts, repository interfaces, and runtime semantics.

## Required Behaviors

- Keep the package installable and dependency-light.
- Treat agent context repositories as external workspaces governed by explicit contracts.
- Prefer first-class APIs over implicit filesystem conventions when the surface matters.
- Make breaking contract changes obvious in docs, tests, and CLI behavior.

## Editing Rules

- Do not add agent-specific bundles, memory, or long-lived workspace data here.
- Do not import code from agent context repositories.
- When adding a new repository invariant, update tests and user-facing validation output.
- Keep CLI surfaces thin wrappers around package APIs.

## Review Standard

A harness change is incomplete if it does not answer:

- What stable interface changed?
- What repository contract does it depend on?
- How does a context repo discover or satisfy that contract?
- What test proves the behavior?
