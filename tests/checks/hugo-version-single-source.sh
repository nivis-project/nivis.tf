#!/usr/bin/env bash
# .hugo-version is the only place the Hugo version number may appear.
#
# The flake checks its Hugo against it, and the dev shell, the build and the
# deployment all use the flake's Hugo. This check stops a second copy from
# appearing, which is how two sources quietly disagree.
set -euo pipefail

root="${1:-.}"
pinned="$(cat "$root/.hugo-version")"

# Any version-shaped literal matching the pin, outside the pin file itself.
hits="$(grep -rn --binary-files=without-match -F "$pinned" "$root" \
  --exclude-dir=.git --exclude-dir=.jj --exclude-dir=public \
  --exclude-dir=result --exclude-dir=node_modules --exclude-dir=resources \
  --exclude=.hugo-version --exclude=flake.lock --exclude=CHANGELOG.md \
  || true)"

if [ -n "$hits" ]; then
  echo "hugo-version-single-source: the Hugo version appears outside .hugo-version" >&2
  echo "$hits" >&2
  echo "Read it from .hugo-version instead of copying the number." >&2
  exit 1
fi

echo "hugo-version-single-source: ok, $pinned appears only in .hugo-version"
