#!/usr/bin/env bash
# Replays the briefing's acceptance criterion literally, rather than
# paraphrasing it as a property:
#
#   "Adding a project to data/home/projects.yaml and data/marks.yaml adds a
#    card with a generated mark, with no template change."
#
# So it really adds a project, really rebuilds, and really diffs layouts/ and
# assets/ to prove they were untouched. The diff is the part that matters:
# without it a test could pass while somebody had quietly added a special case
# to the template for the new project, which is the failure the criterion is
# written to prevent.
set -euo pipefail
root="${1:-.}"
cd "$root"
ROOT_DIR="$(pwd)"

# The minifier drops quotes around single-token attribute values, so grep
# patterns written against readable markup silently stop matching. Normalise
# every built page before inspecting it. See tests/checks/htmlnorm.py.
norm() { for f in $(find "$1" -name '*.html'); do
  python3 "$ROOT_DIR/tests/checks/htmlnorm.py" < "$f" > "$f.n" && mv "$f.n" "$f"
done; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

hugo --source . --destination "$work/before" --cacheDir "$work/c" --minify --environment production \
  > "$work/log" 2>&1 || { echo "acceptance: the site did not build" >&2; cat "$work/log" >&2; exit 1; }
norm "$work/before"
before_cards="$(grep -c 'class="project-card"' "$work/before/index.html" || true)"

cp -r . "$work/added"
python3 - "$work/added" <<'PY'
import pathlib, sys, yaml
root = pathlib.Path(sys.argv[1])
projects = root / "data" / "home" / "projects.yaml"
marks = root / "data" / "marks.yaml"
d = yaml.safe_load(projects.read_text())
d["items"].append({
    "name": "acceptance-probe",
    "status": "probe",
    "mark": "acceptance-probe",
    "text": "Added by tests/checks/acceptance.sh to replay the briefing's criterion.",
})
projects.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))
m = yaml.safe_load(marks.read_text())
# One parameter, not five. A mark states only where it differs, so the probe
# that replays "adding a project is a data edit" should also be the smallest
# thing that can be added. The four copies the assertion below counts come from
# the default set, which is the point.
m["marks"]["acceptance-probe"] = {"lobes": 7}
marks.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True))
PY

hugo --source "$work/added" --destination "$work/after" --cacheDir "$work/c" --minify --environment production \
  > "$work/added.log" 2>&1 || {
    echo "acceptance: adding a project broke the build" >&2; cat "$work/added.log" >&2; exit 1; }
norm "$work/after"

after_cards="$(grep -c 'class="project-card"' "$work/after/index.html" || true)"
if [ "$after_cards" -ne "$((before_cards + 1))" ]; then
  echo "acceptance: adding a project gave $after_cards cards, expected $((before_cards + 1))" >&2
  exit 1
fi

# The new card must carry a generated mark and the right destination.
card="$(python3 - "$work/after/index.html" <<'PY'
import re, sys, pathlib
h = pathlib.Path(sys.argv[1]).read_text()
m = re.search(r'<a class="project-card" href="([^"]+)">(.*?)</a>', h, re.S)
for m in re.finditer(r'<a class="project-card" href="([^"]+)">(.*?)</a>', h, re.S):
    if "acceptance-probe" in m.group(2):
        paths = len(re.findall(r"<path d=\"M", m.group(2)))
        print(f"{m.group(1)} {paths}")
        break
PY
)"
href="${card%% *}"; paths="${card##* }"
if [ "$href" != "https://github.com/nivis-project/acceptance-probe" ]; then
  echo "acceptance: the new card's destination is '$href', not derived from the organisation URL" >&2
  exit 1
fi
if [ "$paths" -ne 4 ]; then
  echo "acceptance: the new card has $paths generated mark copies, expected 4" >&2
  exit 1
fi

# And nothing under layouts/ or assets/ may have changed.
if ! diff -r layouts "$work/added/layouts" > "$work/difflayouts" 2>&1; then
  echo "acceptance: layouts/ differs after adding a project" >&2
  cat "$work/difflayouts" >&2
  exit 1
fi
if ! diff -r assets "$work/added/assets" > "$work/diffassets" 2>&1; then
  echo "acceptance: assets/ differs after adding a project" >&2
  cat "$work/diffassets" >&2
  exit 1
fi

echo "acceptance: adding a project to the data added a card with a generated mark; layouts/ and assets/ untouched"
