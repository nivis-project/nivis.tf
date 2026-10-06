#!/usr/bin/env bash
# The production build: one stylesheet, the right fonts, nothing external.
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

hugo --source . --destination "$work/public" --cacheDir "$work/c" --environment production \
  > "$work/log" 2>&1 || { echo "assets: the site did not build" >&2; cat "$work/log" >&2; exit 1; }
pub="$work/public"

# Exactly one stylesheet, fingerprinted.
sheets="$(grep -o 'rel="stylesheet" href="[^"]*"' "$pub/index.html" | wc -l)"
if [ "$sheets" -ne 1 ]; then
  echo "assets: the page references $sheets stylesheets, expected exactly 1" >&2
  exit 1
fi
href="$(sed -n 's/.*rel="stylesheet" href="\([^"]*\)".*/\1/p' "$pub/index.html")"
if ! printf '%s' "$href" | grep -qE '\.[0-9a-f]{64}\.css$'; then
  echo "assets: the stylesheet name carries no content digest: $href" >&2
  exit 1
fi
if ! grep -q 'integrity="sha256-' "$pub/index.html"; then
  echo "assets: the stylesheet has no integrity attribute" >&2
  exit 1
fi
echo "assets: one fingerprinted stylesheet with integrity"

# Exactly the weights the design uses, and no others.
want="Hind-Medium.woff2 Hind-Regular.woff2 Hind-SemiBold.woff2 IBMPlexMono-Medium.woff2 IBMPlexMono-Regular.woff2"
got="$(cd "$pub/fonts" 2>/dev/null && ls *.woff2 2>/dev/null | sort | tr '\n' ' ' | sed 's/ $//')"
want_sorted="$(printf '%s\n' $want | sort | tr '\n' ' ' | sed 's/ $//')"
if [ "$got" != "$want_sorted" ]; then
  echo "assets: the served fonts are not the set the design uses" >&2
  echo "  want: $want_sorted" >&2
  echo "  got:  $got" >&2
  exit 1
fi
echo "assets: $(printf '%s\n' $want | wc -l) font faces served, exactly the design's set"

# Every face declares a swap, so text is never invisible while a font loads.
css="$(find "$pub" -name '*.css' -print -quit)"
faces="$(grep -o '@font-face' "$css" | wc -l)"
swaps="$(grep -o 'font-display:swap\|font-display: swap' "$css" | wc -l)"
if [ "$faces" -ne "$swaps" ]; then
  echo "assets: $faces font faces but only $swaps declare font-display: swap" >&2
  exit 1
fi
echo "assets: all $faces faces declare font-display: swap"

python3 tests/checks/no-external.py "$pub"
