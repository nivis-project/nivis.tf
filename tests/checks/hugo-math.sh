#!/usr/bin/env bash
# Proves the pinned Hugo can compute the mark curve at build time.
#
# The mark generator (milestone 04) samples r(theta) = a + b * cos(k * theta)
# in a template. If the pinned Hugo lacks math.Cos, math.Sin or math.Pi, that
# epic is dead on arrival. Finding out here costs a second; finding out there
# costs a Hugo bump that invalidates everything built in between.
#
# The expected value is a literal, not "it rendered something": that also
# catches a Hugo whose float formatting changes, which would silently alter
# every path in every mark.
set -euo pipefail

EXPECTED="${EXPECTED_PATH_DATA:-M92.4 0.0L92.2 4.8L91.5 9.6L90.4 14.3L88.8 18.9L86.9 23.3}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/layouts" "$work/content"

cat > "$work/hugo.yaml" <<'YAML'
baseURL: "https://example.org/"
title: probe
disableKinds: [taxonomy, term, RSS, sitemap]
YAML

cat > "$work/layouts/index.html" <<'TPL'
{{- $k := 3 -}}{{- $a := 84.0 -}}{{- $amp := 1.0 -}}
{{- $b := div (mul $a $amp) (add (mul $k $k) 1) -}}
{{- $d := "" -}}
{{- range $i := seq 0 5 -}}
  {{- $t := div (mul (mul 2 math.Pi) $i) 120.0 -}}
  {{- $r := add $a (mul $b (math.Cos (mul $k $t))) -}}
  {{- $x := mul $r (math.Cos $t) -}}
  {{- $y := mul $r (math.Sin $t) -}}
  {{- $d = printf "%s%s%.1f %.1f" $d (cond (eq $i 0) "M" "L") $x $y -}}
{{- end -}}
{{ $d }}
TPL

touch "$work/content/_index.md"

if ! hugo --quiet --source "$work" --destination "$work/out" 2>"$work/err"; then
  echo "hugo-math: the pinned Hugo could not render the curve template" >&2
  cat "$work/err" >&2
  exit 1
fi

got="$(tr -d '\n' < "$work/out/index.html")"
if [ "$got" != "$EXPECTED" ]; then
  echo "hugo-math: the curve rendered, but not to the expected values" >&2
  echo "  expected: $EXPECTED" >&2
  echo "  got:      $got" >&2
  echo "The reference is the generator in nivis-mockup-reference.html." >&2
  exit 1
fi

echo "hugo-math: ok, math.Cos/math.Sin/math.Pi compute the curve correctly"
