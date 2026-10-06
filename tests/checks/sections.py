#!/usr/bin/env python3
"""Assert the page agrees with the data, section by section.

The point is to compare counts rather than transcribe expected values. An
assertion like "the audiences section has two cards" is the data copied into the
test: it passes forever and fails only when somebody changes the data and
forgets the test. Asserting that the rendered count equals the data's count
fails when the TEMPLATE drops an item, which is the actual bug.
"""
import pathlib
import re
import sys

import yaml

# Each section: the data file, the path to its collection, and the pattern that
# marks one rendered item. A section in the content list with no entry here
# fails the check, so a new section cannot arrive unguarded.
SECTIONS = {
    "hero": None,  # no collection
    "audiences": ("home/audiences.yaml", ["cards"], r'class="card stack audience-card"'),
    "quickstart": ("home/quickstart.yaml", ["steps"], r'class="step"'),
    "roundtrip": None,
    "compare": None,
    "projects": None,
    "docs": None,
}


def dig(data, path):
    for key in path:
        data = data[key]
    return data


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    html = (public / "index.html").read_text()
    errors = []

    front = (root / "content" / "_index.md").read_text()
    listed = re.search(r"^sections:\s*\[(.*?)\]", front, re.M)
    if not listed:
        print("sections: FAIL no sections list in content/_index.md", file=sys.stderr)
        return 1
    names = [s.strip() for s in listed.group(1).split(",")]

    for name in names:
        if name not in SECTIONS:
            errors.append(
                f"section {name!r} is in content/_index.md but tests/checks/sections.py "
                f"has no entry for it, so it would ship unguarded"
            )

    checked = 0
    for name in names:
        spec = SECTIONS.get(name)
        if spec is None:
            continue
        data_file, path, item_pattern = spec
        data = yaml.safe_load((root / "data" / data_file).read_text())
        want = len(dig(data, path))
        got = len(re.findall(item_pattern, html))
        if got != want:
            errors.append(
                f"{name}: data has {want} item(s) in {'.'.join(path)} but the page renders {got}"
            )
        else:
            checked += 1

    # Numbered items must be consecutive from one and derived from position.
    numbers = [int(n) for n in re.findall(r'class="step-number"[^>]*>(\d+)<', html)]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"step numbers are {numbers}, expected 1..{len(numbers)} in order")

    # The one step with no optional parts must render no empty elements.
    if re.search(r"<p[^>]*>\s*</p>", html):
        errors.append("the page contains an empty paragraph, so an optional part rendered anyway")
    if re.search(r"<a[^>]*>\s*</a>", html):
        errors.append("the page contains an empty link, so an optional part rendered anyway")

    # Collapsing happens through the grid's minimum width, not breakpoints.
    css = "".join(p.read_text() for p in public.rglob("*.css"))
    queries = re.findall(r"@media\s*\(([^)]*)\)", css)
    width_queries = [q for q in queries if "width" in q]
    if width_queries:
        errors.append(f"the stylesheet collapses with width breakpoints: {width_queries}")
    if "auto-fit" not in css:
        errors.append("no auto-fit grid in the stylesheet; columns cannot collapse on their own")

    if errors:
        for e in errors:
            print(f"sections: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"sections: ok, {checked} collection(s) match their data, "
        f"{len(numbers)} numbered items in order, no width breakpoints"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
