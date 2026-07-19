"""Access + integrity/drift helpers for the vendored L1 canon schema bundle.

The harness ships a pinned copy of the discovery-framework JSON Schemas (authored
in the sibling ``context-repository``) under ``schemas/discovery/`` so it can
validate canon envelopes without that sibling checked out. This module is the one
place that knows where the bundle lives and how to check it.

Two independent guarantees, deliberately separated:

- **Integrity** (``verify_bundle_integrity``): the shipped schema files match the
  sha256 digests recorded in ``MANIFEST.json``. Needs nothing external — catches a
  hand-edited or truncated bundle. Enforceable everywhere, including isolated CI.
- **Drift** (``diff_against_canon``): the shipped bundle matches the *canonical*
  source in context-repository. Needs the canon checkout. Detects the bundle
  falling behind canon; the fix is ``scripts/refresh_discovery_schema_bundle.py``.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


BUNDLE_DIR = Path(__file__).resolve().parent.parent / "schemas" / "discovery"
MANIFEST_PATH = BUNDLE_DIR / "MANIFEST.json"
SCHEMA_GLOB = "*.schema.json"

# Where the canonical (authored) schemas live, for drift comparison. The env var
# lets CI point at a fresh context-repository checkout; the default is the
# workspace layout used by local dev and the reflection loop.
CANON_ENV_VAR = "SKILLFOUNDRY_CANON_SCHEMA_DIR"
_DEFAULT_CANON_DIR = Path(
    "/opt/workspace/projects/context-repository/spec/discovery-framework/schemas"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def verify_bundle_integrity() -> list[str]:
    """Return a list of integrity problems; empty means the bundle is intact.

    Checks that every schema recorded in the manifest exists with a matching
    digest, and that no unrecorded ``*.schema.json`` has crept into the bundle.
    """
    problems: list[str] = []
    manifest = load_manifest()
    recorded: dict[str, str] = manifest.get("schemas", {})

    for name, digest in recorded.items():
        path = BUNDLE_DIR / name
        if not path.is_file():
            problems.append(f"missing: {name} recorded in manifest but not on disk")
            continue
        actual = _sha256(path)
        if actual != digest:
            problems.append(
                f"digest mismatch: {name} manifest={digest} actual={actual}"
            )

    on_disk = {p.name for p in BUNDLE_DIR.glob(SCHEMA_GLOB)}
    for extra in sorted(on_disk - set(recorded)):
        problems.append(f"unrecorded: {extra} present in bundle but not in manifest")

    return problems


def canonical_schema_dir() -> Path | None:
    """Best available path to the canonical schema source, or None if absent.

    Prefers the ``SKILLFOUNDRY_CANON_SCHEMA_DIR`` override (set by CI to a
    context-repository checkout); falls back to the workspace default.
    """
    env = os.environ.get(CANON_ENV_VAR)
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    return _DEFAULT_CANON_DIR if _DEFAULT_CANON_DIR.is_dir() else None


def diff_against_canon(canon_dir: Path) -> list[str]:
    """Return a list of drift findings between the bundle and a canon dir.

    Empty means the bundle is an exact mirror of ``canon_dir``. Compares the set
    of schema files and their byte content (via digest).
    """
    findings: list[str] = []
    bundle = {p.name: _sha256(p) for p in BUNDLE_DIR.glob(SCHEMA_GLOB)}
    canon = {p.name: _sha256(p) for p in canon_dir.glob(SCHEMA_GLOB)}

    for missing in sorted(set(canon) - set(bundle)):
        findings.append(f"canon adds {missing}: not in bundle")
    for removed in sorted(set(bundle) - set(canon)):
        findings.append(f"bundle has {removed}: no longer in canon")
    for name in sorted(set(bundle) & set(canon)):
        if bundle[name] != canon[name]:
            findings.append(f"content drift in {name}: bundle != canon")
    return findings
