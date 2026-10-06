#!/usr/bin/env bash
# The Nu validator over the built site, SVGs included.
#
# It found two real defects the first time it ran: the favicon and the social
# image are generated from the mark partial, which emits INLINE svg. Inline svg
# needs no xmlns and may carry aria-hidden; a standalone .svg FILE requires the
# namespace and rejects both aria-hidden and aria-label on its root element,
# where the accessible name belongs in <title>.
#
# Nothing looked broken: browsers are lenient about loading an SVG via <img>,
# so it would have shipped.
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

hugo --source . --destination "$work/public" --cacheDir "$work/c" --minify --environment production \
  > "$work/log" 2>&1 || { echo "html: the site did not build" >&2; cat "$work/log" >&2; exit 1; }

if ! html5validator --root "$work/public" --also-check-svg > "$work/report" 2>&1; then
  echo "html: the generated markup is not valid" >&2
  cat "$work/report" >&2
  exit 1
fi
if [ -s "$work/report" ]; then
  echo "html: the validator reported messages" >&2
  cat "$work/report" >&2
  exit 1
fi
pages="$(find "$work/public" -name '*.html' | wc -l)"
svgs="$(find "$work/public" -name '*.svg' | wc -l)"
echo "html: ok, $pages page(s) and $svgs SVG(s) validate clean"
