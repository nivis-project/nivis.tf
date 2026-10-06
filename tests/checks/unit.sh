#!/usr/bin/env bash
# Template assertions, driven by fixture sites under tests/fixtures/.
#
# A fixture is a miniature Hugo site that mounts the project's REAL layouts,
# so what is tested is what Hugo actually does with them. Template logic errors
# (a wrong range variable, a missing with) only ever show up in output, which is
# why these build a site rather than parse a template.
#
# Negative fixtures matter as much as positive ones: a check that only ever
# sees passing input is a check that has never been tested.
set -euo pipefail

root="${1:-.}"
cd "$root"
fixtures="tests/fixtures"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
failed=0

note() { printf '  %s\n' "$1"; }
fail() { printf 'unit: FAIL %s\n' "$1" >&2; failed=1; }

build_ok() {
  local name="$1"
  if ! hugo --source "$fixtures/$name" --destination "$work/$name" \
       --cacheDir "$work/cache" > "$work/$name.log" 2>&1; then
    fail "$name: expected the fixture to build, but it did not"
    sed 's/^/    /' "$work/$name.log" >&2
    return 1
  fi
  return 0
}

build_must_fail() {
  local name="$1" expect="$2"
  if hugo --source "$fixtures/$name" --destination "$work/$name" \
     --cacheDir "$work/cache" > "$work/$name.log" 2>&1; then
    fail "$name: expected the build to FAIL, but it succeeded"
    return 1
  fi
  if ! grep -qF "$expect" "$work/$name.log"; then
    fail "$name: build failed as expected, but the message did not mention: $expect"
    sed 's/^/    /' "$work/$name.log" >&2
    return 1
  fi
  return 0
}

echo "unit: section ordering is driven by content"
if build_ok reorder; then
  got="$(grep -o 'data-section="[a-z-]*"' "$work/reorder/index.html" \
       | sed 's/data-section="//;s/"//' | tr '\n' ' ' | sed 's/ $//')"
  want="docs hero compare hero"
  if [ "$got" = "$want" ]; then
    note "ok: order follows content, and a repeated section renders twice"
  else
    fail "reorder: section order is '$got', expected '$want'"
  fi
  # The same fixture proves removal: it omits five of the seven section types.
  for absent in audiences quickstart projects roundtrip; do
    if grep -q "data-section=\"$absent\"" "$work/reorder/index.html"; then
      fail "reorder: '$absent' is not in the content list but rendered anyway"
    fi
  done
  note "ok: sections absent from the list do not render"
fi

echo "unit: a code sample renders byte for byte"
if build_ok code; then
  python3 - "$work/code/index.html" "$fixtures/code/snippets/sample.nix" <<'PY' || failed=1
import html, re, sys, pathlib

page = pathlib.Path(sys.argv[1]).read_text()
source = pathlib.Path(sys.argv[2]).read_text()

block = re.search(r"<code[^>]*>(.*?)</code>", page, re.S)
if not block:
    print("unit: FAIL code: no <code> block in the rendered page", file=sys.stderr)
    sys.exit(1)

rendered = html.unescape(re.sub(r"<[^>]+>", "", block.group(1)))

if rendered != source.rstrip("\n"):
    print("unit: FAIL code: rendered text does not match the snippet file", file=sys.stderr)
    print(f"    rendered: {rendered!r}", file=sys.stderr)
    print(f"    source:   {source.rstrip(chr(10))!r}", file=sys.stderr)
    sys.exit(1)
print("  ok: rendered code equals snippets/sample.nix exactly")
PY
  if ! grep -q 'class="chroma"' "$work/code/index.html"; then
    fail "code: highlighting did not use Chroma CSS classes"
  else
    note "ok: highlighted with CSS classes, not inline styles"
  fi
  if grep -qE '<code[^>]*style=' "$work/code/index.html"; then
    fail "code: the highlighted block carries inline styles"
  fi
fi

echo "unit: an unknown section fails the build, naming the section"
if build_must_fail unknown-section 'section "this-section-does-not-exist"'; then
  note "ok: the build fails and the message names the section, not a template path"
fi

echo "unit: a missing snippet fails the build, naming the snippet"
if build_must_fail missing-snippet 'snippet "nowhere.nix"'; then
  note "ok: the build fails rather than rendering an empty block"
fi

if [ "$failed" -ne 0 ]; then
  echo "unit: one or more assertions failed" >&2
  exit 1
fi
echo "unit: ok, all assertions passed"
