#!/usr/bin/env bash
# Wire the shared pre-commit hook into every skillfoundry repo.
# Idempotent — re-run safely after adding new repos.

set -euo pipefail
# Discover paths relative to this script; avoid hardcoding server-specific locations.
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEDERATION_ROOT="$(cd "$HOOKS_DIR/../../.." && pwd)"

chmod +x "$HOOKS_DIR/pre-commit"

for d in "$FEDERATION_ROOT"/*/; do
  [[ -d "$d/.git" ]] || continue
  (cd "$d" && git config core.hooksPath "$HOOKS_DIR")
  echo "✓ hooks wired: $(basename "$d")"
done
