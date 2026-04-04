"""Durable approval artifacts referenced by promotion proposals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .execution import slug_id, utc_now, validate_identifier
from .integrity import sha256_payload


ALLOWED_APPROVAL_STATUSES = {"approved", "rejected"}


@dataclass(frozen=True)
class ApprovalArtifact:
    """One durable approval decision tied to a proposal."""

    approval_id: str
    proposal_id: str
    proposal_change_sha256: str
    status: str
    reviewer: str
    created_at: str
    updated_at: str
    artifact_sha256: str
    notes: str | None = None
    thread_id: str | None = None
    turn_id: str | None = None


class ApprovalArtifactStore:
    """Create and load approval artifacts under artifacts/approvals/."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def create(
        self,
        *,
        proposal_id: str,
        proposal_change_sha256: str,
        status: str,
        reviewer: str,
        notes: str = "",
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> ApprovalArtifact:
        validate_identifier("proposal_id", proposal_id)
        if status not in ALLOWED_APPROVAL_STATUSES:
            raise ValueError(f"unsupported approval status: {status}")
        reviewer_value = reviewer.strip()
        if not reviewer_value:
            raise ValueError("reviewer is required for approval artifact")
        if not proposal_change_sha256:
            raise ValueError("proposal_change_sha256 is required for approval artifact")
        if thread_id is not None:
            validate_identifier("thread_id", thread_id)
        if turn_id is not None:
            validate_identifier("turn_id", turn_id)
        artifact_payload = {
            "approval_id": slug_id("approval"),
            "proposal_id": proposal_id,
            "proposal_change_sha256": proposal_change_sha256,
            "status": status,
            "reviewer": reviewer_value,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "notes": notes or None,
            "thread_id": thread_id,
            "turn_id": turn_id,
        }
        artifact = ApprovalArtifact(
            artifact_sha256=sha256_payload(self._artifact_payload(artifact_payload)),
            **artifact_payload,
        )
        self.repository.write_artifact_json(self._artifact_path(artifact.approval_id), self._serialize(artifact))
        return artifact

    def load(self, approval_id: str) -> ApprovalArtifact:
        data = self.repository.read_artifact_json(self._artifact_path(approval_id))
        status = data.get("status")
        if status not in ALLOWED_APPROVAL_STATUSES:
            raise ValueError(f"approval {approval_id} has invalid status {status!r}")
        stored_digest = data.get("artifact_sha256")
        candidate = ApprovalArtifact(**data)
        expected_digest = sha256_payload(self._artifact_payload(self._serialize(candidate)))
        if stored_digest != expected_digest:
            raise ValueError(f"approval {approval_id} failed integrity check")
        return candidate

    def _artifact_path(self, approval_id: str) -> str:
        return f"approvals/{approval_id}.json"

    def _serialize(self, artifact: ApprovalArtifact) -> dict[str, Any]:
        return {
            "approval_id": artifact.approval_id,
            "proposal_id": artifact.proposal_id,
            "proposal_change_sha256": artifact.proposal_change_sha256,
            "status": artifact.status,
            "reviewer": artifact.reviewer,
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "artifact_sha256": artifact.artifact_sha256,
            "notes": artifact.notes,
            "thread_id": artifact.thread_id,
            "turn_id": artifact.turn_id,
        }

    def _artifact_payload(self, artifact: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in artifact.items() if key != "artifact_sha256"}
