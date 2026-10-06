#!/usr/bin/env python3
"""Structural assertions over the built page.

These are the things that degrade one section at a time and that nobody notices
until an audit: a second h1, a skipped heading rank, a navigation link to a
section somebody renamed.

A same-page navigation link is the case no link checker catches, because the
address is syntactically fine and never leaves the site.

Navigation entries are checked against the data rather than against whatever the
page happens to contain. The generic anchor scan below only looks at `href="#"`
links, so an entry that leaves the site passes it by never being looked at, and
an entry with a malformed address passes it for the same reason.
"""
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

HEADING = re.compile(r"<h([1-6])\b", re.I)
ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.I)
ANCHOR = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']#([^"']+)["']""", re.I)


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    page = public / "index.html"
    html = normalise(page.read_text())
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
    # Every same-page target is checked unconditionally. While sections were
    # still stubs this carried an UNBUILT_SECTIONS exemption that failed once
    # every section in it resolved, so it could not quietly outlive its purpose.
    # The last section landed, so the exemption is gone rather than left empty:
    # an empty exemption set reads like a disabled guard.
    for t in sorted(targets - ids):
        errors.append(f"a link points at #{t}, which the page does not contain")

    # Every navigation entry, from the data, one of two shapes: a region of this
    # page, which must exist, or an absolute address, which links.py then checks
    # for scheme and host. Anything else is a typo that would otherwise render
    # as a dead relative link.
    nav = yaml.safe_load((root / "data" / "site.yaml").read_text()).get("nav") or []
    # VACUOUS-PASS GUARD: with no entries there is nothing to check and this
    # would report success having looked at nothing.
    if not nav:
        errors.append("data/site.yaml has no navigation entries to check")
    in_page = 0
    for entry in nav:
        href = str(entry.get("href", ""))
        label = entry.get("label", "?")
        if href.startswith("#"):
            in_page += 1
            if href[1:] not in ids:
                errors.append(
                    f"navigation entry {label!r} points at {href}, "
                    f"which the page does not contain"
                )
        elif href.startswith("https://"):
            pass
        else:
            errors.append(
                f"navigation entry {label!r} has address {href!r}, which is "
                f"neither a region of this page nor an absolute https address"
            )
        if href and href not in html:
            errors.append(f"navigation entry {label!r} does not appear on the page")
    # The page's own sections must stay reachable: entries that leave the site
    # are in addition to those, not instead of them.
    if nav and in_page == 0:
        errors.append("no navigation entry points at a region of this page")

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
        f"{len(targets)} same-page links all resolve, "
        f"{len(nav)} navigation entries ({in_page} on this page), "
        f"chrome strings from data, focus and hover rules present"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
