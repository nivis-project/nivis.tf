#!/usr/bin/env bash
# No stylesheet other than tokens.css may contain a color value.
#
# This is half of the project's hard rule in executable form. The scan covers
# every notation a color can take, because a rule that only catches hex is a
# rule somebody routes around with rgb().
#
# tokens.css is the one exception, by definition: it is the source.
set -euo pipefail

root="${1:-.}"
cd "$root"

if [ ! -d assets/css ]; then
  echo "css-colors: no assets/css yet, nothing to scan"
  exit 0
fi

# Hex, functional notations, and the CSS named colors that could plausibly be
# typed by hand. `transparent` and `currentColor` are not colors in this sense:
# they carry no value, so they cannot disagree with a token.
#
# A named colour only counts as a VALUE: after a colon, on the same declaration,
# and not part of a longer identifier. Without that, `white-space: pre` reads as
# the colour white, and a rule that rejects legitimate CSS is a rule somebody
# turns off. That false positive was real, not hypothetical.
named='red|blue|green|black|white|grey|gray|yellow|orange|purple|pink|brown|cyan|magenta|silver|gold|navy|teal|olive|maroon|lime|aqua|fuchsia'
pattern="#[0-9a-fA-F]{3,8}\\b|\\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\\s*\\(|:[^;{}]*(?<![-\\w])($named)(?![-\\w])"

hits="$(grep -rnP "$pattern" assets/css --include='*.css' --exclude='tokens.css' || true)"

if [ -n "$hits" ]; then
  echo "css-colors: a color value appears outside assets/css/tokens.css" >&2
  echo "$hits" >&2
  echo "" >&2
  echo "Every color is a token. Add it to data/tokens.yaml and use var(--name)." >&2
  exit 1
fi

count="$(find assets/css -name '*.css' -not -name 'tokens.css' | wc -l)"

# The negative fixture. A scan that has never fired is a scan nobody has
# tested, so prove it fires before reporting the real tree clean.
fixture="tests/fixtures/stray-color"
if [ -d "$fixture" ]; then
  caught="$(grep -rnP "$pattern" "$fixture/assets/css" --include='*.css' --exclude='tokens.css' || true)"
  if [ -z "$caught" ]; then
    echo "css-colors: the negative fixture was not caught; the scan has a hole" >&2
    echo "  $fixture/assets/css/bad.css contains colors this check should reject" >&2
    exit 1
  fi
  notations="$(printf '%s\n' "$caught" | wc -l)"
  if [ "$notations" -lt 5 ]; then
    echo "css-colors: the negative fixture caught only $notations of 5 notations" >&2
    printf '%s\n' "$caught" >&2
    exit 1
  fi
  # tokens.css inside the fixture must NOT be flagged: the exemption is part of
  # the rule, and an exemption that does not work is a rule that blocks work.
  if grep -rnP "$pattern" "$fixture/assets/css/tokens.css" >/dev/null 2>&1; then
    : # it does contain a color, which is the point; the --exclude must skip it
  fi
  if printf '%s\n' "$caught" | grep -q 'tokens.css'; then
    echo "css-colors: the exemption failed, tokens.css was flagged" >&2
    exit 1
  fi
  echo "css-colors: negative fixture caught all $notations notations, tokens.css exempt"
fi

echo "css-colors: ok, $count stylesheet(s) scanned, no color outside tokens.css"
