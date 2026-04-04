"""Explicit run lifecycle primitives and durable run artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


ALLOWED_RUN_STATUSES = {"running", "awaiting_approval", "completed", "failed"}
ALLOWED_ITEM_STATUSES = {"started", "completed", "failed", "pending_approval"}
ALLOWED_THREAD_STATUSES = {"active", "completed", "failed"}
ALLOWED_TURN_STATUSES = {"running", "awaiting_approval", "completed", "failed"}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def validate_identifier(name: str, value: str) -> None:
    if not value or any(char.isspace() for char in value) or "/" in value or "\\" in value:
        raise ValueError(f"{name} must be a non-empty slash-free identifier")


@dataclass(frozen=True)
class ThreadRecord:
    """Durable thread metadata."""

    thread_id: str
    agent_id: str
    status: str
    created_at: str
    updated_at: str
    latest_turn_id: str
    turn_count: int


@dataclass(frozen=True)
class TurnRecord:
    """Durable turn metadata."""

    turn_id: str
    thread_id: str
    task: str
    branch: str
    status: str
    started_at: str
    updated_at: str
    completed_at: str | None = None
    latest_run_id: str | None = None
    item_count: int = 0
    worktree_name: str | None = None
    worktree_path: str | None = None
    worktree_head_sha: str | None = None


@dataclass(frozen=True)
class RunItem:
    """One observable event within a run."""

    item_id: str
    kind: str
    status: str
    created_at: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class RunRecord:
    """Durable run metadata."""

    run_id: str
    thread_id: str
    turn_id: str
    task: str
    branch: str
    agent_id: str
    status: str
    started_at: str
    completed_at: str | None = None
    item_count: int = 0
    worktree_name: str | None = None
    worktree_path: str | None = None
    worktree_head_sha: str | None = None


class RunRecorder:
    """Append-only writer for run artifacts."""

    def __init__(
        self,
        *,
        repository: Any,
        run_dir: Path,
        latest_path: Path,
        record: RunRecord,
        thread_record: ThreadRecord,
        turn_record: TurnRecord,
    ) -> None:
        self.repository = repository
        self.run_dir = run_dir
        self.latest_path = latest_path
        self.record = record
        self.thread_record = thread_record
        self.turn_record = turn_record
        self.items_path = self.run_dir / "items.jsonl"
        self.record_path = self.run_dir / "run.json"
        self.thread_path = self.repository.resolve_run_path(f"threads/{self.record.thread_id}/thread.json")
        self.thread_latest_turn_path = self.repository.resolve_run_path(f"threads/{self.record.thread_id}/LATEST_TURN")
        self.turn_path = self.repository.resolve_run_path(f"threads/{self.record.thread_id}/turns/{self.record.turn_id}.json")

    @classmethod
    def create(
        cls,
        *,
        repository: Any,
        thread_id: str,
        task: str,
        branch: str | None = None,
        turn_id: str | None = None,
        worktree_name: str | None = None,
    ) -> "RunRecorder":
        validate_identifier("thread_id", thread_id)
        run_id = slug_id("run")
        effective_turn_id = turn_id or slug_id("turn")
        validate_identifier("turn_id", effective_turn_id)
        date_segment = datetime.now(UTC).strftime("%Y-%m-%d")
        run_dir = repository.runs_dir / date_segment / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        latest_path = repository.runs_dir / "LATEST_RUN"
        started_at = utc_now()
        bound_worktree = None
        effective_branch = branch or "main"
        if worktree_name is not None:
            bound_worktree = repository.worktrees().bind_execution(
                worktree_name,
                thread_id=thread_id,
                turn_id=effective_turn_id,
                run_id=run_id,
                started_at=started_at,
            )
            effective_branch = branch or bound_worktree.branch
        record = RunRecord(
            run_id=run_id,
            thread_id=thread_id,
            turn_id=effective_turn_id,
            task=task,
            branch=effective_branch,
            agent_id=repository.config.agent_id,
            status="running",
            started_at=started_at,
            worktree_name=bound_worktree.worktree_name if bound_worktree else None,
            worktree_path=bound_worktree.path if bound_worktree else None,
            worktree_head_sha=bound_worktree.head_sha if bound_worktree else None,
        )
        thread_path = repository.resolve_run_path(f"threads/{thread_id}/thread.json")
        if thread_path.exists():
            thread_record = ThreadRecord(**repository.read_run_json(f"threads/{thread_id}/thread.json"))
            if thread_record.status not in ALLOWED_THREAD_STATUSES:
                raise ValueError(f"thread {thread_id} has invalid status {thread_record.status!r}")
            thread_record = replace(
                thread_record,
                status="active",
                updated_at=started_at,
                latest_turn_id=effective_turn_id,
                turn_count=thread_record.turn_count + 1,
            )
        else:
            thread_record = ThreadRecord(
                thread_id=thread_id,
                agent_id=repository.config.agent_id,
                status="active",
                created_at=started_at,
                updated_at=started_at,
                latest_turn_id=effective_turn_id,
                turn_count=1,
            )
        turn_record = TurnRecord(
            turn_id=effective_turn_id,
            thread_id=thread_id,
            task=task,
            branch=effective_branch,
            status="running",
            started_at=started_at,
            updated_at=started_at,
            latest_run_id=run_id,
            worktree_name=bound_worktree.worktree_name if bound_worktree else None,
            worktree_path=bound_worktree.path if bound_worktree else None,
            worktree_head_sha=bound_worktree.head_sha if bound_worktree else None,
        )
        recorder = cls(
            repository=repository,
            run_dir=run_dir,
            latest_path=latest_path,
            record=record,
            thread_record=thread_record,
            turn_record=turn_record,
        )
        repository.write_run_text(f"{date_segment}/{run_id}/items.jsonl", "")
        recorder._persist_record()
        recorder._persist_thread_record()
        recorder._persist_turn_record()
        recorder._persist_latest_pointer()
        return recorder

    def append_item(self, *, kind: str, payload: dict[str, Any], status: str = "completed") -> RunItem:
        if status not in ALLOWED_ITEM_STATUSES:
            raise ValueError(f"unsupported item status: {status}")
        item = RunItem(
            item_id=slug_id("item"),
            kind=kind,
            status=status,
            created_at=utc_now(),
            payload=payload,
        )
        self.repository.append_run_jsonl(f"{self._run_relative_dir()}/items.jsonl", asdict(item))
        next_status = self.record.status
        if status == "pending_approval":
            next_status = "awaiting_approval"
        elif self.record.status == "awaiting_approval" and status == "completed":
            next_status = "running"
        timestamp = utc_now()
        self.record = replace(self.record, status=next_status, item_count=self.record.item_count + 1)
        turn_status = "awaiting_approval" if status == "pending_approval" else next_status
        self.turn_record = replace(
            self.turn_record,
            status=turn_status,
            updated_at=timestamp,
            latest_run_id=self.record.run_id,
            item_count=self.turn_record.item_count + 1,
        )
        self.thread_record = replace(
            self.thread_record,
            status="active",
            updated_at=timestamp,
            latest_turn_id=self.turn_record.turn_id,
        )
        self._persist_record()
        self._persist_thread_record()
        self._persist_turn_record()
        self._persist_latest_pointer()
        return item

    def write_compaction(self, summary: str) -> Path:
        path = self.repository.write_run_text(f"{self._run_relative_dir()}/compaction.md", summary)
        self.append_item(
            kind="compaction",
            status="completed",
            payload={"path": path.relative_to(self.repository.runs_dir).as_posix()},
        )
        return path

    def complete(self, *, status: str = "completed") -> RunRecord:
        if status not in {"completed", "failed"}:
            raise ValueError(f"unsupported terminal status: {status}")
        timestamp = utc_now()
        self.record = replace(self.record, status=status, completed_at=timestamp)
        thread_status = "completed" if status == "completed" else "failed"
        self.turn_record = replace(
            self.turn_record,
            status=status,
            updated_at=timestamp,
            completed_at=timestamp,
            latest_run_id=self.record.run_id,
        )
        self.thread_record = replace(
            self.thread_record,
            status=thread_status,
            updated_at=timestamp,
            latest_turn_id=self.turn_record.turn_id,
        )
        self._persist_record()
        self._persist_thread_record()
        self._persist_turn_record()
        self._persist_latest_pointer()
        return self.record

    def snapshot(self) -> dict[str, Any]:
        return {
            "record": asdict(self.record),
            "thread": asdict(self.thread_record),
            "turn": asdict(self.turn_record),
            "run_dir": str(self.run_dir),
            "items_path": str(self.items_path),
        }

    def _persist_record(self) -> None:
        self.repository.write_run_json(f"{self._run_relative_dir()}/run.json", asdict(self.record))

    def _persist_thread_record(self) -> None:
        self.repository.write_run_json(f"threads/{self.record.thread_id}/thread.json", asdict(self.thread_record))
        self.repository.write_run_text(f"threads/{self.record.thread_id}/LATEST_TURN", f"{self.record.turn_id}\n")

    def _persist_turn_record(self) -> None:
        self.repository.write_run_json(f"threads/{self.record.thread_id}/turns/{self.record.turn_id}.json", asdict(self.turn_record))

    def _persist_latest_pointer(self) -> None:
        self.repository.write_run_text("LATEST_RUN", f"{self.record.run_id}\n")

    def _run_relative_dir(self) -> str:
        return self.run_dir.relative_to(self.repository.runs_dir).as_posix()
