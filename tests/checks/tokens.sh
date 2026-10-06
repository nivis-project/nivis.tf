#!/usr/bin/env bash
# Build the site, then assert over the GENERATED tokens stylesheet.
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Production, so this parses the bundle that actually ships, minified and all.
hugo --source . --destination "$work/public" --cacheDir "$work/cache" --minify --environment production \
  > "$work/log" 2>&1 || {
  echo "tokens: the site did not build" >&2; cat "$work/log" >&2; exit 1; }

css="$(find "$work/public" -name '*.css' -print -quit)"
if [ -z "$css" ]; then
  echo "tokens: no stylesheet in the built site" >&2
  exit 1
fi
python3 tests/checks/tokens.py "$css"
