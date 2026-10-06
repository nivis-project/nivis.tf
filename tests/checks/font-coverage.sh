#!/usr/bin/env bash
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
hugo --source . --destination "$work/public" --cacheDir "$work/c" --minify --environment production \
  > "$work/log" 2>&1 || { echo "font-coverage: the site did not build" >&2; cat "$work/log" >&2; exit 1; }
python3 tests/checks/font-coverage.py "$work/public" "${FONT_SOURCES:-}"
