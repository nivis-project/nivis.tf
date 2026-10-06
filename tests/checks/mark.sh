#!/usr/bin/env bash
# Build the mark fixture and the real site, then verify the geometry.
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

hugo --source tests/fixtures/mark --destination "$work/marks" --cacheDir "$work/c" \
  > "$work/log" 2>&1 || { echo "mark: the fixture did not build" >&2; cat "$work/log" >&2; exit 1; }

python3 tests/checks/mark.py . "$work/marks/index.html"

# The favicon must exist in the real built site and carry generated path data.
hugo --source . --destination "$work/site" --cacheDir "$work/c" \
  > "$work/site.log" 2>&1 || { echo "mark: the site did not build" >&2; cat "$work/site.log" >&2; exit 1; }

fav="$work/site/favicon.svg"
if [ ! -f "$fav" ]; then
  echo "mark: no favicon.svg in the built site" >&2
  exit 1
fi
if ! grep -q '<path d="M' "$fav"; then
  echo "mark: favicon.svg has no generated path data" >&2
  exit 1
fi
if grep -q 'var(--' "$fav"; then
  echo "mark: favicon.svg still references custom properties, which it cannot resolve" >&2
  exit 1
fi
# Its colors must be the token values, not something hand-typed.
for tok in mark-a mark-b mark-core; do
  want="$(grep -oP "(?<=name: $tok,)\s*light: \"\K[^\"]+" data/tokens.yaml | head -1)"
  if ! grep -qF "$want" "$fav"; then
    echo "mark: favicon.svg does not use the $tok token value ($want)" >&2
    exit 1
  fi
done
echo "mark: favicon generated from the same partial, colors inlined from the tokens"
