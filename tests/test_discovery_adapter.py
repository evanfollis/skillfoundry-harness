"""Smoke tests for the skillfoundry discovery adapter.

Each test writes a minimal markdown fixture to a tmp dir, calls the
corresponding parse_* function, and asserts the resulting canon envelope
has the expected core fields. Schema-level validation is exercised by
`python -m skillfoundry_harness.discovery_adapter.migrate --dry-run`;
these tests are lighter-weight shape checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skillfoundry_harness.discovery_adapter import (
    emit_policy_quality_note,
    parse_assumption,
    parse_decision,
    parse_evidence,
    parse_probe,
)


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


def test_parse_probe_closed_emits_three_events(fixtures, tmp_path):
    closed = PROBE_MD.replace(
        "- `ended_at`: `(open)`\n- `status`: `active`",
        "- `ended_at`: `2026-04-20T00:00:00Z`\n- `status`: `closed`",
    )
    p = tmp_path / "probe_closed.md"
    p.write_text(closed)
    events = parse_probe(p)
    assert len(events) == 3
    assert events[-1]["phase_transition"]["from_phase"] == "probe"
    assert events[-1]["phase_transition"]["to_phase"] == "promotion"


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
