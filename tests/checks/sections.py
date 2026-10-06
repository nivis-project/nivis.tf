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
    "roundtrip": ("home/roundtrip.yaml", ["phases"], r'class="phase"'),
    "compare": ("home/compare.yaml", ["rows"], r'<th scope="row"'),
    "projects": ("home/projects.yaml", ["items"], r'class="project-card"'),
    "docs": ("home/docs.yaml", ["links"], r"<li><a href="),
}


def dig(data, path):
    for key in path:
        data = data[key]
    return data


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    html = (public / "index.html").read_text()
    css = "".join(p.read_text() for p in public.rglob("*.css"))
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

    # The comparison must be a real table with scoped headers, otherwise a
    # reader using assistive technology cannot tell what a cell means.
    if "compare" in names:
        cmp_data = yaml.safe_load((root / "data" / "home" / "compare.yaml").read_text())
        cols = len(re.findall(r'<th scope="col"', html))
        want_cols = len(cmp_data["tools"]) + 1  # plus the empty corner cell
        if cols != want_cols:
            errors.append(f"the comparison has {cols} column headers, expected {want_cols}")
        if not re.search(r"<table\b", html):
            errors.append("the comparison is not a real table")

        # The subject column follows a flag in data, not a hard-coded position.
        subject = [i for i, tool in enumerate(cmp_data["tools"]) if tool.get("highlight")]
        if len(subject) != 1:
            errors.append(f"exactly one tool must be flagged as the subject, found {len(subject)}")
        else:
            # One header cell plus one cell per row.
            want_subject = 1 + len(cmp_data["rows"])
            got_subject = len(re.findall(r"is-subject", html))
            if got_subject != want_subject:
                errors.append(
                    f"{got_subject} cells are marked as the subject, expected {want_subject}"
                )

        # A weak tone is emphasis on a distinction the TEXT already makes. If a
        # weak cell were empty, the meaning would rest on colour alone.
        weak_in_data = sum(
            1
            for row in cmp_data["rows"]
            for tool in cmp_data["tools"]
            if isinstance(row.get(tool["key"]), dict) and row[tool["key"]].get("tone") == "weak"
        )
        weak_rendered = len(re.findall(r'data-tone="weak"', html))
        if weak_rendered != weak_in_data:
            errors.append(
                f"{weak_rendered} cells render as qualified, data says {weak_in_data}"
            )
        for m in re.finditer(r'data-tone="weak"[^>]*>([^<]*)<', html):
            if not m.group(1).strip():
                errors.append("a qualified cell has no text, so its meaning rests on colour alone")
                break

    # A card that acts as a link must be ONE link. A card with a link on the
    # title and another on the mark reads as one thing visually and as three to
    # a keyboard.
    for card in re.findall(r'<a class="project-card".*?</a>', html, re.S):
        inner = len(re.findall(r"<a\b", card))
        if inner != 1:
            errors.append(f"a project card contains {inner} link elements, expected exactly 1")
            break
    if re.search(r"<a\b[^>]*>(?:(?!</a>).)*?<a\b", html, re.S):
        errors.append("the page contains a link nested inside another link")

    # Every section is labelled by its own heading, so a reader listing the
    # page's regions sees what each one is.
    for m in re.finditer(r"<section\b([^>]*)>", html):
        attrs = m.group(1)
        if "aria-labelledby" not in attrs and "aria-label" not in attrs:
            errors.append(f"a section has no accessible name: <section{attrs}>")
            break
    labelled = re.findall(r'aria-labelledby="([^"]+)"', html)
    for ref in labelled:
        if f'id="{ref}"' not in html:
            errors.append(f"a section is labelled by #{ref}, which does not exist")

    # Ordinal labels that appear as text are generated from position.
    ordinals = re.findall(r'class="mono-label band-label">(\d+)\s', html)
    if ordinals and [int(o) for o in ordinals] != list(range(1, len(ordinals) + 1)):
        errors.append(f"phase ordinals are {ordinals}, expected consecutive from 1")

    # Exactly these regions may scroll sideways. A new overflow-x anywhere else
    # is how the page itself starts scrolling on a phone.
    ALLOWED_SCROLL = {"figure.code pre", ".table-scroll"}
    scrolling = set()
    for m in re.finditer(r"([^{}]+)\{[^{}]*overflow-x\s*:\s*auto[^{}]*\}", css):
        for sel in m.group(1).split(","):
            sel = sel.strip().split("@")[-1].strip()
            if sel:
                scrolling.add(sel)
    unexpected = scrolling - ALLOWED_SCROLL
    if unexpected:
        errors.append(
            f"these selectors scroll horizontally but are not meant to: {sorted(unexpected)}"
        )
    missing_scroll = ALLOWED_SCROLL - scrolling
    if missing_scroll:
        errors.append(f"these selectors should scroll horizontally but do not: {sorted(missing_scroll)}")

    # Collapsing happens through the grid's minimum width, not breakpoints.
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
