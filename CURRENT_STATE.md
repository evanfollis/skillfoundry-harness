# CURRENT_STATE — skillfoundry-harness

**Last verified**: 2026-09-05

## Operational state

- Generic Python harness and discovery-to-canon adapter are healthy.
- `make check` passes: repository hygiene, Ruff, 67 tests, and `git diff --check`.
- The adapter validates against the bundled canon v0.2.0 schemas.
- Policy emission is deterministic: policy v1 retains its original effective date instead of using migration time.

## Skillfoundry portfolio context

- Preflight is live at `https://preflight.skillfoundry.workers.dev/`. Recent traffic is dominated by known automation; unattributed traffic is not called human demand without a tool call or stronger evidence.
- Launchpad Lint is live at `https://skillfoundry.synaplex.ai/products/launchpad-lint/`, with a useful HTML landing page and a production-isolated telemetry path. Its AgenticMarket listing has five installs and one star, but no verified production completion or payment evidence.
- The Skillfoundry index at `https://skillfoundry.synaplex.ai/` is functional.
- Launch Compliance Intelligence remains intentionally parked. Its landing page is not treated as an active commercial probe.
- The expired Launchpad Lint Stage-1 probe is closed and retained under passive portfolio measurement; one completed production tool call or paid event can reopen it.

## Known limitations

- The markdown adapter intentionally collapses each three-part critical assumption into one canon envelope. `MAPPING.md` records this as lossy by design pending a versioned mapping change.
- The pure-parse interface ADR remains accepted but unscheduled.
- Opposing-model review is currently unavailable because the configured Claude OAuth session is expired. Local tests and Codex review are the available fallback; review artifacts must state this limitation rather than claiming an independent Claude review.

## Next safe action

Keep the harness generic. Run `make check` before delivery, run discovery migrations twice when changing emission semantics, and require an unchanged second result as the idempotence check.
