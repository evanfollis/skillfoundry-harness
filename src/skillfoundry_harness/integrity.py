"""Stable hashing helpers for durable artifact integrity checks."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_payload(payload: Any) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def sha256_text(content: str) -> str:
    return sha256_bytes(content.encode("utf-8"))
