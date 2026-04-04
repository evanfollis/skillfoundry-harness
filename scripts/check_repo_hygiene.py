#!/usr/bin/env python3
"""Reject files that suggest workspace-state drift into the harness repo."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOT_ENTRIES = {"agents", "bundles", "memory", "artifacts", "runs", "context"}
FORBIDDEN_FILE_PATTERNS = (
    "*.prompt",
    "*.prompty",
    "*.jsonl",
)


class HygieneError(Exception):
    """Raised when the repo layout violates policy."""


def iter_tracked_files() -> list[Path]:
    return [path for path in REPO_ROOT.rglob("*") if ".git" not in path.parts]


def validate_forbidden_names() -> None:
    violations: list[str] = []
    for name in FORBIDDEN_ROOT_ENTRIES:
        path = REPO_ROOT / name
        if path.exists():
            violations.append(str(path.relative_to(REPO_ROOT)))

    config_path = REPO_ROOT / "skillfoundry.toml"
    if config_path.exists():
        violations.append(str(config_path.relative_to(REPO_ROOT)))

    for path in iter_tracked_files():
        if path.is_file():
            for pattern in FORBIDDEN_FILE_PATTERNS:
                if path.match(pattern):
                    violations.append(str(path.relative_to(REPO_ROOT)))
    if violations:
        raise HygieneError(f"forbidden runtime artifacts detected: {', '.join(sorted(violations))}")


def main() -> int:
    try:
        validate_forbidden_names()
    except HygieneError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print("OK repository hygiene checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
