"""Explicit proposal and promotion mechanics for canonical memory updates."""

from __future__ import annotations

from difflib import unified_diff
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .approval_records import ApprovalArtifact
from .execution import slug_id, utc_now, validate_identifier
from .integrity import sha256_payload, sha256_text
from .validation_records import ValidationArtifact


ALLOWED_PROPOSAL_STATUSES = {"draft", "approved", "rejected", "applied"}


@dataclass(frozen=True)
class ArtifactReference:
    """Immutable reference to an artifact by id and content hash."""

    artifact_id: str
    artifact_sha256: str


@dataclass(frozen=True)
class PromotionProposal:
    """Durable proposal for updating canonical memory."""

    proposal_id: str
    target_path: str
    candidate_artifact_path: str
    current_artifact_path: str
    diff_artifact_path: str
    candidate_sha256: str
    current_sha256: str
    diff_sha256: str
    change_sha256: str
    rationale: str
    status: str
    created_at: str
    updated_at: str
    target_exists: bool
    thread_id: str | None = None
    turn_id: str | None = None
    source_branch: str | None = None
    source_branch_memory_path: str | None = None
    reviewer: str | None = None
    review_notes: str | None = None
    applied_at: str | None = None
    approval_refs: tuple[ArtifactReference, ...] = ()
    validation_refs: tuple[ArtifactReference, ...] = ()


