#!/usr/bin/env bash
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
hugo --source . --destination "$work/public" --cacheDir "$work/c" --environment production \
  > "$work/log" 2>&1 || { echo "syntax: the site did not build" >&2; cat "$work/log" >&2; exit 1; }
python3 tests/checks/syntax.py "$work/public"
