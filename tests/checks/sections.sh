#!/usr/bin/env bash
set -euo pipefail
root="${1:-.}"
cd "$root"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
hugo --source . --destination "$work/public" --cacheDir "$work/c" --environment production \
  > "$work/log" 2>&1 || { echo "sections: the site did not build" >&2; cat "$work/log" >&2; exit 1; }
python3 tests/checks/sections.py "$work/public" .

# Step numbers must follow POSITION, not the item. Build again from reordered
# data: asserting the first step is numbered 1 proves nothing, because a
# hard-coded "1" in the template would also pass.
cp -r . "$work/reordered"
python3 - "$work/reordered/data/home/quickstart.yaml" <<'PY'
import sys, pathlib, yaml
p = pathlib.Path(sys.argv[1])
d = yaml.safe_load(p.read_text())
d["steps"] = list(reversed(d["steps"]))
p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))
PY
hugo --source "$work/reordered" --destination "$work/rev" --cacheDir "$work/c" --environment production \
  > "$work/rev.log" 2>&1 || { echo "sections: the reordered build failed" >&2; cat "$work/rev.log" >&2; exit 1; }

first_before="$(grep -o 'class="step"[^|]*' "$work/public/index.html" | head -1)"
titles_before="$(grep -oP '(?<=<h3>)[^<]+' "$work/public/index.html" | tail -n +3 | head -4 | tr '\n' '|')"
titles_after="$(grep -oP '(?<=<h3>)[^<]+' "$work/rev/index.html" | tail -n +3 | head -4 | tr '\n' '|')"
nums_after="$(grep -oP '(?<=class="step-number" aria-hidden="true">)\d+' "$work/rev/index.html" | tr '\n' ' ')"

if [ "$titles_before" = "$titles_after" ]; then
  echo "sections: reordering the data did not reorder the steps" >&2
  exit 1
fi
if [ "$nums_after" != "1 2 3 4 " ]; then
  echo "sections: after reordering, the step numbers are '$nums_after', expected '1 2 3 4 '" >&2
  exit 1
fi
echo "sections: step numbers follow position, not the item (proven by reordering)"

# The subject column must follow the FLAG, not a hard-coded position. Move the
# flag to a different tool, rebuild, and assert the distinction moved with it.
# Asserting "the Nivis column is highlighted" would pass against exactly the
# hard-coded template the flag exists to prevent.
cp -r . "$work/reflagged" 2>/dev/null || true
python3 - "$work/reflagged/data/home/compare.yaml" <<'PY'
import sys, pathlib, yaml
p = pathlib.Path(sys.argv[1])
d = yaml.safe_load(p.read_text())
for tool in d["tools"]:
    tool.pop("highlight", None)
d["tools"][3]["highlight"] = True          # NixOps 4, deliberately not first
p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))
PY
hugo --source "$work/reflagged" --destination "$work/flag" --cacheDir "$work/c" --environment production \
  > "$work/flag.log" 2>&1 || { echo "sections: the reflagged build failed" >&2; cat "$work/flag.log" >&2; exit 1; }

# The header cell carrying the distinction must now be the fourth tool.
subject_header="$(grep -oP '(?<=<th scope="col" class="is-subject">)[^<]+' "$work/flag/index.html" | head -1)"
if [ "$subject_header" != "NixOps 4" ]; then
  echo "sections: after moving the highlight flag the subject column is '$subject_header', expected 'NixOps 4'" >&2
  echo "          the template is hard-coding the column instead of reading the flag" >&2
  exit 1
fi
echo "sections: the subject column follows the flag in data (proven by moving it)"
