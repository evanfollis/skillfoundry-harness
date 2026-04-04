"""Context repository accessors."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .approval_records import ApprovalArtifactStore
from .bundles import BundleStore
from .execution import RunRecorder, validate_identifier
from .promotion import ProposalManager
from .validation import RepositoryConfig, load_repository_config
from .validation_records import ValidationArtifactStore
from .worktrees import GitWorktreeManager


@dataclass(frozen=True)
class BranchWorkspace:
    """Bounded branch-local draft workspace rooted under artifacts/branches/."""

    repository: "ContextRepository"
    branch: str

    def __post_init__(self) -> None:
        validate_identifier("branch", self.branch)

    @property
    def root(self) -> Path:
        return self.repository.artifacts_dir / "branches" / self.branch

    @property
    def memory_dir(self) -> Path:
        return self.root / "memory"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    def resolve_memory_path(self, relative_path: str) -> Path:
        return self.repository._resolve_file_path(self.memory_dir, relative_path, scope_name=f"branch[{self.branch}].memory")

    def resolve_artifact_path(self, relative_path: str) -> Path:
        return self.repository._resolve_file_path(
            self.artifacts_dir,
            relative_path,
            scope_name=f"branch[{self.branch}].artifacts",
        )

    def write_memory_text(self, relative_path: str, content: str) -> Path:
        return self.repository._write_text(self.resolve_memory_path(relative_path), content)

    def write_artifact_text(self, relative_path: str, content: str) -> Path:
        return self.repository._write_text(self.resolve_artifact_path(relative_path), content)

    def read_memory_text(self, relative_path: str) -> str:
        return self.resolve_memory_path(relative_path).read_text()

    def snapshot(self) -> dict[str, object]:
        return {
            "branch": self.branch,
            "root": str(self.root.relative_to(self.repository.root)),
            "memory_dir": str(self.memory_dir.relative_to(self.repository.root)),
            "artifacts_dir": str(self.artifacts_dir.relative_to(self.repository.root)),
        }

    def create_memory_proposal(
        self,
        *,
        relative_path: str,
        rationale: str,
        target_path: str | None = None,
        thread_id: str | None = None,
        turn_id: str | None = None,
        validation_ids: list[str] | None = None,
    ):
        effective_target_path = target_path or relative_path
        return self.repository.proposals().create_memory_proposal_from_branch(
            branch=self.branch,
            branch_memory_path=relative_path,
            target_path=effective_target_path,
            rationale=rationale,
            thread_id=thread_id,
            turn_id=turn_id,
            validation_ids=validation_ids,
        )


@dataclass(frozen=True)
class ContextRepository:
    """Filesystem-backed agent context repository."""

    root: Path
    config: RepositoryConfig

    @classmethod
    def open(cls, path: str | Path) -> "ContextRepository":
        root = Path(path).resolve()
        config_path = root / "skillfoundry.toml"
        if not root.is_dir():
            raise FileNotFoundError(f"context repo path does not exist: {root}")
        if not config_path.exists():
            raise FileNotFoundError(f"missing context repo config: {config_path}")
        return cls(root=root, config=load_repository_config(config_path))

    @property
    def config_path(self) -> Path:
        return self.root / "skillfoundry.toml"

    @property
    def bundles_dir(self) -> Path:
        return self.root / self.config.layout.bundles_dir

    @property
    def memory_dir(self) -> Path:
        return self.root / self.config.layout.memory_dir

    @property
    def artifacts_dir(self) -> Path:
        return self.root / self.config.layout.artifacts_dir

    @property
    def runs_dir(self) -> Path:
        return self.root / self.config.layout.runs_dir

    @property
    def writable_roots(self) -> tuple[Path, Path, Path]:
        return (self.memory_dir, self.artifacts_dir, self.runs_dir)

    @property
    def pinned_frontdoor_paths(self) -> tuple[Path, ...]:
        return tuple(self.root / path for path in self.config.frontdoor.pinned_paths)

    @property
    def discoverable_frontdoor_paths(self) -> tuple[Path, ...]:
        return tuple(self.root / path for path in self.config.frontdoor.discoverable_paths)

    @property
    def threads_dir(self) -> Path:
        return self.runs_dir / "threads"

    def bundle_paths(self) -> list[Path]:
        if not self.bundles_dir.exists():
            return []
        return sorted(self.bundles_dir.rglob("*.json"))

    def bundles(self) -> BundleStore:
        return BundleStore(self)

    def frontdoor_snapshot(self, max_chars: int = 400) -> dict[str, Any]:
        pinned = []
        for path in self.pinned_frontdoor_paths:
            contents = path.read_text()
            preview = contents[:max_chars]
            if len(contents) > max_chars:
                preview = f"{preview}..."
            pinned.append(
                {
                    "path": str(path.relative_to(self.root)),
                    "preview": preview,
                }
            )
        discoverable = [str(path.relative_to(self.root)) for path in self.discoverable_frontdoor_paths]
        return {
            "repository": asdict(self.config),
            "pinned": pinned,
            "discoverable": discoverable,
        }

    def create_run(
        self,
        *,
        thread_id: str,
        task: str,
        branch: str | None = None,
        turn_id: str | None = None,
        worktree_name: str | None = None,
    ) -> RunRecorder:
        return RunRecorder.create(
            repository=self,
            thread_id=thread_id,
            task=task,
            branch=branch,
            turn_id=turn_id,
            worktree_name=worktree_name,
        )

    def resolve_memory_path(self, relative_path: str) -> Path:
        return self._resolve_file_path(self.memory_dir, relative_path, scope_name="memory")

    def resolve_artifact_path(self, relative_path: str) -> Path:
        return self._resolve_file_path(self.artifacts_dir, relative_path, scope_name="artifacts")

    def resolve_run_path(self, relative_path: str) -> Path:
        return self._resolve_file_path(self.runs_dir, relative_path, scope_name="runs")

    def write_artifact_text(self, relative_path: str, content: str) -> Path:
        return self._write_text(self.resolve_artifact_path(relative_path), content)

    def write_artifact_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        return self.write_artifact_text(relative_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def write_run_text(self, relative_path: str, content: str) -> Path:
        return self._write_text(self.resolve_run_path(relative_path), content)

    def write_run_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        return self.write_run_text(relative_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def append_run_jsonl(self, relative_path: str, payload: dict[str, Any]) -> Path:
        path = self.resolve_run_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        return path

    def read_run_json(self, relative_path: str) -> dict[str, Any]:
        path = self.resolve_run_path(relative_path)
        return json.loads(path.read_text())

    def read_artifact_text(self, relative_path: str) -> str:
        path = self.resolve_artifact_path(relative_path)
        return path.read_text()

    def read_artifact_json(self, relative_path: str) -> dict[str, Any]:
        return json.loads(self.read_artifact_text(relative_path))

    def read_memory_text(self, relative_path: str) -> str:
        path = self.resolve_memory_path(relative_path)
        return path.read_text()

    def proposals(self) -> ProposalManager:
        return ProposalManager(self)

    def validations(self) -> ValidationArtifactStore:
        return ValidationArtifactStore(self)

    def approvals(self) -> ApprovalArtifactStore:
        return ApprovalArtifactStore(self)

    def branch_workspace(self, branch: str) -> BranchWorkspace:
        return BranchWorkspace(self, branch)

    def worktrees(self) -> GitWorktreeManager:
        return GitWorktreeManager(self)

    def _write_canonical_memory_text(self, relative_path: str, content: str) -> Path:
        return self._write_text(self.resolve_memory_path(relative_path), content)

    def _resolve_file_path(self, scope_root: Path, relative_path: str, *, scope_name: str) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute():
            raise ValueError(f"{scope_name} path must be relative: {relative_path}")
        if ".." in relative.parts:
            raise ValueError(f"{scope_name} path must stay inside the repository: {relative_path}")
        normalized = Path(relative.as_posix().strip("/"))
        if normalized in {Path(""), Path(".")}:
            raise ValueError(f"{scope_name} path must name a file: {relative_path}")
        if normalized.name in {"", ".", ".."}:
            raise ValueError(f"{scope_name} path must name a file: {relative_path}")
        return scope_root / normalized

    def _write_text(self, path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        temp_path.replace(path)
        return path
