# Repo Policy

The harness repo should contain stable machinery, not workspace state.

## Forbidden Content

- Agent registry data.
- Long-lived agent memory, bundles, artifacts, or runs.
- Agent-specific prompt corpora or notes.
- A checked-in context repo at the root of this repository.

## Allowed Exceptions

- Test fixtures under `tests/fixtures/`.
- Small documentation snippets that illustrate repository contracts.
- Canonical schemas and validators.
- Generic repository contract examples.

## Review Heuristic

If a change describes "how any compliant agent repo should work," it likely belongs
here. If it describes "what this one agent currently knows or is doing," it does not.
