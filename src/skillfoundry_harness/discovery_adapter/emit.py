"""Parse skillfoundry venture markdown → canon envelopes.

All four object types (CriticalAssumption, Probe, Evidence, Decision) use the
same header shape: a markdown H1 title followed by a bulleted list of
`- ``key``: ``value``` pairs, with optional prose sections below. This
adapter extracts the header dict and maps to canon envelopes per MAPPING.md.

No I/O — the caller writes envelopes to `.canon/` and runs the validator.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AdapterParseError(ValueError):
    """Raised when a markdown file contains a value the adapter cannot map
    unambiguously to a canon enum. Callers should log this as a friction
    event and skip the file rather than emitting a coerced envelope."""


def _resolve_enum(raw: str, mapping: dict[str, str],
                  field_name: str, source: "Path | str") -> str:
    result = mapping.get(raw)
    if result is None:
        raise AdapterParseError(
            f"{source}: unknown {field_name} value {raw!r}; "
            f"valid values: {sorted(mapping)}"
        )
    return result


SPEC_VERSION = "0.1.0"
EMITTER = "L3:skillfoundry"
LAYER = "L3"
INSTANCE_ID = "skillfoundry-valuation-context"

QUALITY_POLICY_ID = "skillfoundry.evidence_quality_note"
QUALITY_POLICY_VERSION = "1"


# --------------------------------------------------------------------------
# Markdown header parser
# --------------------------------------------------------------------------


_HEADER_LINE = re.compile(
    r"^\-\s+`(?P<key>[a-z_]+)`\s*:\s*`?(?P<val>[^`\n]*)`?\s*$"
)
_LIST_CONTINUATION = re.compile(r"^\s+\-\s+`?(?P<val>[^`\n]*)`?\s*$")


def parse_header(md_text: str) -> dict[str, Any]:
    """Extract `key: value` pairs from the markdown H1-adjacent bulleted list.

    Supports list-valued fields (evidence_refs in decisions). Stops at the
    first blank-after-list or the first H2 (`## `).

    Returns a dict; unknown keys pass through.
    """
    lines = md_text.splitlines()
    out: dict[str, Any] = {}
    current_key: str | None = None
    in_block = False

    for line in lines:
        # Start of header block: first bulleted key-value line
        m = _HEADER_LINE.match(line)
        if m:
            in_block = True
            current_key = m.group("key")
            val = m.group("val").strip()
            # Bare "(open)" / "(empty)" / etc. become None
            if val in ("", "(open)", "(empty)", "(n/a)", "null"):
                val = None
            # Line with no value content (just the key and a colon on its own)
            out[current_key] = val
            continue

        # Continuation inside a list-valued key
        if in_block and current_key:
            cm = _LIST_CONTINUATION.match(line)
            if cm:
                v = cm.group("val").strip()
                if not isinstance(out.get(current_key), list):
                    # Convert from singleton to list if needed
                    prev = out[current_key]
                    out[current_key] = [] if prev in (None, "", "(empty)") else [prev]
                out[current_key].append(v)
                continue

        # Blank line during the block: keep going if the next line is a
        # continuation or another header entry; break otherwise.
        if in_block and line.strip() == "":
            # Peek ahead isn't easy in a for-loop; just continue. The break
            # is handled by the H2 check below.
            continue

        # End the block on H2
        if in_block and line.startswith("## "):
            break
        if in_block and not line.startswith("-") and not line.startswith(" ") and line.strip() != "":
            # First non-list non-blank non-H2 prose line ends the block.
            break

    return out


# --------------------------------------------------------------------------
# Envelope helpers
# --------------------------------------------------------------------------


def _iso(ts: str | datetime | None, default: str | None = None) -> str:
    if ts is None and default is None:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if ts is None:
        return default  # type: ignore[return-value]
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return ts  # already in canonical form we can't reparse; trust
    else:
        dt = ts
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _sha256_str(s: str) -> str:
    return f"sha256:{hashlib.sha256(s.encode('utf-8')).hexdigest()}"


def _default_exposure() -> dict[str, Any]:
    """Skillfoundry venture probes run with negligible operational exposure
    pre-transaction. Capital-at-risk is bounded by the probe's build cost
    (already sunk); external exposure is information, not capital."""
    return {
        "capital_at_risk": 0,
        "reversibility": "reversible",
        "correlation_tags": ["skillfoundry-valuation"],
        "time_to_realization": "P14D",
        "blast_radius": "local",
    }


def _common_envelope(object_type: str, id_: str, emitted_at: str,
                     role_declared_at: str | None = None,
                     binding: str = "binding") -> dict[str, Any]:
    return {
        "id": id_,
        "spec_version": SPEC_VERSION,
        "object_type": object_type,
        "emitted_at": emitted_at,
        "emitter": EMITTER,
        "layer": LAYER,
        "roles": [object_type],
        "role_declared_at": role_declared_at or emitted_at,
        "binding": binding,
        "sources": [],
        "instance_id": INSTANCE_ID,
    }


def _artifact_pointer(md_path: Path, uri_base: str | None = None) -> dict[str, Any]:
    md_path = Path(md_path)
    uri = uri_base or f"file://{md_path}"
    return {
        "uri": uri,
        "content_hash": _sha256_file(md_path),
        "version": str(int(md_path.stat().st_mtime)),
        "media_type": "text/markdown",
    }


# --------------------------------------------------------------------------
# CriticalAssumption → Claim
# --------------------------------------------------------------------------


def parse_assumption(md_path: Path | str) -> dict[str, Any]:
    """skillfoundry CriticalAssumption markdown → canon Claim envelope.

    Canon Claim has a single `statement`. Skillfoundry assumptions carry
    three component claims (problem_claim, economic_claim, channel_claim)
    which together form one buyer story. We use `problem_claim` as the
    primary statement (it is the falsifiable commercial claim); the
    economic and channel claims are preserved in the markdown artifact
    via hash-bound ArtifactPointer.

    The `falsification_rule` prose becomes the sole entry in
    `falsification_criteria`.
    """
    md_path = Path(md_path)
    header = parse_header(md_path.read_text())

    if "assumption_id" not in header or "problem_claim" not in header:
        raise ValueError(f"{md_path}: missing assumption_id or problem_claim")

    emitted = _iso(header.get("created_at"))
    role_at = emitted
    envelope = _common_envelope(
        "Claim", header["assumption_id"], emitted, role_at,
    )
    envelope["statement"] = header["problem_claim"]
    envelope["falsification_criteria"] = [
        header.get("falsification_rule", "(no falsification rule provided)")
    ]
    envelope["thresholds"] = {}
    envelope["exposure"] = _default_exposure()
    envelope["artifact"] = _artifact_pointer(md_path)
    return envelope


# --------------------------------------------------------------------------
# Probe → EventLogEntry (phase_transition + methodology_log)
# --------------------------------------------------------------------------


def parse_probe(md_path: Path | str,
                decision_kind: str | None = None) -> list[dict[str, Any]]:
    """Probe markdown → list of EventLogEntry envelopes.

    Emits:
      1. phase_transition (draft → probe) at probe start
      2. methodology_log with ArtifactPointer to the probe markdown
      3. phase_transition (probe → promotion) ONLY when the caller passes
         decision_kind="promote" for a closed probe

    The L1 schema's phase_transition only models three phases: draft, probe,
    promotion. Killed/pivoted/closed probes do not get a closure event — the
    Decision envelope itself records the outcome. Passing decision_kind for a
    non-promote close therefore emits nothing extra.

    Returns a list (not single envelope) because a probe emits multiple events.
    """
    md_path = Path(md_path)
    header = parse_header(md_path.read_text())

    if "probe_id" not in header or "assumption_id" not in header:
        raise ValueError(f"{md_path}: missing probe_id or assumption_id")

    probe_id = header["probe_id"]
    claim_id = header["assumption_id"]
    started = _iso(header.get("started_at"))
    ended_raw = header.get("ended_at")
    ended = _iso(ended_raw) if ended_raw else None

    artifact = _artifact_pointer(md_path)
    events: list[dict[str, Any]] = []

    # 1. phase_transition draft → probe
    pt1 = _common_envelope(
        "EventLogEntry", f"pt-{probe_id}-draft-probe", started, started,
    )
    pt1["event_kind"] = "phase_transition"
    pt1["subject_id"] = claim_id
    pt1["phase_transition"] = {
        "claim_id": claim_id,
        "from_phase": "draft",
        "to_phase": "probe",
    }
    events.append(pt1)

    # 2. methodology_log at probe entry (canon.md Phase Invariants require this)
    ml = _common_envelope(
        "EventLogEntry", f"ml-{probe_id}", started, started,
    )
    ml["event_kind"] = "methodology_log"
    ml["subject_id"] = claim_id
    ml["methodology_log"] = {
        "artifact": artifact,
        "summary": header.get("probe_type", "manual probe"),
    }
    events.append(ml)

    # 3. phase_transition probe → promotion, only when caller confirms promote
    status = header.get("status")
    if status == "closed" and ended and decision_kind == "promote":
        pt2 = _common_envelope(
            "EventLogEntry", f"pt-{probe_id}-probe-promotion", ended, ended,
        )
        pt2["event_kind"] = "phase_transition"
        pt2["subject_id"] = claim_id
        pt2["phase_transition"] = {
            "claim_id": claim_id,
            "from_phase": "probe",
            "to_phase": "promotion",
        }
        events.append(pt2)

    return events


# --------------------------------------------------------------------------
# Evidence → Evidence
# --------------------------------------------------------------------------


_TIER_ALIASES = {
    # Skillfoundry writes the same 4 strings canon uses natively.
    "internal_operational": "internal_operational",
    "external_conversation": "external_conversation",
    "external_commitment": "external_commitment",
    "external_transaction": "external_transaction",
}


_POLARITY_MAP = {
    "supports_assumption": "supports",
    "contradicts_assumption": "contradicts",
    "neutral": "neutral",
    # Looser values observed in real files — all map to neutral because they
    # describe probe readiness/activation rather than assumption polarity.
    "lane_activation_only": "neutral",
    "lane_activation": "neutral",
    "activation_only": "neutral",
    "operational_readiness_only": "neutral",
}


def parse_evidence(md_path: Path | str) -> dict[str, Any]:
    """skillfoundry Evidence markdown → canon Evidence envelope."""
    md_path = Path(md_path)
    header = parse_header(md_path.read_text())

    for required in ("evidence_id", "assumption_id", "evidence_class"):
        if required not in header:
            raise ValueError(f"{md_path}: missing {required}")

    emitted = _iso(header.get("observed_at"))
    envelope = _common_envelope(
        "Evidence", header["evidence_id"], emitted, emitted,
    )
    envelope["claim_id"] = header["assumption_id"]
    envelope["evidence_type"] = header.get("source_type", "unspecified")

    tier_raw = header["evidence_class"]
    envelope["tier"] = _resolve_enum(tier_raw, _TIER_ALIASES, "evidence_class", md_path)

    supports_raw = header.get("supports", "neutral")
    envelope["polarity"] = _resolve_enum(supports_raw, _POLARITY_MAP, "supports", md_path)
    envelope["observed_at"] = emitted
    envelope["artifact"] = _artifact_pointer(md_path)
    return envelope


# --------------------------------------------------------------------------
# Decision → Decision
# --------------------------------------------------------------------------


_DECISION_KIND_MAP = {
    "continue": "continue",
    "tighten": "continue",  # skillfoundry-specific variant; flagged in rationale
    "pivot": "pivot",
    "pause": "continue",  # non-terminal pause preserves the claim; rationale carries the nuance
    "kill": "kill",
    "promote": "promote",
}


def parse_decision(md_path: Path | str) -> dict[str, Any]:
    """skillfoundry Decision markdown → canon Decision envelope.

    Skillfoundry's `decision_type` enum is richer than canon's (tighten,
    pause); the mapping folds them into the closest canon kind and
    preserves the nuance in `rationale` with an explicit "[skillfoundry-
    type=tighten]" prefix marker.
    """
    md_path = Path(md_path)
    text = md_path.read_text()
    header = parse_header(text)

    for required in ("decision_id", "assumption_id", "decision_type", "timestamp"):
        if required not in header:
            raise ValueError(f"{md_path}: missing {required}")

    emitted = _iso(header["timestamp"])
    decision_type_raw = header["decision_type"]
    kind = _resolve_enum(decision_type_raw, _DECISION_KIND_MAP, "decision_type", md_path)

    envelope = _common_envelope(
        "Decision", header["decision_id"], emitted, emitted,
    )
    envelope["kind"] = kind
    envelope["candidate_claims"] = [header["assumption_id"]]
    envelope["chosen_claim_id"] = header["assumption_id"]

    ev_refs = header.get("evidence_refs")
    if isinstance(ev_refs, str):
        ev_refs = [ev_refs] if ev_refs else []
    elif ev_refs is None:
        ev_refs = []
    envelope["cited_evidence"] = ev_refs

    rationale = header.get("rationale", "(no rationale provided)")
    if decision_type_raw != kind:
        rationale = f"[skillfoundry-type={decision_type_raw}] {rationale}"
    envelope["rationale"] = rationale

    envelope["policies_in_force"] = [
        {
            "policy_id": QUALITY_POLICY_ID,
            "version": QUALITY_POLICY_VERSION,
            "class": "operational",
        }
    ]
    envelope["exposure"] = _default_exposure()

    if kind == "promote":
        # skillfoundry decisions don't carry an explicit promotion_id;
        # synthesize one from the decision id.
        envelope["promotion_id"] = f"prom-{header['decision_id']}"

    return envelope


# --------------------------------------------------------------------------
# Policy — quality-field note
# --------------------------------------------------------------------------


def emit_policy_quality_note(effective_from: str | datetime | None = None) -> dict[str, Any]:
    """Policy capturing the semantics of skillfoundry's evidence_quality
    field (weak|moderate|strong), which has no direct canon field.

    canon.Evidence has `tier` (bindingness axis) but no quality axis. The
    quality label is preserved in the markdown artifact via ArtifactPointer;
    this Policy documents that interpretation so consumers can find it
    mechanically.
    """
    ts = effective_from or datetime.now(timezone.utc)
    emitted = _iso(ts) if not isinstance(ts, str) else ts

    envelope = _common_envelope(
        "Policy", QUALITY_POLICY_ID, emitted, emitted,
    )
    # Policy schema forbids instance_id
    envelope.pop("instance_id", None)
    envelope["class"] = "operational"
    envelope["scope"] = f"L3:{INSTANCE_ID}"
    envelope["field_path"] = "evidence.quality_label"
    envelope["value"] = {
        "location": "artifact body of each Evidence envelope",
        "values": ["weak", "moderate", "strong"],
        "note": (
            "Skillfoundry markdown Evidence records carry an "
            "`evidence_quality` label that canon does not model directly "
            "(canon.Evidence has `tier` for bindingness, not for quality). "
            "The label is preserved in the ArtifactPointer-referenced "
            "markdown and can be extracted by re-parsing the artifact if "
            "needed. Promoting quality to a first-class canon field "
            "requires a canon spec bump (v0.2.0)."
        ),
    }
    envelope["version"] = QUALITY_POLICY_VERSION
    envelope["issuer"] = EMITTER
    envelope["amendment_authority"] = [EMITTER, "human:evan"]
    envelope["ratification_rule"] = {
        "kind": "principal_signoff",
        "signatories": ["human:evan"],
    }
    envelope["rollback_rule"] = {
        "rules": [
            {
                "id": "canon_gains_quality_field",
                "condition": (
                    "canon.spec_version advances to include an Evidence.quality "
                    "field, at which point this Policy's note is obsolete"
                ),
            }
        ],
        "precedence": ["canon_gains_quality_field"],
    }
    envelope["provenance"] = [
        {"version": QUALITY_POLICY_VERSION, "effective_from": emitted}
    ]
    envelope["effective_from"] = emitted
    envelope["effective_until"] = None
    return envelope
