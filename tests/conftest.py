"""Test-level isolation fixtures (synthesis Proposal 5b).

Why this file exists: ``discovery_adapter/migrate.py`` writes one telemetry
event per ``migrate()`` invocation to the workspace-shared sink at
``/opt/workspace/runtime/.telemetry/events.jsonl``. Without isolation, every
test that drives ``migrate()`` (directly or transitively) lands a real event
on the operational stream — visible historically as ``sourceType: user``
events whose ``details.venture_root`` is under ``/tmp/pytest-of-root/...``.

Two layers of redirection here, both required:

1. ``SKILLFOUNDRY_TELEMETRY_PATH`` env var — covers any future code path or
   subprocess that re-reads the env var at call time.
2. ``migrate.TELEMETRY_PATH`` module attribute — required because the
   production module reads the env var **at import time** and binds the
   resulting Path to a module-level constant. By the time pytest fixtures
   run, that constant is already set; an env-var-only fixture would be a
   no-op for any test that imports ``migrate`` at collection time.

Tests that need their own redirection (e.g. to assert event content from a
specific path) can still use ``monkeypatch.setattr`` on the same attribute;
monkeypatch's per-test override layers cleanly on top of this autouse.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_ENV_VAR = "SKILLFOUNDRY_TELEMETRY_PATH"


@pytest.fixture(autouse=True)
def isolate_telemetry_sink(tmp_path, monkeypatch):
    """Redirect every test's telemetry emissions to a tmp path.

    Idempotent and safe to layer with explicit ``monkeypatch.setattr`` calls
    inside individual tests — those override this fixture's defaults and
    monkeypatch's own teardown restores both.
    """
    sink = tmp_path / "events.jsonl"
    monkeypatch.setenv(_ENV_VAR, str(sink))

    # Also patch the live module attribute, since migrate.py captures the
    # env var into TELEMETRY_PATH at import time. Skip cleanly if the module
    # hasn't been imported yet (e.g. for tests that don't touch migrate).
    try:
        from skillfoundry_harness.discovery_adapter import migrate as migrate_mod
    except Exception:
        return
    monkeypatch.setattr(migrate_mod, "TELEMETRY_PATH", Path(sink), raising=False)
