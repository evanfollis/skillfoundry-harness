"""Durable validation artifacts referenced by promotion proposals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .execution import slug_id, utc_now, validate_identifier
from .integrity import sha256_payload


ALLOWED_VALIDATION_STATUSES = {"passed", "failed"}


@dataclass(frozen=True)
class ValidationArtifact:
    """One durable validation result with provenance and evidence."""

    validation_id: str
    kind: str
    status: str
    created_at: str
    updated_at: str
    evidence_paths: tuple[str, ...]
    artifact_sha256: str
    summary: str | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    reviewer: str | None = None


class ValidationArtifactStore:
    """Create and load validation artifacts under artifacts/validations/."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def create(
        self,
        *,
        kind: str,
        status: str,
        evidence_paths: list[str],
        summary: str = "",
        thread_id: str | None = None,
        turn_id: str | None = None,
        reviewer: str | None = None,
    ) -> ValidationArtifact:
        if not kind.strip():
            raise ValueError("validation kind is required")
        if status not in ALLOWED_VALIDATION_STATUSES:
            raise ValueError(f"unsupported validation status: {status}")
        if thread_id is not None:
            validate_identifier("thread_id", thread_id)
        if turn_id is not None:
            validate_identifier("turn_id", turn_id)
        normalized_evidence: list[str] = []
        for evidence_path in evidence_paths:
            if not evidence_path.strip():
                raise ValueError("evidence path must be non-empty")
            resolved = self.repository.resolve_artifact_path(evidence_path)
            if not resolved.exists():
                raise ValueError(f"evidence path does not exist: {evidence_path}")
            normalized_evidence.append(evidence_path)
        artifact_payload = {
            "validation_id": slug_id("validation"),
            "kind": kind.strip(),
            "status": status,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "evidence_paths": tuple(normalized_evidence),
            "summary": summary or None,
            "thread_id": thread_id,
            "turn_id": turn_id,
            "reviewer": reviewer.strip() if reviewer else None,
        }
        artifact = ValidationArtifact(
            artifact_sha256=sha256_payload(self._artifact_payload(artifact_payload)),
            **artifact_payload,
        )
        self.repository.write_artifact_json(self._artifact_path(artifact.validation_id), self._serialize(artifact))
        return artifact

    def load(self, validation_id: str) -> ValidationArtifact:
        data = self.repository.read_artifact_json(self._artifact_path(validation_id))
        status = data.get("status")
        if status not in ALLOWED_VALIDATION_STATUSES:
            raise ValueError(f"validation {validation_id} has invalid status {status!r}")
        data["evidence_paths"] = tuple(data.get("evidence_paths", ()))
        stored_digest = data.get("artifact_sha256")
        candidate = ValidationArtifact(**data)
        expected_digest = sha256_payload(self._artifact_payload(self._serialize(candidate)))
        if stored_digest != expected_digest:
            raise ValueError(f"validation {validation_id} failed integrity check")
        return candidate

    def _artifact_path(self, validation_id: str) -> str:
        return f"validations/{validation_id}.json"

    def _serialize(self, artifact: ValidationArtifact) -> dict[str, Any]:
        return {
            "validation_id": artifact.validation_id,
            "kind": artifact.kind,
            "status": artifact.status,
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "evidence_paths": list(artifact.evidence_paths),
            "artifact_sha256": artifact.artifact_sha256,
            "summary": artifact.summary,
            "thread_id": artifact.thread_id,
            "turn_id": artifact.turn_id,
            "reviewer": artifact.reviewer,
        }

    def _artifact_payload(self, artifact: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in artifact.items() if key != "artifact_sha256"}