class ProposalManager:
    """Create, review, and apply canonical memory proposals."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def create_memory_proposal(
        self,
        *,
        target_path: str,
        content: str,
        rationale: str,
        thread_id: str | None = None,
        turn_id: str | None = None,
        source_branch: str | None = None,
        source_branch_memory_path: str | None = None,
        validation_ids: list[str] | None = None,
    ) -> PromotionProposal:
        target = self.repository.resolve_memory_path(target_path)
        if thread_id is not None:
            validate_identifier("thread_id", thread_id)
        if turn_id is not None:
            validate_identifier("turn_id", turn_id)
        if source_branch is not None:
            validate_identifier("source_branch", source_branch)
        proposal_id = slug_id("proposal")
        suffix = Path(target_path).suffix or ".md"
        candidate_artifact_path = f"promotions/{proposal_id}/candidate{suffix}"
        current_artifact_path = f"promotions/{proposal_id}/current{suffix}"
        diff_artifact_path = f"promotions/{proposal_id}/diff.patch"
        target_exists = target.exists()
        current_content = target.read_text() if target_exists else ""
        diff_text = self._render_diff(
            target_path=str(target.relative_to(self.repository.memory_dir)),
            current_content=current_content,
            candidate_content=content,
        )
        validation_refs = self._load_validation_refs(validation_ids or ())
        proposal = PromotionProposal(
            proposal_id=proposal_id,
            target_path=str(target.relative_to(self.repository.memory_dir)),
            candidate_artifact_path=candidate_artifact_path,
            current_artifact_path=current_artifact_path,
            diff_artifact_path=diff_artifact_path,
            candidate_sha256=sha256_text(content),
            current_sha256=sha256_text(current_content),
            diff_sha256=sha256_text(diff_text),
            change_sha256="",
            rationale=rationale,
            status="draft",
            created_at=utc_now(),
            updated_at=utc_now(),
            target_exists=target_exists,
            thread_id=thread_id,
            turn_id=turn_id,
            source_branch=source_branch,
            source_branch_memory_path=source_branch_memory_path,
            validation_refs=validation_refs,
        )
        proposal = replace(proposal, change_sha256=self._proposal_change_sha256(proposal))
        self.repository.write_artifact_text(current_artifact_path, current_content)
        self.repository.write_artifact_text(candidate_artifact_path, content)
        self.repository.write_artifact_text(diff_artifact_path, diff_text)
        self.repository.write_artifact_json(self._proposal_manifest_path(proposal_id), asdict(proposal))
        return proposal

    def create_memory_proposal_from_branch(
        self,
        *,
        branch: str,
        branch_memory_path: str,
        target_path: str,
        rationale: str,
        thread_id: str | None = None,
        turn_id: str | None = None,
        validation_ids: list[str] | None = None,
    ) -> PromotionProposal:
        branch_workspace = self.repository.branch_workspace(branch)
        content = branch_workspace.read_memory_text(branch_memory_path)
        return self.create_memory_proposal(
            target_path=target_path,
            content=content,
            rationale=rationale,
            thread_id=thread_id,
            turn_id=turn_id,
            source_branch=branch,
            source_branch_memory_path=branch_memory_path,
            validation_ids=validation_ids,
        )

    def approve(
        self,
        proposal_id: str,
        *,
        reviewer: str,
        notes: str = "",
        validation_ids: list[str] | None = None,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> PromotionProposal:
        proposal = self.load(proposal_id)
        if proposal.status != "draft":
            raise ValueError(f"proposal {proposal_id} must be in 'draft' status before approval")
        if not reviewer.strip():
            raise ValueError("reviewer is required for approval")
        validation_refs = self._merge_validation_refs(proposal, validation_ids or ())
        proposal_for_approval = replace(
            proposal,
            validation_refs=validation_refs,
            updated_at=utc_now(),
        )
        proposal_for_approval = replace(
            proposal_for_approval,
            change_sha256=self._proposal_change_sha256(proposal_for_approval),
        )
        approval = self.repository.approvals().create(
            proposal_id=proposal_id,
            proposal_change_sha256=proposal_for_approval.change_sha256,
            status="approved",
            reviewer=reviewer,
            notes=notes,
            thread_id=thread_id or proposal.thread_id,
            turn_id=turn_id or proposal.turn_id,
        )
        approved = replace(
            proposal_for_approval,
            status="approved",
            reviewer=approval.reviewer,
            review_notes=approval.notes,
            approval_refs=proposal.approval_refs + (
                ArtifactReference(artifact_id=approval.approval_id, artifact_sha256=approval.artifact_sha256),
            ),
        )
        self._persist(approved)
        return approved

    def reject(self, proposal_id: str, *, reviewer: str, notes: str) -> PromotionProposal:
        proposal = self.load(proposal_id)
        if proposal.status not in {"draft", "approved"}:
            raise ValueError(f"proposal {proposal_id} cannot be rejected from status {proposal.status!r}")
        rejected = replace(
            proposal,
            status="rejected",
            updated_at=utc_now(),
            reviewer=reviewer,
            review_notes=notes,
        )
        self._persist(rejected)
        return rejected

    def apply(self, proposal_id: str) -> PromotionProposal:
        proposal = self.load(proposal_id)
        if proposal.status != "approved":
            raise ValueError(f"proposal {proposal_id} must be approved before apply")
        if proposal.reviewer is None:
            raise ValueError(f"proposal {proposal_id} is missing reviewer attribution")
        if not proposal.approval_refs:
            raise ValueError(f"proposal {proposal_id} is missing approval artifacts")
        self._verify_proposal_integrity(proposal)
        self._enforce_policy(proposal)
        candidate_text = self.repository.read_artifact_text(proposal.candidate_artifact_path)
        self.repository._write_canonical_memory_text(proposal.target_path, candidate_text)
        applied = replace(
            proposal,
            status="applied",
            updated_at=utc_now(),
            applied_at=utc_now(),
        )
        self._persist(applied)
        return applied

    def load(self, proposal_id: str) -> PromotionProposal:
        data = self.repository.read_artifact_json(self._proposal_manifest_path(proposal_id))
        status = data.get("status")
        if status not in ALLOWED_PROPOSAL_STATUSES:
            raise ValueError(f"proposal {proposal_id} has invalid status {status!r}")
        data["approval_refs"] = tuple(ArtifactReference(**entry) for entry in data.get("approval_refs", ()))
        data["validation_refs"] = tuple(ArtifactReference(**entry) for entry in data.get("validation_refs", ()))
        proposal = PromotionProposal(**data)
        if proposal.change_sha256 != self._proposal_change_sha256(proposal):
            raise ValueError(f"proposal {proposal_id} failed integrity check")
        return proposal

    def _persist(self, proposal: PromotionProposal) -> None:
        self.repository.write_artifact_json(self._proposal_manifest_path(proposal.proposal_id), asdict(proposal))

    def _proposal_manifest_path(self, proposal_id: str) -> str:
        return f"promotions/{proposal_id}/proposal.json"

    def _enforce_policy(self, proposal: PromotionProposal) -> None:
        policy = self.repository.config.promotion_policy
        target = Path(proposal.target_path)
        if not any(self._path_is_within_root(target, Path(root)) for root in policy.promotable_memory_roots):
            raise ValueError(
                f"proposal {proposal.proposal_id} targets non-promotable memory path {proposal.target_path!r}"
            )
        validations = self._load_attested_validations(proposal)
        missing = [
            kind
            for kind in policy.required_validation_kinds
            if not self._has_passing_validation(validations, kind)
        ]
        if missing:
            raise ValueError(
                f"proposal {proposal.proposal_id} is missing required validation kinds: {', '.join(missing)}"
            )
        approvals = self._load_attested_approvals(proposal)
        if not self._has_approval_for_proposal(approvals, proposal):
            raise ValueError(f"proposal {proposal.proposal_id} has no matching approved approval artifact")

    def _path_is_within_root(self, path: Path, root: Path) -> bool:
        return path == root or root in path.parents

    def _has_passing_validation(self, validations: list[ValidationArtifact], required_kind: str) -> bool:
        return any(validation.kind == required_kind and validation.status == "passed" for validation in validations)

    def _has_approval_for_proposal(self, approvals: list[ApprovalArtifact], proposal: PromotionProposal) -> bool:
        return any(
            approval.proposal_id == proposal.proposal_id
            and approval.status == "approved"
            and approval.proposal_change_sha256 == proposal.change_sha256
            for approval in approvals
        )

    def _verify_proposal_integrity(self, proposal: PromotionProposal) -> None:
        candidate_text = self.repository.read_artifact_text(proposal.candidate_artifact_path)
        if sha256_text(candidate_text) != proposal.candidate_sha256:
            raise ValueError(f"proposal {proposal.proposal_id} candidate artifact has drifted")
        current_snapshot = self.repository.read_artifact_text(proposal.current_artifact_path)
        if sha256_text(current_snapshot) != proposal.current_sha256:
            raise ValueError(f"proposal {proposal.proposal_id} current snapshot artifact has drifted")
        diff_text = self.repository.read_artifact_text(proposal.diff_artifact_path)
        if sha256_text(diff_text) != proposal.diff_sha256:
            raise ValueError(f"proposal {proposal.proposal_id} diff artifact has drifted")
        current_canon = self.repository.read_memory_text(proposal.target_path) if self.repository.resolve_memory_path(proposal.target_path).exists() else ""
        if sha256_text(current_canon) != proposal.current_sha256:
            raise ValueError(f"proposal {proposal.proposal_id} is stale: canonical memory changed after proposal creation")

    def _load_validation_refs(self, validation_ids: list[str] | tuple[str, ...]) -> tuple[ArtifactReference, ...]:
        refs: list[ArtifactReference] = []
        for validation_id in validation_ids:
            artifact = self.repository.validations().load(validation_id)
            refs.append(ArtifactReference(artifact_id=artifact.validation_id, artifact_sha256=artifact.artifact_sha256))
        return tuple(refs)

    def _merge_validation_refs(
        self,
        proposal: PromotionProposal,
        additional_validation_ids: list[str] | tuple[str, ...],
    ) -> tuple[ArtifactReference, ...]:
        merged = {ref.artifact_id: ref for ref in proposal.validation_refs}
        for ref in self._load_validation_refs(additional_validation_ids):
            merged[ref.artifact_id] = ref
        return tuple(sorted(merged.values(), key=lambda ref: ref.artifact_id))

    def _load_attested_validations(self, proposal: PromotionProposal) -> list[ValidationArtifact]:
        validations: list[ValidationArtifact] = []
        for ref in proposal.validation_refs:
            artifact = self.repository.validations().load(ref.artifact_id)
            if artifact.artifact_sha256 != ref.artifact_sha256:
                raise ValueError(
                    f"proposal {proposal.proposal_id} validation artifact {ref.artifact_id} has drifted since attestation"
                )
            validations.append(artifact)
        return validations

    def _load_attested_approvals(self, proposal: PromotionProposal) -> list[ApprovalArtifact]:
        approvals: list[ApprovalArtifact] = []
        for ref in proposal.approval_refs:
            artifact = self.repository.approvals().load(ref.artifact_id)
            if artifact.artifact_sha256 != ref.artifact_sha256:
                raise ValueError(
                    f"proposal {proposal.proposal_id} approval artifact {ref.artifact_id} has drifted since attestation"
                )
            approvals.append(artifact)
        return approvals

    def _proposal_change_sha256(self, proposal: PromotionProposal) -> str:
        return sha256_payload(
            {
                "proposal_id": proposal.proposal_id,
                "target_path": proposal.target_path,
                "candidate_artifact_path": proposal.candidate_artifact_path,
                "current_artifact_path": proposal.current_artifact_path,
                "diff_artifact_path": proposal.diff_artifact_path,
                "candidate_sha256": proposal.candidate_sha256,
                "current_sha256": proposal.current_sha256,
                "diff_sha256": proposal.diff_sha256,
                "rationale": proposal.rationale,
                "target_exists": proposal.target_exists,
                "thread_id": proposal.thread_id,
                "turn_id": proposal.turn_id,
                "source_branch": proposal.source_branch,
                "source_branch_memory_path": proposal.source_branch_memory_path,
                "validation_refs": [
                    {"artifact_id": ref.artifact_id, "artifact_sha256": ref.artifact_sha256}
                    for ref in proposal.validation_refs
                ],
            }
        )

    def _render_diff(self, *, target_path: str, current_content: str, candidate_content: str) -> str:
        diff_lines = unified_diff(
            current_content.splitlines(keepends=True),
            candidate_content.splitlines(keepends=True),
            fromfile=f"memory/{target_path}",
            tofile=f"candidate/{target_path}",
        )
        rendered = "".join(diff_lines)
        if rendered:
            return rendered
        return "No changes.\n"
