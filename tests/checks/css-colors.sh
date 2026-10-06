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

# A script can introduce a colour as easily as a stylesheet, and since the hero
# mark is animated in the browser, the rule has to reach there too.
#
# "Builds one from parts" matters as much as a literal. The snippet this site's
# animation grew from assembled hsl() from a hardcoded hue at run time; a scan
# looking only for hex would have called it clean. So the function names are
# matched wherever they appear, open bracket and all, not only inside a
# complete colour.
jspattern="#[0-9a-fA-F]{3,8}\\b|\\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch)\\s*\\(|[\"'\''](($named))[\"'\'']"
jscount=0
if [ -d assets/js ]; then
  jshits="$(grep -rnP "$jspattern" assets/js --include='*.js' || true)"
  if [ -n "$jshits" ]; then
    echo "css-colors: a color value appears in a script" >&2
    echo "$jshits" >&2
    echo "" >&2
    echo "Every color is a token. Select one with var(--name); do not build one." >&2
    exit 1
  fi
  jscount="$(find assets/js -name '*.js' | wc -l)"
fi

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

  jscaught="$(grep -rnP "$jspattern" "$fixture/assets/js" --include='*.js' || true)"
  if [ -z "$jscaught" ]; then
    echo "css-colors: the script negative fixture was not caught; the scan has a hole" >&2
    echo "  $fixture/assets/js/bad.js contains colors this check should reject" >&2
    exit 1
  fi
  jsnotations="$(printf '%s\n' "$jscaught" | wc -l)"
  if [ "$jsnotations" -lt 5 ]; then
    echo "css-colors: the script fixture caught only $jsnotations of 5 notations" >&2
    printf '%s\n' "$jscaught" >&2
    exit 1
  fi
  if ! printf '%s\n' "$jscaught" | grep -q 'assembled'; then
    echo "css-colors: the scan missed a colour ASSEMBLED from parts, which is the" >&2
    echo "  way a script is most likely to introduce one" >&2
    exit 1
  fi
  echo "css-colors: script fixture caught all $jsnotations notations, assembly included"
fi

echo "css-colors: ok, $count stylesheet(s) and $jscount script(s) scanned, no color outside tokens.css"
