#!/usr/bin/env bash
# Pre-deploy checklist for any new Skillfoundry product.
# Runs gating checks before a product is considered deployable.
# Usage: preflight-deploy.sh <product-directory>

set -euo pipefail
DIR="${1:-.}"
cd "$DIR"
FAIL=0

say() { printf "%-40s %s\n" "$1" "$2"; }
check() { if eval "$2" >/dev/null 2>&1; then say "$1" "✓"; else say "$1" "✗"; FAIL=1; fi; }

echo "=== Pre-deploy checklist: $(pwd) ==="

check ".gitignore present"                 "test -f .gitignore"
check ".gitignore excludes secrets"        "grep -qE '(\\*token\\*|\\*\\.key|\\.env)' .gitignore"
check ".gitignore excludes node_modules"   "grep -q '^node_modules' .gitignore"
check "No secret-looking files staged"     "! git ls-files | grep -iE '(token|secret|\\.env$|\\.key$)'"
check "No node_modules tracked"            "! git ls-files | grep -q '^node_modules/'"
check "package.json or pyproject present"  "test -f package.json -o -f pyproject.toml"
check "README present"                     "test -f README.md"
check "server.json present"                "test -f server.json"
check "Captures userAgent in telemetry"    "grep -rq 'userAgent' src/"
check "Emits telemetry on session events"  "grep -rq 'session_started' src/"
check "Has /health endpoint"               "grep -rq '/health' src/"
check "CTA/nextSteps in tool output"       "grep -rqE '(nextSteps|learnMore|notify)' src/"

echo
if [[ $FAIL -eq 0 ]]; then
  echo "PASS — product ready for deploy."
else
  echo "FAIL — resolve checks above before deploying."
  exit 1
fi
