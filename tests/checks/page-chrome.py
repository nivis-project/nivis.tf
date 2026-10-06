#!/usr/bin/env python3
"""Structural assertions over the built page.

These are the things that degrade one section at a time and that nobody notices
until an audit: a second h1, a skipped heading rank, a navigation link to a
section somebody renamed.

A same-page navigation link is the case no link checker catches, because the
address is syntactically fine and never leaves the site.
"""
import pathlib
import re
import sys

# Sections whose partials are still empty. A navigation entry may point at one
# of these without resolving yet. This list shrinks to nothing as the sections
# land, and the check fails loudly if it is empty and a target still dangles.
UNBUILT_SECTIONS = {"roundtrip", "compare", "projects"}

HEADING = re.compile(r"<h([1-6])\b", re.I)
ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.I)
ANCHOR = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']#([^"']+)["']""", re.I)


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    page = public / "index.html"
    html = page.read_text()
    errors = []

    ranks = [int(m.group(1)) for m in HEADING.finditer(html)]
    h1s = ranks.count(1)
    if h1s != 1:
        errors.append(f"the page has {h1s} first-level headings, expected exactly 1")
    if ranks and ranks[0] != 1:
        errors.append(f"the first heading on the page is h{ranks[0]}, expected h1")
    for a, b in zip(ranks, ranks[1:]):
        if b > a + 1:
            errors.append(f"heading rank jumps from h{a} to h{b}, skipping a level")
            break

    ids = set(ID.findall(html))
    targets = set(ANCHOR.findall(html))
    dangling = sorted(t for t in targets if t not in ids)
    still_unbuilt = sorted(t for t in dangling if t in UNBUILT_SECTIONS)
    real = sorted(t for t in dangling if t not in UNBUILT_SECTIONS)
    for t in real:
        errors.append(f"a link points at #{t}, which the page does not contain")
    if not still_unbuilt and UNBUILT_SECTIONS:
        # Every exempted section now resolves: the exemption is dead weight.
        resolved = sorted(s for s in UNBUILT_SECTIONS if s in ids)
        if len(resolved) == len(UNBUILT_SECTIONS):
            errors.append(
                "every section in UNBUILT_SECTIONS now resolves; remove the "
                "exemption in tests/checks/page-chrome.py so it guards again"
            )

    # The chrome takes its strings from data, so the data's values must appear.
    site = (root / "data" / "site.yaml").read_text()
    for key in ("name", "license", "domain"):
        m = re.search(rf"^{key}:\s*(.+)$", site, re.M)
        if not m:
            errors.append(f"data/site.yaml has no {key}")
            continue
        value = m.group(1).strip().strip('"')
        if value not in html:
            errors.append(f"site.yaml {key} is {value!r} but it does not appear on the page")

    # Skip link first, and pointing at the main region.
    first_link = re.search(r"""<a\b[^>]*?\bhref\s*=\s*["']#([^"']+)["']""", html)
    if not first_link:
        errors.append("the page has no same-page link at all; the skip link is missing")
    elif first_link.group(1) not in ids:
        errors.append(f"the skip link points at #{first_link.group(1)}, which does not exist")

    # Focus and hover rules must exist. Whether a focus ring is VISIBLE needs a
    # browser; that is the end-to-end epic. Its total absence is the common bug.
    css_text = "".join(p.read_text() for p in public.rglob("*.css"))
    if ":focus-visible" not in css_text:
        errors.append("no :focus-visible rule reaches the page")
    if ":hover" not in css_text:
        errors.append("no :hover rule reaches the page")

    if errors:
        for e in errors:
            print(f"page-chrome: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"page-chrome: ok, 1 h1 and {len(ranks)} headings in rank order, "
        f"{len(targets)} same-page links ({len(still_unbuilt)} awaiting a section), "
        f"chrome strings from data, focus and hover rules present"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
