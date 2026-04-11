"""Bootstrap and fork git-backed context lineages."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .repository import ContextRepository
from .validation import validate_context_repo


DEFAULT_PINNED_PATHS = ("README.md", "memory/mission.md")
DEFAULT_DISCOVERABLE_PATHS = ("bundles", "memory", "artifacts")
DEFAULT_PROMOTABLE_MEMORY_ROOTS = ("notes", "plans")
DEFAULT_REQUIRED_VALIDATION_KINDS = ("canon-safe", "frontdoor-reviewed")
COMMITTER_NAME = "Skillfoundry"
COMMITTER_EMAIL = "skillfoundry@local"


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _commit_all(repo_root: Path, message: str) -> None:
    _run_git(["add", "."], cwd=repo_root)
    result = subprocess.run(
        [
            "git",
            "-c",
            f"user.name={COMMITTER_NAME}",
            "-c",
            f"user.email={COMMITTER_EMAIL}",
            "commit",
            "--quiet",
            "-m",
            message,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )


def _ensure_empty_or_missing(path: Path) -> None:
    if not path.exists():
        return
    if not path.is_dir():
        raise ValueError(f"target path must be a directory or missing: {path}")
    if any(path.iterdir()):
        raise ValueError(f"target path must be empty before initialization: {path}")


def _render_repository_config(
    *,
    agent_id: str,
    name: str,
    bundles_dir: str = "bundles",
    memory_dir: str = "memory",
    artifacts_dir: str = "artifacts",
    runs_dir: str = "runs",
    pinned_paths: tuple[str, ...] = DEFAULT_PINNED_PATHS,
    discoverable_paths: tuple[str, ...] = DEFAULT_DISCOVERABLE_PATHS,
    promotable_memory_roots: tuple[str, ...] = DEFAULT_PROMOTABLE_MEMORY_ROOTS,
    required_validation_kinds: tuple[str, ...] = DEFAULT_REQUIRED_VALIDATION_KINDS,
) -> str:
    return "\n".join(
        [
            "[repository]",
            'schema_version = "1"',
            f'name = "{name}"',
            f'agent_id = "{agent_id}"',
            "",
            "[frontdoor]",
            f"pinned_paths = [{', '.join(repr(path) for path in pinned_paths)}]",
            f"discoverable_paths = [{', '.join(repr(path) for path in discoverable_paths)}]",
            "",
            "[promotion_policy]",
            f"promotable_memory_roots = [{', '.join(repr(path) for path in promotable_memory_roots)}]",
            f"required_validation_kinds = [{', '.join(repr(kind) for kind in required_validation_kinds)}]",
            "",
        ]
    )


def _patch_toml_identity(toml_path: Path, *, agent_id: str, name: str) -> None:
    """Rewrite only agent_id and name in an existing skillfoundry.toml, preserving all other content."""
    import re

    text = toml_path.read_text()
    text = re.sub(r'^(agent_id\s*=\s*)"[^"]*"', f'\\1"{agent_id}"', text, flags=re.MULTILINE)
    text = re.sub(r'^(name\s*=\s*)"[^"]*"', f'\\1"{name}"', text, flags=re.MULTILINE)
    toml_path.write_text(text)


def _write_bootstrap_files(root: Path, *, agent_id: str, name: str, mission: str) -> None:
    for directory in ("bundles", "memory", "artifacts", "runs"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    for directory in ("bundles", "artifacts", "runs"):
        (root / directory / ".gitkeep").write_text("")
    (root / "README.md").write_text(
        "\n".join(
            [
                f"# {name}",
                "",
                "This repository is the canonical context lineage for one Skillfoundry agent.",
                "The harness runs inside this repository root. Fresh runtime instances may come",
                "and go, but this context lineage remains the durable working mind.",
                "",
                "## Front Door",
                "",
                "- `memory/mission.md`",
                "",
            ]
        )
        + "\n"
    )
    (root / "memory" / "mission.md").write_text(f"# Mission\n\n{mission.strip()}\n")
    (root / "skillfoundry.toml").write_text(
        _render_repository_config(agent_id=agent_id, name=name),
    )


def init_context_lineage(
    path: str | Path,
    *,
    agent_id: str,
    name: str,
    mission: str | None = None,
) -> ContextRepository:
    root = Path(path).resolve()
    _ensure_empty_or_missing(root)
    root.mkdir(parents=True, exist_ok=True)
    _write_bootstrap_files(
        root,
        agent_id=agent_id,
        name=name,
        mission=mission or "Define the current mission for this agent context lineage.",
    )
    _run_git(["init", "--initial-branch", "main"], cwd=root)
    _commit_all(root, f"Initialize context lineage for {agent_id}")
    validate_context_repo(root)
    return ContextRepository.open(root)


def fork_context_lineage(
    source_path: str | Path,
    target_path: str | Path,
    *,
    agent_id: str | None = None,
    name: str | None = None,
) -> ContextRepository:
    source_root = Path(source_path).resolve()
    source_repo = ContextRepository.open(source_root)
    validate_context_repo(source_root)

    target_root = Path(target_path).resolve()
    if target_root.exists():
        raise ValueError(f"target path already exists: {target_root}")
    target_root.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["clone", "--quiet", "--no-hardlinks", str(source_root), str(target_root)], cwd=target_root.parent)
    subprocess.run(["git", "-C", str(target_root), "remote", "remove", "origin"], check=False, capture_output=True, text=True)

    effective_agent_id = agent_id or source_repo.config.agent_id
    effective_name = name or source_repo.config.name
    if effective_agent_id != source_repo.config.agent_id or effective_name != source_repo.config.name:
        _patch_toml_identity(
            target_root / "skillfoundry.toml",
            agent_id=effective_agent_id,
            name=effective_name,
        )
        _commit_all(target_root, f"Fork context lineage for {effective_agent_id}")

    validate_context_repo(target_root)
    return ContextRepository.open(target_root)
