"""Smoke tests for the skillfoundry discovery adapter.

Each test writes a minimal markdown fixture to a tmp dir, calls the
corresponding parse_* function, and asserts the resulting canon envelope
has the expected core fields. Schema-level validation is exercised by
`python -m skillfoundry_harness.discovery_adapter.migrate --dry-run`;
these tests are lighter-weight shape checks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillfoundry_harness.discovery_adapter import (
    AdapterParseError,
    emit_policy_quality_note,
    parse_assumption,
    parse_decision,
    parse_evidence,
    parse_probe,
)
from skillfoundry_harness.discovery_adapter import schema_bundle
from skillfoundry_harness.discovery_adapter.migrate import DEFAULT_SCHEMA_DIR


# The harness ships a pinned copy of the L1 canon schemas (schemas/discovery/) so
# migrate()'s success path is exercised hermetically here — DEFAULT_SCHEMA_DIR now
# points at that bundle, which is always present. No test skips the success path.
#
# Two separate guards keep that bundle honest:
#   * integrity — bundle files match their recorded digests (runs everywhere);
#   * drift     — bundle matches the canonical context-repository source (runs
#                 wherever canon is reachable: the workspace, or CI via a
#                 checkout that sets SKILLFOUNDRY_CANON_SCHEMA_DIR).


ASSUMPTION_MD = """\
# CriticalAssumption: demo

- `assumption_id`: `demo`
- `title`: `demo title`
- `status`: `active`
- `owner`: `skillfoundry`
- `buyer_role`: `demo buyer`
- `problem_claim`: `Demo buyers need a thing`
- `economic_claim`: `They will pay`
- `channel_claim`: `Direct email works`
- `falsification_rule`: `If nobody engages, claim is wrong`
- `next_probe_id`: `demo-probe`
- `created_at`: `2026-04-10T00:00:00Z`
- `updated_at`: `2026-04-10T00:00:00Z`
"""


PROBE_MD = """\
# Probe: demo-probe

- `probe_id`: `demo-probe`
- `assumption_id`: `demo`
- `probe_type`: `manual_offer`
- `artifact_class`: `service_probe`
- `target_evidence_class`: `external_conversation`
- `minimum_evidence_quality`: `moderate`
- `success_rule`: `any builder engages`
- `falsification_rule`: `no builder engages after 14d`
- `started_at`: `2026-04-10T00:00:00Z`
- `ended_at`: `(open)`
- `status`: `active`
- `owner`: `skillfoundry`
"""


EVIDENCE_MD = """\
# Evidence: 2026-04-12 first external reply

- `evidence_id`: `2026-04-12-first-external-reply`
- `assumption_id`: `demo`
- `probe_id`: `demo-probe`
- `evidence_class`: `external_conversation`
- `evidence_quality`: `moderate`
- `source_type`: `email_reply`
- `source_identity`: `anon-builder-1`
- `observed_at`: `2026-04-12T10:00:00Z`
- `summary`: `Builder expressed interest`
- `raw_pointer`: `memory/venture/evidence/raw/…`
- `supports`: `supports_assumption`
- `confidence`: `moderate`
"""


DECISION_MD = """\
# Decision: 2026-04-13 continue demo

- `decision_id`: `2026-04-13-continue-demo`
- `assumption_id`: `demo`
- `probe_id`: `demo-probe`
- `decision_type`: `tighten`
- `timestamp`: `2026-04-13T00:00:00Z`
- `owner`: `skillfoundry`
- `evidence_refs`:
  - `2026-04-12-first-external-reply`
