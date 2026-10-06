#!/usr/bin/env bash
# Build the mark fixture and the real site, then verify the geometry.
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

hugo --source tests/fixtures/mark --destination "$work/marks" --cacheDir "$work/c" \
  > "$work/log" 2>&1 || { echo "mark: the fixture did not build" >&2; cat "$work/log" >&2; exit 1; }

# The favicon must exist in the real built site and carry generated path data,
# and the real page is also where the animated mark lives: the fixture has no
# hero, so the claim that the build renders the resting pose can only be
# checked here.
hugo --source . --destination "$work/site" --cacheDir "$work/c" \
  > "$work/site.log" 2>&1 || { echo "mark: the site did not build" >&2; cat "$work/site.log" >&2; exit 1; }

python3 tests/checks/mark.py . "$work/marks/index.html" "$work/site/index.html"

fav="$work/site/favicon.svg"
if [ ! -f "$fav" ]; then
  echo "mark: no favicon.svg in the built site" >&2
  exit 1
fi
if ! grep -q '<path d="M' "$fav"; then
  echo "mark: favicon.svg has no generated path data" >&2
  exit 1
fi
# The copies are translucent, so what is behind them is part of how the mark
# looks. On the page that is --ground; a standalone file has to carry it, or it
# washes out against whatever the browser composites it on. This regressed the
# moment every copy became translucent.
if ! grep -q '<rect' "$fav"; then
  echo "mark: favicon.svg has no background. Its copies are translucent, so" >&2
  echo "      without one it composites against the browser's own chrome." >&2
  exit 1
fi
if grep -q 'var(--' "$fav"; then
  echo "mark: favicon.svg still references custom properties, which it cannot resolve" >&2
  exit 1
fi
# Its colours must come from the span in data/tokens.yaml, not be hand-typed.
# A standalone file cannot resolve custom properties, so the values are
# substituted; this checks they are the ones the stylesheet would have produced.
python3 - "$fav" <<'PY'
import pathlib, re, sys, yaml
fav = pathlib.Path(sys.argv[1]).read_text()
span = yaml.safe_load(pathlib.Path("data/tokens.yaml").read_text())["mark_span"]
copies = len(re.findall(r"<path", fav))
steps = int(span["ramp_steps"])
want = {
    "hsl(%g %g%% %g%%)" % (
        span["hue_centre"]
        + (int((steps * i) / (copies - 1) + 0.5) / steps - 0.5) * span["hue_spread"],
        span["saturation"], span["lightness"])
    for i in range(copies)
}
got = set(re.findall(r'fill="([^"]+)"', fav))
missing = want - got
if missing:
    print(f"mark: favicon.svg colours do not come from the span: missing {sorted(missing)}",
          file=sys.stderr)
    print(f"      it has {sorted(got)}", file=sys.stderr)
    sys.exit(1)
print(f"mark: favicon colours are the {copies} span steps, substituted from data/tokens.yaml")
PY
echo "mark: favicon generated from the same partial, colors inlined from the tokens"
