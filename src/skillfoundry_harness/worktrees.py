"""Managed git worktree orchestration for isolated subagent execution."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from .execution import utc_now, validate_identifier


@dataclass(frozen=True)
class ManagedWorktree:
    worktree_name: str
    branch: str
    path: str
    base_ref: str
    head_sha: str
    created_at: str
    updated_at: str
    status: str
    latest_thread_id: str | None = None
    latest_turn_id: str | None = None
    latest_run_id: str | None = None
    latest_run_started_at: str | None = None


class GitWorktreeManager:
    """Create, list, and retire managed git worktrees for a context repo."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    @property
    def managed_root(self) -> Path:
        return self.repository.root.parent / ".skillfoundry-worktrees" / self.repository.root.name

    def create(self, worktree_name: str, *, base_ref: str = "HEAD", branch: str | None = None) -> ManagedWorktree:
        self._ensure_git_repository()
        validate_identifier("worktree_name", worktree_name)
        effective_branch = branch or worktree_name
        validate_identifier("branch", effective_branch)
        path = self.managed_root / worktree_name
        if path.exists():
            raise ValueError(f"managed worktree path already exists: {path}")
        self.managed_root.mkdir(parents=True, exist_ok=True)
        self._git("worktree", "add", "-b", effective_branch, str(path), base_ref)
        head_sha = self._git("rev-parse", "HEAD", cwd=path)
        record = ManagedWorktree(
            worktree_name=worktree_name,
            branch=effective_branch,
            path=str(path),
            base_ref=base_ref,
            head_sha=head_sha,
            created_at=utc_now(),
            updated_at=utc_now(),
            status="active",
        )
        self._persist(record)
        return record

    def list(self) -> list[ManagedWorktree]:
        self._ensure_git_repository()
        records: list[ManagedWorktree] = []
        for metadata_path in sorted((self.repository.artifacts_dir / "worktrees").glob("*.json")):
            payload = json.loads(metadata_path.read_text())
            record = ManagedWorktree(**payload)
            if record.status == "active":
                actual = self._find_worktree_by_path(Path(record.path))
                if actual is None:
                    record = ManagedWorktree(**{**payload, "status": "missing"})
                else:
                    record = ManagedWorktree(**{**payload, "head_sha": actual["HEAD"], "updated_at": utc_now()})
            records.append(record)
        return records

    def load(self, worktree_name: str) -> ManagedWorktree:
        metadata_path = self._metadata_path(worktree_name)
        if not metadata_path.exists():
            raise FileNotFoundError(f"managed worktree metadata not found: {worktree_name}")
        return ManagedWorktree(**json.loads(metadata_path.read_text()))

    def remove(self, worktree_name: str, *, force: bool = False) -> ManagedWorktree:
        self._ensure_git_repository()
        record = self.load(worktree_name)
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(record.path)
        self._git(*args)
        removed = ManagedWorktree(
            worktree_name=record.worktree_name,
            branch=record.branch,
            path=record.path,
            base_ref=record.base_ref,
            head_sha=record.head_sha,
            created_at=record.created_at,
            updated_at=utc_now(),
            status="removed",
            latest_thread_id=record.latest_thread_id,
            latest_turn_id=record.latest_turn_id,
            latest_run_id=record.latest_run_id,
            latest_run_started_at=record.latest_run_started_at,
        )
        self._persist(removed)
        self._git("worktree", "prune")
        return removed

    def bind_execution(
        self,
        worktree_name: str,
        *,
        thread_id: str,
        turn_id: str,
        run_id: str,
        started_at: str,
    ) -> ManagedWorktree:
        self._ensure_git_repository()
        validate_identifier("thread_id", thread_id)
        validate_identifier("turn_id", turn_id)
        validate_identifier("run_id", run_id)
        record = self.load(worktree_name)
        if record.status != "active":
            raise ValueError(f"managed worktree {worktree_name} is not active")
        actual = self._find_worktree_by_path(Path(record.path))
        if actual is None:
            raise ValueError(f"managed worktree {worktree_name} is missing from git worktree list")
        bound = ManagedWorktree(
            worktree_name=record.worktree_name,
            branch=record.branch,
            path=record.path,
            base_ref=record.base_ref,
            head_sha=actual["HEAD"],
            created_at=record.created_at,
            updated_at=utc_now(),
            status="active",
            latest_thread_id=thread_id,
            latest_turn_id=turn_id,
            latest_run_id=run_id,
            latest_run_started_at=started_at,
        )
        self._persist(bound)
        return bound

    def _persist(self, record: ManagedWorktree) -> None:
        self.repository.write_artifact_json(
            f"worktrees/{record.worktree_name}.json",
            {
                "worktree_name": record.worktree_name,
                "branch": record.branch,
                "path": record.path,
                "base_ref": record.base_ref,
                "head_sha": record.head_sha,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "status": record.status,
                "latest_thread_id": record.latest_thread_id,
                "latest_turn_id": record.latest_turn_id,
                "latest_run_id": record.latest_run_id,
                "latest_run_started_at": record.latest_run_started_at,
            },
        )

    def _metadata_path(self, worktree_name: str) -> Path:
        return self.repository.resolve_artifact_path(f"worktrees/{worktree_name}.json")

    def _ensure_git_repository(self) -> None:
        result = subprocess.run(
            ["git", "-C", str(self.repository.root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or result.stdout.strip() != "true":
            raise ValueError(f"context repo is not a git worktree: {self.repository.root}")

    def _find_worktree_by_path(self, target_path: Path) -> dict[str, str] | None:
        current: dict[str, str] = {}
        results: list[dict[str, str]] = []
        output = self._git("worktree", "list", "--porcelain")
        for line in output.splitlines():
            if not line.strip():
                if current:
                    results.append(current)
                    current = {}
                continue
            key, value = line.split(" ", 1) if " " in line else (line, "")
            current[key] = value
        if current:
            results.append(current)
        target = str(target_path.resolve())
        for record in results:
            if Path(record["worktree"]).resolve().as_posix() == target:
                return {"HEAD": record.get("HEAD", ""), "branch": record.get("branch", "")}
        return None

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(
            ["git", "-C", str(cwd or self.repository.root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or result.stdout.strip() or "git command failed")
        return result.stdout.strip()
