#!/usr/bin/env bash
# Wire the shared pre-commit hook into every skillfoundry repo.
# Idempotent — re-run safely after adding new repos.

set -euo pipefail
HOOKS_DIR="/opt/projects/skillfoundry/skillfoundry-harness/scripts/hooks"
chmod +x "$HOOKS_DIR/pre-commit"

for d in /opt/projects/skillfoundry/*/; do
  [[ -d "$d/.git" ]] || continue
  (cd "$d" && git config core.hooksPath "$HOOKS_DIR")
  echo "✓ hooks wired: $(basename "$d")"
done
