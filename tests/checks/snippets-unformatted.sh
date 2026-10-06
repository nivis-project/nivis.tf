#!/usr/bin/env bash
# The formatter must never touch snippets/.
#
# This is a regression guard for a defect that actually happened: `nix fmt`
# rewrote snippets/flake.nix, reflowing a sample whose exact formatting is the
# approved copy, and errored on roundtrip-note.nix, which is a fragment rather
# than a complete Nix expression. Both failures are silent from a reader's point
# of view: the page simply shows something other than what was approved.
#
# Checking the formatter's source for an exclusion would test the wrong thing.
# This runs it and compares the bytes.
set -euo pipefail

root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cp -r snippets "$work/before"
nixfmt_targets="$(find snippets -name '*.nix' | sort)"
if [ -z "$nixfmt_targets" ]; then
  echo "snippets-unformatted: no .nix snippets, nothing to guard"
  exit 0
fi

# Run the formatter the way `nix fmt` does: over the whole tree.
find . -name '*.nix' -not -path '*/.*' -not -path '*/snippets/*' -print0 \
  | xargs -0 -r nixfmt >/dev/null 2>&1 || true

if ! diff -r "$work/before" snippets >/dev/null 2>&1; then
  echo "snippets-unformatted: the formatter modified a snippet" >&2
  diff -r "$work/before" snippets >&2 || true
  echo "" >&2
  echo "snippets/ holds approved copy, not source. Exclude it in flake.nix." >&2
  exit 1
fi

n="$(printf '%s\n' "$nixfmt_targets" | wc -l)"
echo "snippets-unformatted: ok, $n .nix snippet(s) survived a formatter run unchanged"
