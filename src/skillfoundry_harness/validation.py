"""Validation for context bundles and context repositories."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable


DEFAULT_LAYOUT = {
    "bundles_dir": "bundles",
    "memory_dir": "memory",
    "artifacts_dir": "artifacts",
    "runs_dir": "runs",
}
FRONTDOOR_KEYS = {"pinned_paths", "discoverable_paths"}
PROMOTION_POLICY_KEYS = {"promotable_memory_roots", "required_validation_kinds"}


BUNDLE_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
ALLOWED_SOURCE_KINDS = {"doc", "code", "issue", "conversation", "dataset", "other"}
ALLOWED_CONTENT_TYPES = {"instruction", "constraint", "fact", "example", "summary"}
ALLOWED_PROMOTION_STATUSES = {"draft", "candidate", "promoted"}
ALLOWED_COMPATIBILITY = {"additive", "compatible", "breaking"}


class ValidationError(Exception):
    """Raised when validation fails."""


@dataclass(frozen=True)
class ValidationResult:
    """Machine-readable validation result."""

    path: Path
    message: str


@dataclass(frozen=True)
class RepositoryLayout:
    """Declared repository layout relative to the context repo root."""

    bundles_dir: str
    memory_dir: str
    artifacts_dir: str
    runs_dir: str

    def values(self) -> tuple[str, str, str, str]:
        return (self.bundles_dir, self.memory_dir, self.artifacts_dir, self.runs_dir)


@dataclass(frozen=True)
class FrontDoorConfig:
    """Pinned starting context and discoverable roots for progressive disclosure."""

    pinned_paths: tuple[str, ...]
    discoverable_paths: tuple[str, ...]


@dataclass(frozen=True)
class PromotionPolicy:
    """Repository-owned post-reasoning promotion policy."""

    promotable_memory_roots: tuple[str, ...]
    required_validation_kinds: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryConfig:
    """Validated repository config."""

    schema_version: str
    name: str
    agent_id: str
    layout: RepositoryLayout
    frontdoor: FrontDoorConfig
    promotion_policy: PromotionPolicy


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def load_schema() -> Any:
    return json.loads(files("skillfoundry_harness").joinpath("schemas/context-bundle.schema.json").read_text())


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_datetime(value: str, field_name: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field_name}: expected ISO-8601 datetime, got {value!r}") from exc


def validate_relative_directory(value: Any, field_name: str) -> str:
    ensure(isinstance(value, str) and value.strip(), f"{field_name}: expected non-empty string")
    path = Path(value)
    ensure(not path.is_absolute(), f"{field_name}: must be relative to the context repo root")
    ensure(".." not in path.parts, f"{field_name}: must not escape the context repo root")
    normalized = path.as_posix().strip("/")
    ensure(normalized not in {"", "."}, f"{field_name}: must resolve to a directory path")
    return normalized


def validate_distinct_directories(values: Iterable[str], field_name: str) -> None:
    normalized = list(values)
    ensure(len(set(normalized)) == len(normalized), f"{field_name}: directories must be distinct")


def validate_relative_path(value: Any, field_name: str) -> str:
    ensure(isinstance(value, str) and value.strip(), f"{field_name}: expected non-empty string")
    path = Path(value)
    ensure(not path.is_absolute(), f"{field_name}: must be relative to the context repo root")
    ensure(".." not in path.parts, f"{field_name}: must not escape the context repo root")
    normalized = path.as_posix().strip("/")
    ensure(normalized not in {"", "."}, f"{field_name}: must resolve to a file or directory path")
    return normalized


def validate_relative_path_list(value: Any, field_name: str) -> tuple[str, ...]:
    ensure(isinstance(value, list) and value, f"{field_name}: expected non-empty array")
    normalized = tuple(validate_relative_path(item, f"{field_name}[{index}]") for index, item in enumerate(value))
    ensure(len(set(normalized)) == len(normalized), f"{field_name}: paths must be distinct")
    return normalized


def validate_token_list(value: Any, field_name: str) -> tuple[str, ...]:
    ensure(isinstance(value, list) and value, f"{field_name}: expected non-empty array")
    tokens: list[str] = []
    for index, item in enumerate(value):
        ensure(isinstance(item, str) and item.strip(), f"{field_name}[{index}]: expected non-empty string")
        token = item.strip()
        ensure(all(character not in token for character in " \t\r\n/\\"),
               f"{field_name}[{index}]: expected slash-free token without whitespace")
        tokens.append(token)
    ensure(len(set(tokens)) == len(tokens), f"{field_name}: values must be distinct")
    return tuple(tokens)


def validate_owner(owner: Any, index: int) -> None:
    ensure(isinstance(owner, dict), f"owners[{index}]: expected object")
    ensure(set(owner) == {"name", "contact"}, f"owners[{index}]: expected only name/contact")
    ensure(isinstance(owner["name"], str) and owner["name"].strip(), f"owners[{index}].name: required")
    ensure(
        isinstance(owner["contact"], str) and len(owner["contact"].strip()) >= 3,
        f"owners[{index}].contact: required",
    )


def validate_source(source: Any, index: int) -> None:
    ensure(isinstance(source, dict), f"sources[{index}]: expected object")
    allowed = {"kind", "locator", "captured_at", "notes"}
    ensure(set(source).issubset(allowed), f"sources[{index}]: unexpected keys present")
    for key in ("kind", "locator", "captured_at"):
        ensure(key in source, f"sources[{index}].{key}: required")
    ensure(source["kind"] in ALLOWED_SOURCE_KINDS, f"sources[{index}].kind: invalid value")
    ensure(isinstance(source["locator"], str) and source["locator"].strip(), f"sources[{index}].locator: required")
    ensure(isinstance(source["captured_at"], str), f"sources[{index}].captured_at: expected string")
    parse_datetime(source["captured_at"], f"sources[{index}].captured_at")
    if "notes" in source:
        ensure(isinstance(source["notes"], str), f"sources[{index}].notes: expected string")


def validate_content_entry(entry: Any, index: int, source_count: int) -> None:
    ensure(isinstance(entry, dict), f"content[{index}]: expected object")
    allowed = {"id", "type", "body", "source_refs"}
    ensure(set(entry).issubset(allowed), f"content[{index}]: unexpected keys present")
    for key in ("id", "type", "body"):
        ensure(key in entry, f"content[{index}].{key}: required")
    ensure(isinstance(entry["id"], str) and entry["id"].strip(), f"content[{index}].id: required")
    ensure(entry["type"] in ALLOWED_CONTENT_TYPES, f"content[{index}].type: invalid value")
    ensure(isinstance(entry["body"], str) and entry["body"].strip(), f"content[{index}].body: required")
    if "source_refs" in entry:
        ensure(isinstance(entry["source_refs"], list), f"content[{index}].source_refs: expected array")
        for ref in entry["source_refs"]:
            ensure(isinstance(ref, int), f"content[{index}].source_refs: expected integers")
            ensure(0 <= ref < source_count, f"content[{index}].source_refs: out-of-range index {ref}")


def validate_promotion(promotion: Any) -> None:
    ensure(isinstance(promotion, dict), "promotion: expected object")
    allowed = {"status", "reviewed_at", "compatibility", "notes"}
    ensure(set(promotion).issubset(allowed), "promotion: unexpected keys present")
    for key in ("status", "reviewed_at"):
        ensure(key in promotion, f"promotion.{key}: required")
    ensure(promotion["status"] in ALLOWED_PROMOTION_STATUSES, "promotion.status: invalid value")
    ensure(isinstance(promotion["reviewed_at"], str), "promotion.reviewed_at: expected string")
    parse_datetime(promotion["reviewed_at"], "promotion.reviewed_at")
    if "compatibility" in promotion:
        ensure(promotion["compatibility"] in ALLOWED_COMPATIBILITY, "promotion.compatibility: invalid value")
    if "notes" in promotion:
        ensure(isinstance(promotion["notes"], str), "promotion.notes: expected string")


def validate_bundle(bundle: Any, path: Path) -> ValidationResult:
    ensure(isinstance(bundle, dict), f"{path}: root must be an object")
    required = {"schema_version", "bundle_id", "purpose", "owners", "sources", "content", "promotion"}
    ensure(required.issubset(bundle), f"{path}: missing required keys")
    ensure(set(bundle).issubset(required), f"{path}: unexpected top-level keys present")

    ensure(bundle["schema_version"] == "1.0", f"{path}: schema_version must be '1.0'")
    ensure(
        isinstance(bundle["bundle_id"], str) and BUNDLE_ID_RE.fullmatch(bundle["bundle_id"]),
        f"{path}: bundle_id must match {BUNDLE_ID_RE.pattern}",
    )
    ensure(
        isinstance(bundle["purpose"], str) and len(bundle["purpose"].strip()) >= 10,
        f"{path}: purpose must be a meaningful string",
    )

    owners = bundle["owners"]
    ensure(isinstance(owners, list) and owners, f"{path}: owners must be a non-empty array")
    for index, owner in enumerate(owners):
        validate_owner(owner, index)

    sources = bundle["sources"]
    ensure(isinstance(sources, list) and sources, f"{path}: sources must be a non-empty array")
    for index, source in enumerate(sources):
        validate_source(source, index)

    content = bundle["content"]
    ensure(isinstance(content, list) and content, f"{path}: content must be a non-empty array")
    seen_ids: set[str] = set()
    for index, entry in enumerate(content):
        validate_content_entry(entry, index, len(sources))
        entry_id = entry["id"]
        ensure(entry_id not in seen_ids, f"{path}: duplicate content id {entry_id!r}")
        seen_ids.add(entry_id)

    validate_promotion(bundle["promotion"])
    return ValidationResult(path=path, message="bundle is valid")


def validate_bundle_file(path: str | Path) -> ValidationResult:
    bundle_path = Path(path).resolve()
    load_schema()
    bundle = load_json(bundle_path)
    return validate_bundle(bundle, bundle_path)


def load_repository_config(path: Path) -> RepositoryConfig:
    try:
        config = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"{path}: invalid TOML: {exc}") from exc

    ensure("repository" in config, f"{path}: missing [repository] table")
    repository = config["repository"]
    ensure(isinstance(repository, dict), f"{path}: [repository] must be a table")
    for key in ("schema_version", "name", "agent_id"):
        ensure(key in repository, f"{path}: repository.{key} is required")
    ensure(set(repository).issubset({"schema_version", "name", "agent_id"}), f"{path}: unexpected repository keys")
    schema_version = repository["schema_version"]
    ensure(schema_version == "1", f"{path}: repository.schema_version must be '1'")
    name = repository["name"]
    ensure(isinstance(name, str) and name.strip(), f"{path}: repository.name is required")
    agent_id = repository["agent_id"]
    ensure(
        isinstance(agent_id, str) and BUNDLE_ID_RE.fullmatch(agent_id),
        f"{path}: repository.agent_id must match {BUNDLE_ID_RE.pattern}",
    )
    layout_table = config.get("layout", {})
    ensure(isinstance(layout_table, dict), f"{path}: [layout] must be a table")
    ensure(set(layout_table).issubset(DEFAULT_LAYOUT), f"{path}: unexpected layout keys")
    layout_values = {
        key: validate_relative_directory(layout_table.get(key, default), f"{path}: layout.{key}")
        for key, default in DEFAULT_LAYOUT.items()
    }
    validate_distinct_directories(layout_values.values(), f"{path}: layout")
    frontdoor_table = config.get("frontdoor")
    ensure(isinstance(frontdoor_table, dict), f"{path}: [frontdoor] is required")
    ensure(set(frontdoor_table).issubset(FRONTDOOR_KEYS), f"{path}: unexpected frontdoor keys")
    for key in FRONTDOOR_KEYS:
        ensure(key in frontdoor_table, f"{path}: frontdoor.{key} is required")
    frontdoor = FrontDoorConfig(
        pinned_paths=validate_relative_path_list(frontdoor_table["pinned_paths"], f"{path}: frontdoor.pinned_paths"),
        discoverable_paths=validate_relative_path_list(
            frontdoor_table["discoverable_paths"],
            f"{path}: frontdoor.discoverable_paths",
        ),
    )
    promotion_table = config.get("promotion_policy")
    ensure(isinstance(promotion_table, dict), f"{path}: [promotion_policy] is required")
    ensure(set(promotion_table).issubset(PROMOTION_POLICY_KEYS), f"{path}: unexpected promotion_policy keys")
    for key in PROMOTION_POLICY_KEYS:
        ensure(key in promotion_table, f"{path}: promotion_policy.{key} is required")
    promotion_policy = PromotionPolicy(
        promotable_memory_roots=validate_relative_path_list(
            promotion_table["promotable_memory_roots"],
            f"{path}: promotion_policy.promotable_memory_roots",
        ),
        required_validation_kinds=validate_token_list(
            promotion_table["required_validation_kinds"],
            f"{path}: promotion_policy.required_validation_kinds",
        ),
    )
    return RepositoryConfig(
        schema_version=schema_version,
        name=name.strip(),
        agent_id=agent_id,
        layout=RepositoryLayout(**layout_values),
        frontdoor=frontdoor,
        promotion_policy=promotion_policy,
    )


def validate_repo_config(path: Path) -> ValidationResult:
    load_repository_config(path)
    return ValidationResult(path=path, message="context repo config is valid")


def validate_context_repo(path: str | Path) -> list[ValidationResult]:
    root = Path(path).resolve()
    ensure(root.is_dir(), f"{root}: expected a directory")
    config_path = root / "skillfoundry.toml"
    ensure(config_path.exists(), f"{root}: missing skillfoundry.toml")
    config = load_repository_config(config_path)
    results = [ValidationResult(path=config_path, message="context repo config is valid")]

    required_dirs = {
        "bundles": root / config.layout.bundles_dir,
        "memory": root / config.layout.memory_dir,
        "artifacts": root / config.layout.artifacts_dir,
        "runs": root / config.layout.runs_dir,
    }
    for label, directory in required_dirs.items():
        ensure(directory.exists(), f"{root}: missing {label} directory at {directory.relative_to(root)}")
        ensure(directory.is_dir(), f"{root}: expected directory at {directory.relative_to(root)}")

    for relative_path in config.frontdoor.pinned_paths:
        pinned_path = root / relative_path
        ensure(pinned_path.exists(), f"{root}: missing frontdoor pinned path {relative_path}")
        ensure(pinned_path.is_file(), f"{root}: frontdoor pinned path must be a file: {relative_path}")

    for relative_path in config.frontdoor.discoverable_paths:
        discoverable_path = root / relative_path
        ensure(discoverable_path.exists(), f"{root}: missing frontdoor discoverable path {relative_path}")
        ensure(discoverable_path.is_dir(), f"{root}: frontdoor discoverable path must be a directory: {relative_path}")

    bundles_dir = required_dirs["bundles"]
    for bundle_path in sorted(bundles_dir.rglob("*.json")):
        results.append(validate_bundle_file(bundle_path))
    return results
