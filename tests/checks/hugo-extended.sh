#!/usr/bin/env bash
# The extended build is required: Hugo Pipes' CSS handling and the asset
# pipeline this site depends on are not in the plain build.
set -euo pipefail

version="$(hugo version)"
if ! printf '%s' "$version" | grep -q 'extended'; then
  echo "hugo-extended: the pinned Hugo is not the extended build" >&2
  echo "  $version" >&2
  exit 1
fi
echo "hugo-extended: ok, $version"
