#!/usr/bin/env bash
# --warm is a fill, never a text colour.
#
# In the light palette warm on the page background is about 1.76:1, far below
# the 4.5:1 minimum. In dark it is around 10:1, so contrast alone does not
# enforce the rule: a reader in dark mode would see nothing wrong while a reader
# in light mode could not read it at all.
#
# So the rule is enforced where it is actually broken: in the stylesheet.
set -euo pipefail
root="${1:-.}"
cd "$root"

hits="$(grep -rnE '(^|[^-])color\s*:\s*var\(--warm\)' assets/css --include='*.css' || true)"
if [ -n "$hits" ]; then
  echo "warm-is-a-fill: --warm is used as a text colour" >&2
  echo "$hits" >&2
  echo "" >&2
  echo "In the light palette that is about 1.76:1 against the page background." >&2
  echo "Use --warm as a background and --on-warm for the text on it." >&2
  exit 1
fi
echo "warm-is-a-fill: ok, --warm appears only as a fill"
