"""Typed bundle loading for validated context inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .validation import load_json, validate_bundle


@dataclass(frozen=True)
class BundleOwner:
    name: str
    contact: str


@dataclass(frozen=True)
class BundleSource:
    kind: str
    locator: str
    captured_at: str
    notes: str | None = None


@dataclass(frozen=True)
class BundleContentEntry:
    entry_id: str
    content_type: str
    body: str
    source_refs: tuple[int, ...] = ()


@dataclass(frozen=True)
class BundlePromotion:
    status: str
    reviewed_at: str
    compatibility: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ContextBundle:
    path: Path
    schema_version: str
    bundle_id: str
    purpose: str
    owners: tuple[BundleOwner, ...]
    sources: tuple[BundleSource, ...]
    content: tuple[BundleContentEntry, ...]
    promotion: BundlePromotion

    def snapshot(self) -> dict[str, Any]:
        return {
            "path": self.path.as_posix(),
            "bundle_id": self.bundle_id,
            "purpose": self.purpose,
            "promotion_status": self.promotion.status,
            "content_entries": len(self.content),
            "source_count": len(self.sources),
        }


class BundleStore:
    """Load validated bundles from the repository bundle root."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def list(self) -> list[ContextBundle]:
        return [self.load_path(path) for path in self.repository.bundle_paths()]

    def load(self, bundle_id: str) -> ContextBundle:
        for path in self.repository.bundle_paths():
            candidate = self.load_path(path)
            if candidate.bundle_id == bundle_id:
                return candidate
        raise FileNotFoundError(f"bundle not found: {bundle_id}")

    def load_path(self, path: Path) -> ContextBundle:
        payload = load_json(path)
        validate_bundle(payload, path)
        return ContextBundle(
            path=path,
            schema_version=payload["schema_version"],
            bundle_id=payload["bundle_id"],
            purpose=payload["purpose"],
            owners=tuple(BundleOwner(**owner) for owner in payload["owners"]),
            sources=tuple(BundleSource(**source) for source in payload["sources"]),
            content=tuple(
                BundleContentEntry(
                    entry_id=entry["id"],
                    content_type=entry["type"],
                    body=entry["body"],
                    source_refs=tuple(entry.get("source_refs", ())),
                )
                for entry in payload["content"]
            ),
            promotion=BundlePromotion(**payload["promotion"]),
        )
