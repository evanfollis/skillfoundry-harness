"""Canon adapter — emits discovery-framework canon envelopes from skillfoundry
markdown records under `skillfoundry-valuation-context/memory/venture/`.

The skillfoundry venture layer (CriticalAssumption / Probe / Evidence /
Decision) is a markdown-first ontology: each object is a markdown file with
a backtick-keyed header list (see README.md in each subdirectory). This
adapter parses the markdown, extracts the structured metadata, and emits
canon envelopes conforming to the L1 spec at
/opt/workspace/projects/context-repository/spec/discovery-framework/ (v0.1.0).

The adapter is additive — the markdown files remain the authoring surface
and are unchanged.

Public API:
    parse_assumption(md_path)  -> canon Claim dict
    parse_probe(md_path)       -> (phase_transition, methodology_log) events
    parse_evidence(md_path)    -> canon Evidence dict
    parse_decision(md_path)    -> canon Decision dict
    emit_policy_quality_note() -> canon Policy capturing the quality-field note
"""

from .emit import (
    EMITTER,
    INSTANCE_ID,
    LAYER,
    SPEC_VERSION,
    emit_policy_quality_note,
    parse_assumption,
    parse_decision,
    parse_evidence,
    parse_probe,
)

__all__ = [
    "EMITTER",
    "INSTANCE_ID",
    "LAYER",
    "SPEC_VERSION",
    "emit_policy_quality_note",
    "parse_assumption",
    "parse_decision",
    "parse_evidence",
    "parse_probe",
]
