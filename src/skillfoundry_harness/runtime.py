"""Runtime entrypoints."""

from __future__ import annotations

from pathlib import Path

from .bundles import ContextBundle
from .execution import RunRecorder
from .promotion import PromotionProposal
from .repository import BranchWorkspace, ContextRepository
from .validation import ValidationResult, validate_context_repo
from .validation_records import ValidationArtifact
from .worktrees import ManagedWorktree


class Runtime:
    """Open and operate on a single agent context repository."""

    def __init__(self, repository: ContextRepository) -> None:
        self.repository = repository

    @classmethod
    def open(cls, path: str | Path) -> "Runtime":
        repository = ContextRepository.open(path)
        return cls(repository)

    def describe(self) -> dict[str, str]:
        return {
            "repository.name": self.repository.config.name,
            "repository.agent_id": self.repository.config.agent_id,
            "repository.schema_version": self.repository.config.schema_version,
            "layout.bundles_dir": str(self.repository.bundles_dir),
            "layout.memory_dir": str(self.repository.memory_dir),
            "layout.artifacts_dir": str(self.repository.artifacts_dir),
            "layout.runs_dir": str(self.repository.runs_dir),
            "worktrees.managed_root": str(self.repository.worktrees().managed_root),
            "promotion_policy.promotable_memory_roots": ",".join(self.repository.config.promotion_policy.promotable_memory_roots),
            "promotion_policy.required_validation_kinds": ",".join(self.repository.config.promotion_policy.required_validation_kinds),
        }

    def frontdoor_snapshot(self, max_chars: int = 400) -> dict[str, object]:
        return self.repository.frontdoor_snapshot(max_chars=max_chars)

    def branch_workspace(self, branch: str) -> BranchWorkspace:
        return self.repository.branch_workspace(branch)

    def list_bundles(self) -> list[ContextBundle]:
        return self.repository.bundles().list()

    def load_bundle(self, bundle_id: str) -> ContextBundle:
        return self.repository.bundles().load(bundle_id)

    def create_worktree(
        self,
        worktree_name: str,
        *,
        base_ref: str = "HEAD",
        branch: str | None = None,
    ) -> ManagedWorktree:
        return self.repository.worktrees().create(worktree_name, base_ref=base_ref, branch=branch)

    def list_worktrees(self) -> list[ManagedWorktree]:
        return self.repository.worktrees().list()

    def remove_worktree(self, worktree_name: str, *, force: bool = False) -> ManagedWorktree:
        return self.repository.worktrees().remove(worktree_name, force=force)

    def start_run(
        self,
        *,
        thread_id: str,
        task: str,
        branch: str | None = None,
        turn_id: str | None = None,
        worktree_name: str | None = None,
    ) -> RunRecorder:
        return self.repository.create_run(
            thread_id=thread_id,
            task=task,
            branch=branch,
            turn_id=turn_id,
            worktree_name=worktree_name,
        )

    def create_memory_proposal(
        self,
        *,
        target_path: str,
        content: str,
        rationale: str,
        thread_id: str | None = None,
        turn_id: str | None = None,
        validation_ids: list[str] | None = None,
    ) -> PromotionProposal:
        return self.repository.proposals().create_memory_proposal(
            target_path=target_path,
            content=content,
            rationale=rationale,
            thread_id=thread_id,
            turn_id=turn_id,
            validation_ids=validation_ids,
        )

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
        return self.repository.proposals().create_memory_proposal_from_branch(
            branch=branch,
            branch_memory_path=branch_memory_path,
            target_path=target_path,
            rationale=rationale,
            thread_id=thread_id,
            turn_id=turn_id,
            validation_ids=validation_ids,
        )

    def create_validation_artifact(
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
        return self.repository.validations().create(
            kind=kind,
            status=status,
            evidence_paths=evidence_paths,
            summary=summary,
            thread_id=thread_id,
            turn_id=turn_id,
            reviewer=reviewer,
        )

    def load_proposal(self, proposal_id: str) -> PromotionProposal:
        return self.repository.proposals().load(proposal_id)

    def approve_proposal(
        self,
        proposal_id: str,
        *,
        reviewer: str,
        notes: str = "",
        validation_ids: list[str] | None = None,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> PromotionProposal:
        return self.repository.proposals().approve(
            proposal_id,
            reviewer=reviewer,
            notes=notes,
            validation_ids=validation_ids,
            thread_id=thread_id,
            turn_id=turn_id,
        )

    def apply_proposal(self, proposal_id: str) -> PromotionProposal:
        return self.repository.proposals().apply(proposal_id)

    def validate(self) -> list[ValidationResult]:
        return validate_context_repo(self.repository.root)
