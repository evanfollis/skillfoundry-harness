#!/usr/bin/env python3
"""Refresh the vendored L1 discovery-framework schema bundle from canon.

The harness validates discovery canon envelopes (claims, evidence, decisions,
event-log entries, policies) against JSON Schemas that are *authored* in the
sibling `context-repository` (the L1 canon). To stay self-sufficient — installable
and testable without that sibling checked out — the harness carries a pinned copy
of those schemas under ``src/skillfoundry_harness/schemas/discovery/`` plus a
``MANIFEST.json`` recording each file's sha256 and the exact canon commit the copy
was cut from.

This script regenerates that bundle. Run it whenever the drift guard
(``tests/test_discovery_adapter.py::test_bundled_schemas_match_canonical_source``)
reports that canon has moved ahead of the bundle:

    python3 scripts/refresh_discovery_schema_bundle.py \
        --canon /opt/workspace/projects/context-repository

then review the diff, run the tests, and commit the bundle together with its
manifest so the digest and the files never diverge.

It intentionally has no third-party dependencies so it can run under a bare
interpreter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "src" / "skillfoundry_harness" / "schemas" / "discovery"
MANIFEST_PATH = BUNDLE_DIR / "MANIFEST.json"
CANON_SUBPATH = Path("spec/discovery-framework/schemas")
SCHEMA_GLOB = "*.schema.json"


def sha256_of(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canon_commit(canon_repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(canon_repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--canon", type=Path,
        default=Path("/opt/workspace/projects/context-repository"),
        help="Path to a context-repository checkout (its root).",
    )
    ap.add_argument(
        "--generated-at", default="",
        help="ISO date stamp to record as the bundle cut date (optional).",
    )
    args = ap.parse_args()

    canon_schema_dir = args.canon / CANON_SUBPATH
    if not canon_schema_dir.is_dir():
        print(f"ERROR canon schema dir not found: {canon_schema_dir}", file=sys.stderr)
        return 1

    sources = sorted(canon_schema_dir.glob(SCHEMA_GLOB))
    if not sources:
        print(f"ERROR no {SCHEMA_GLOB} under {canon_schema_dir}", file=sys.stderr)
        return 1

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    # Drop any stale vendored schemas no longer present in canon, so the bundle
    # is an exact mirror rather than an accreting pile.
    for stale in BUNDLE_DIR.glob(SCHEMA_GLOB):
        if stale.name not in {s.name for s in sources}:
            stale.unlink()
            print(f"removed stale {stale.name}")

    digests: dict[str, str] = {}
    for src in sources:
        dst = BUNDLE_DIR / src.name
        dst.write_bytes(src.read_bytes())
        digests[src.name] = sha256_of(dst)
        print(f"vendored {src.name}")

    manifest = {
        "_comment": (
            "Pinned copy of the L1 discovery-framework JSON Schemas from "
            "context-repository. Do not hand-edit the schema files or this "
            "manifest; regenerate with scripts/refresh_discovery_schema_bundle.py "
            "and commit together. The drift guard in the test suite compares this "
            "against the canonical source."
        ),
        "source": {
            "repo": "github.com/evanfollis/context-repository",
            "path": str(CANON_SUBPATH),
            "commit": canon_commit(args.canon),
        },
        "generated_at": args.generated_at,
        "schemas": digests,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)} ({len(digests)} schemas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
