#!/usr/bin/env python3
"""The built page must load nothing from another host.

Anchor links are deliberately not flagged. A link to GitHub is the page doing
its job; a stylesheet from GitHub is the defect. Conflating the two would make
the check impossible to satisfy and therefore impossible to keep.

What counts as loading a resource: src on any element, href on <link>, and any
url() inside the bundled stylesheet.
"""
import pathlib
import re
import sys

SRC = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)
LINK_TAG = re.compile(r"<link\b[^>]*>", re.I)

# Only these rel values make the browser FETCH something. canonical, alternate,
# author and license are metadata: they describe the page, they do not load it.
# Flagging canonical would make the rule impossible to satisfy for any site with
# an absolute canonical address, which is every site.
FETCHING_REL = {
    "stylesheet", "preload", "prefetch", "preconnect", "dns-prefetch",
    "icon", "shortcut icon", "apple-touch-icon", "mask-icon", "manifest",
    "modulepreload", "prerender",
}
CSS_URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", re.I)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//", re.I)


def offenders(values, where):
    out = []
    for v in values:
        v = v.strip()
        if not v or v.startswith("data:") or v.startswith("#"):
            continue
        if EXTERNAL.match(v):
            out.append(f"{where} loads {v}")
    return out


def main():
    public = pathlib.Path(sys.argv[1])
    errors = []

    html_files = sorted(public.rglob("*.html"))
    if not html_files:
        print("no-external: FAIL no HTML in the built site", file=sys.stderr)
        return 1

    for page in html_files:
        text = page.read_text()
        rel = page.relative_to(public)
        errors += offenders(SRC.findall(text), f"{rel} (src)")
        for tag in LINK_TAG.findall(text):
            rel_m = re.search(r"""\brel\s*=\s*["']([^"']+)["']""", tag, re.I)
            href_m = re.search(r"""\bhref\s*=\s*["']([^"']+)["']""", tag, re.I)
            if not rel_m or not href_m:
                continue
            if rel_m.group(1).strip().lower() in FETCHING_REL:
                errors += offenders([href_m.group(1)], f"{rel} (link rel={rel_m.group(1)})")

    css_files = sorted(public.rglob("*.css"))
    for sheet in css_files:
        rel = sheet.relative_to(public)
        errors += offenders(CSS_URL.findall(sheet.read_text()), f"{rel} (url)")

    # Every preload must name a file the site actually serves, otherwise it is
    # a wasted request and a lie about what is coming.
    for page in html_files:
        text = page.read_text()
        for m in re.finditer(r"""<link\b[^>]*\brel\s*=\s*["']preload["'][^>]*>""", text, re.I):
            tag = m.group(0)
            href = re.search(r"""\bhref\s*=\s*["']([^"']+)["']""", tag)
            if not href:
                errors.append(f"{page.relative_to(public)}: a preload has no href")
                continue
            target = public / href.group(1).lstrip("/")
            if not target.is_file():
                errors.append(
                    f"{page.relative_to(public)}: preloads {href.group(1)}, which the site does not serve"
                )

    if errors:
        for e in errors:
            print(f"no-external: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"no-external: ok, {len(html_files)} page(s) and {len(css_files)} stylesheet(s) "
        f"load only from this origin; every preload resolves"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