- `rationale`: `one positive signal is enough to tighten`
"""


@pytest.fixture
def fixtures(tmp_path: Path):
    (tmp_path / "assumption.md").write_text(ASSUMPTION_MD)
    (tmp_path / "probe.md").write_text(PROBE_MD)
    (tmp_path / "evidence.md").write_text(EVIDENCE_MD)
    (tmp_path / "decision.md").write_text(DECISION_MD)
    return tmp_path


def test_parse_assumption(fixtures):
    c = parse_assumption(fixtures / "assumption.md")
    assert c["object_type"] == "Claim"
    assert c["id"] == "demo"
    assert c["statement"] == "Demo buyers need a thing"
    assert c["falsification_criteria"] == [
        "If nobody engages, claim is wrong"
    ]
    assert c["emitter"] == "L3:skillfoundry"
    assert c["binding"] == "binding"
    assert c["exposure"]["capital_at_risk"] == 0
    assert c["instance_id"] == "skillfoundry-valuation-context"
    assert c["artifact"]["content_hash"].startswith("sha256:")


def test_parse_probe_emits_three_events_when_closed(fixtures):
    # Active probe: 2 events (phase_transition draft→probe + methodology_log)
    events = parse_probe(fixtures / "probe.md")
    assert len(events) == 2
    assert events[0]["event_kind"] == "phase_transition"
    assert events[0]["phase_transition"]["from_phase"] == "draft"
    assert events[0]["phase_transition"]["to_phase"] == "probe"
    assert events[1]["event_kind"] == "methodology_log"
    assert events[1]["methodology_log"]["artifact"]["content_hash"].startswith("sha256:")


def test_parse_probe_closed_no_decision_kind_emits_two_events(fixtures, tmp_path):
    # Without a decision_kind, a closed probe emits no closure event.
    # The Decision envelope records the outcome; L1 has no "killed" phase.
    closed = PROBE_MD.replace(
        "- `ended_at`: `(open)`\n- `status`: `active`",
        "- `ended_at`: `2026-04-20T00:00:00Z`\n- `status`: `closed`",
    )
    p = tmp_path / "probe_closed.md"
    p.write_text(closed)
    events = parse_probe(p)
    assert len(events) == 2


def test_parse_probe_closed_with_promote_emits_three_events(fixtures, tmp_path):
    closed = PROBE_MD.replace(
        "- `ended_at`: `(open)`\n- `status`: `active`",
        "- `ended_at`: `2026-04-20T00:00:00Z`\n- `status`: `closed`",
    )
    p = tmp_path / "probe_closed_promote.md"
    p.write_text(closed)
    events = parse_probe(p, decision_kind="promote")
    assert len(events) == 3
    assert events[-1]["phase_transition"]["from_phase"] == "probe"
    assert events[-1]["phase_transition"]["to_phase"] == "promotion"


def test_parse_probe_closed_with_kill_emits_two_events(fixtures, tmp_path):
    # Killed probe: Decision records the kill; no L1 phase_transition emitted.
    closed = PROBE_MD.replace(
        "- `ended_at`: `(open)`\n- `status`: `active`",
        "- `ended_at`: `2026-04-20T00:00:00Z`\n- `status`: `closed`",
    )
    p = tmp_path / "probe_closed_kill.md"
    p.write_text(closed)
    events = parse_probe(p, decision_kind="kill")
    assert len(events) == 2


def test_parse_probe_closed_with_pivot_emits_two_events(fixtures, tmp_path):
    closed = PROBE_MD.replace(
        "- `ended_at`: `(open)`\n- `status`: `active`",
        "- `ended_at`: `2026-04-20T00:00:00Z`\n- `status`: `closed`",
    )
    p = tmp_path / "probe_closed_pivot.md"
    p.write_text(closed)
    events = parse_probe(p, decision_kind="pivot")
    assert len(events) == 2


def test_parse_evidence_polarity_and_tier(fixtures):
    e = parse_evidence(fixtures / "evidence.md")
    assert e["object_type"] == "Evidence"
    assert e["tier"] == "external_conversation"
    assert e["polarity"] == "supports"
    assert e["claim_id"] == "demo"
    assert e["evidence_type"] == "email_reply"


def test_parse_evidence_lane_activation_neutral(fixtures, tmp_path):
    alt = EVIDENCE_MD.replace(
        "- `supports`: `supports_assumption`",
        "- `supports`: `lane_activation_only`",
    )
    p = tmp_path / "evidence_activation.md"
    p.write_text(alt)
    e = parse_evidence(p)
    assert e["polarity"] == "neutral"


def test_parse_decision_tighten_maps_to_continue(fixtures):
    d = parse_decision(fixtures / "decision.md")
    assert d["object_type"] == "Decision"
    assert d["kind"] == "continue"
    assert d["rationale"].startswith("[skillfoundry-type=tighten]")
    assert d["candidate_claims"] == ["demo"]
    assert d["chosen_claim_id"] == "demo"
    assert d["cited_evidence"] == ["2026-04-12-first-external-reply"]


@pytest.mark.parametrize(
    "decision_type,expected_kind,expected_marker",
    [
        ("continue", "continue", None),
        ("tighten", "continue", "[skillfoundry-type=tighten]"),
        ("pivot", "pivot", None),
        ("pause", "continue", "[skillfoundry-type=pause]"),
        ("kill", "kill", None),
    ],
)
def test_decision_kind_mapping(tmp_path, decision_type, expected_kind,
                               expected_marker):
    md = DECISION_MD.replace(
        "- `decision_type`: `tighten`",
        f"- `decision_type`: `{decision_type}`",
    )
    p = tmp_path / "d.md"
    p.write_text(md)
    d = parse_decision(p)
    assert d["kind"] == expected_kind
    if expected_marker:
        assert d["rationale"].startswith(expected_marker)


def test_policy_shape():
    p = emit_policy_quality_note()
    assert p["object_type"] == "Policy"
    assert p["class"] == "operational"
    assert p["scope"] == "L3:skillfoundry-valuation-context"
    assert "instance_id" not in p  # Policy schema forbids
    assert p["value"]["values"] == ["weak", "moderate", "strong"]


# --------------------------------------------------------------------------
# Finding 2 — unknown enum values must raise AdapterParseError, not coerce
# --------------------------------------------------------------------------


def test_evidence_unknown_tier_raises(tmp_path):
    bad = EVIDENCE_MD.replace(
        "- `evidence_class`: `external_conversation`",
        "- `evidence_class`: `commercial_signal`",
    )
    p = tmp_path / "evidence_bad_tier.md"
    p.write_text(bad)
    with pytest.raises(AdapterParseError, match="evidence_class"):
        parse_evidence(p)


def test_evidence_unknown_polarity_raises(tmp_path):
    bad = EVIDENCE_MD.replace(
        "- `supports`: `supports_assumption`",
        "- `supports`: `strongly_supports`",
    )
    p = tmp_path / "evidence_bad_polarity.md"
    p.write_text(bad)
    with pytest.raises(AdapterParseError, match="supports"):
        parse_evidence(p)


def test_decision_unknown_type_raises(tmp_path):
    bad = DECISION_MD.replace(
        "- `decision_type`: `tighten`",
        "- `decision_type`: `approved`",
    )
    p = tmp_path / "decision_bad_type.md"
    p.write_text(bad)
    with pytest.raises(AdapterParseError, match="decision_type"):
        parse_decision(p)


def test_known_lane_activation_polarity_still_maps(tmp_path):
    # lane_activation_only is a known alias in _POLARITY_MAP; must not raise.
    md = EVIDENCE_MD.replace(
        "- `supports`: `supports_assumption`",
        "- `supports`: `lane_activation_only`",
    )
    p = tmp_path / "evidence_lane.md"
    p.write_text(md)
    e = parse_evidence(p)
    assert e["polarity"] == "neutral"


# --------------------------------------------------------------------------
# Post-review Finding B — migrate.py pre-pass must not swallow decision
# header parse failures silently.
# --------------------------------------------------------------------------


def test_migrate_prepass_surfaces_bad_decision_header(
    tmp_path, capsys, monkeypatch
):
    from skillfoundry_harness.discovery_adapter import migrate as migrate_mod
    from skillfoundry_harness.discovery_adapter.migrate import (
        DEFAULT_SCHEMA_DIR,
        migrate,
    )

    venture = tmp_path / "venture"
    mv = venture / "memory" / "venture"
    for sub in ("assumptions", "probes", "evidence", "decisions"):
        (mv / sub).mkdir(parents=True)
    (mv / "assumptions" / "demo.md").write_text(ASSUMPTION_MD)
    (mv / "probes" / "demo-probe.md").write_text(PROBE_MD)
    (mv / "evidence" / "2026-04-12-first-external-reply.md").write_text(
        EVIDENCE_MD
    )
    (mv / "decisions" / "2026-04-13-bad.md").write_text(DECISION_MD)

    # Simulate a parse_header failure on the decision file during the pre-pass
    # (rare but real class of error: encoding issues, mid-file read corruption,
    # or a future header-format migration that raises on legacy files).
    real_parse_header = migrate_mod.parse_header

    def flaky_parse_header(text):
        if text.startswith("# Decision:"):
            raise ValueError("simulated header parse failure")
        return real_parse_header(text)

    monkeypatch.setattr(migrate_mod, "parse_header", flaky_parse_header)

    rc = migrate(venture, DEFAULT_SCHEMA_DIR, dry_run=True)

    err = capsys.readouterr().err
    assert "[PREPASS-DECISION]" in err, (
        "pre-pass must surface bad decision header on stderr; silent skip was "
        "post-review Finding B"
    )
    assert "2026-04-13-bad.md" in err
    assert "probe closure edge" in err  # loss-of-edge framing preserved
    assert rc != 0


# --------------------------------------------------------------------------
# Workspace compliance: migrate must emit one structured telemetry event
# per run (CLAUDE.md S1-P2). Cycle-12 carry-forward — fix in 2026-05-03.
# --------------------------------------------------------------------------


def test_migrate_emits_telemetry_event_per_run(tmp_path, monkeypatch):
    from skillfoundry_harness.discovery_adapter import migrate as migrate_mod
    from skillfoundry_harness.discovery_adapter.migrate import (
        DEFAULT_SCHEMA_DIR,
        migrate,
    )

    venture = tmp_path / "venture"
    mv = venture / "memory" / "venture"
    for sub in ("assumptions", "probes", "evidence", "decisions"):
        (mv / sub).mkdir(parents=True)
    (mv / "assumptions" / "demo.md").write_text(ASSUMPTION_MD)
    (mv / "probes" / "demo-probe.md").write_text(PROBE_MD)
    (mv / "evidence" / "2026-04-12-first-external-reply.md").write_text(
        EVIDENCE_MD
    )
    (mv / "decisions" / "2026-04-13-good.md").write_text(DECISION_MD)

    sink = tmp_path / "events.jsonl"
    monkeypatch.setattr(migrate_mod, "TELEMETRY_PATH", sink)

    rc = migrate(venture, DEFAULT_SCHEMA_DIR, dry_run=True, source_type="cron")
    assert rc == 0

    assert sink.exists(), "telemetry sink file must be created on success"
    lines = sink.read_text().strip().splitlines()
    assert len(lines) == 1, f"exactly one event per migrate run, got {len(lines)}"
    ev = json.loads(lines[0])

    # Required workspace shape (CLAUDE.md S1-P2).
    for key in ("project", "source", "eventType", "level", "timestamp", "sourceType"):
        assert key in ev, f"telemetry missing required field: {key}"

    assert ev["project"] == "skillfoundry-harness"
    assert ev["source"] == "skillfoundry_harness.discovery_adapter.migrate"
    assert ev["sourceType"] == "cron"
    assert ev["level"] == "info"
    assert ev["eventType"] == "migrate.success"
    assert isinstance(ev["timestamp"], int)  # epoch milliseconds, not ISO string
    assert ev["details"]["dry_run"] is True
    assert ev["details"]["counts"]["claims"]["ok"] == 1
    assert ev["details"]["total_bad"] == 0


def test_migrate_emits_failure_telemetry_when_venture_missing(
    tmp_path, monkeypatch, capsys
):
    from skillfoundry_harness.discovery_adapter import migrate as migrate_mod
    from skillfoundry_harness.discovery_adapter.migrate import (
        DEFAULT_SCHEMA_DIR,
        migrate,
    )

    sink = tmp_path / "events.jsonl"
    monkeypatch.setattr(migrate_mod, "TELEMETRY_PATH", sink)

    rc = migrate(
        tmp_path / "no-venture-here",
        DEFAULT_SCHEMA_DIR,
        dry_run=True,
        source_type="cron",
    )
    capsys.readouterr()  # drain the "no memory/venture" message
    assert rc == 2

    lines = sink.read_text().strip().splitlines()
    assert len(lines) == 1
    ev = json.loads(lines[0])

    # This failure path returns before any schema is loaded, so it runs in CI
    # even when the canon schemas are absent. That makes it the right place to
    # assert the workspace-mandated telemetry field shape (CLAUDE.md S1-P2),
    # so the contract is verified everywhere — not only where canon is present.
    for key in ("project", "source", "eventType", "level", "timestamp", "sourceType"):
        assert key in ev, f"telemetry missing required field: {key}"
    assert ev["project"] == "skillfoundry-harness"
    assert ev["source"] == "skillfoundry_harness.discovery_adapter.migrate"
    assert ev["sourceType"] == "cron"  # source_type passes through
    assert isinstance(ev["timestamp"], int)  # epoch millis, not ISO string
    assert ev["eventType"] == "migrate.failure"
    assert ev["level"] == "error"
    assert "memory/venture not found" in ev["details"]["error"]


# --------------------------------------------------------------------------
# Canon schema bundle: self-sufficiency + drift guards.
#
# The harness vendors a pinned copy of the L1 discovery-framework schemas so it
# can validate canon envelopes without the sibling context-repository checked
# out. These guards keep that copy trustworthy.
# --------------------------------------------------------------------------


def test_default_schema_dir_is_the_bundled_copy():
    # DEFAULT_SCHEMA_DIR must resolve inside the installed package (self-
    # sufficient), not an absolute path into a sibling repo.
    assert DEFAULT_SCHEMA_DIR == schema_bundle.BUNDLE_DIR
    assert (DEFAULT_SCHEMA_DIR / "common.schema.json").is_file()


def test_bundled_schemas_pass_manifest_integrity():
    # Hermetic: shipped files match their recorded digests, and the manifest and
    # the on-disk bundle agree on the file set. Runs everywhere, including CI.
    problems = schema_bundle.verify_bundle_integrity()
    assert problems == [], "bundle integrity problems:\n  " + "\n  ".join(problems)


def test_bundled_schemas_match_canonical_source():
    # Drift guard: the pinned bundle must be an exact mirror of the canonical
    # context-repository schemas. Needs the canon source; CI provides it via a
    # checkout that sets SKILLFOUNDRY_CANON_SCHEMA_DIR. When canon is genuinely
    # unreachable (e.g. an offline checkout with the env var unset) this skips
    # with a reason — that is a missing *reference for comparison*, not a skipped
    # core code path; migrate()'s success path is exercised against the bundle by
    # the tests above regardless.
    canon_dir = schema_bundle.canonical_schema_dir()
    if canon_dir is None:
        pytest.skip(
            "canonical context-repository schemas not reachable "
            f"(set {schema_bundle.CANON_ENV_VAR} to a checkout to enable drift "
            "detection here; it runs in the workspace and in CI)"
        )
    drift = schema_bundle.diff_against_canon(canon_dir)
    assert drift == [], (
        "vendored schema bundle has drifted from canon at "
        f"{canon_dir}:\n  " + "\n  ".join(drift) + "\n"
        "Refresh it: python3 scripts/refresh_discovery_schema_bundle.py "
        "--canon <context-repository path>, then commit the bundle + manifest."
    )
