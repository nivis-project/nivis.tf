#!/usr/bin/env python3
"""Sharing metadata must agree with the page it describes.

The failure this guards is duplication drift: a title in the page, a different
one in the Open Graph tag, a third in the card tag, all slowly diverging until
a shared link contradicts the thing it links to.

It also catches a relative og:image, which looks correct in the markup and fails
only once somebody actually shares the link, because sharing systems resolve
these with no document base.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

REQUIRED = [
    ("link", "canonical"),
    ("meta", "og:type"),
    ("meta", "og:url"),
    ("meta", "og:site_name"),
    ("meta", "og:title"),
    ("meta", "og:description"),
    ("meta", "og:image"),
    ("meta", "og:image:type"),
    ("meta", "og:image:width"),
    ("meta", "og:image:height"),
    ("meta", "twitter:card"),
    ("meta", "twitter:title"),
    ("meta", "twitter:description"),
    ("meta", "twitter:image"),
]

MUST_BE_ABSOLUTE = {"canonical", "og:url", "og:image", "twitter:image"}
PLACEHOLDERS = {"tbd", "todo", "fixme", "xxx", "placeholder", "lorem ipsum", "example.com"}


def value_of(html, kind, name):
    if kind == "link":
        m = re.search(rf'<link[^>]*\brel="{re.escape(name)}"[^>]*\bhref="([^"]*)"', html)
        if not m:
            m = re.search(rf'<link[^>]*\bhref="([^"]*)"[^>]*\brel="{re.escape(name)}"', html)
        return m.group(1) if m else None
    attr = "property" if name.startswith("og:") else "name"
    m = re.search(rf'<meta[^>]*\b{attr}="{re.escape(name)}"[^>]*\bcontent="([^"]*)"', html)
    if not m:
        m = re.search(rf'<meta[^>]*\bcontent="([^"]*)"[^>]*\b{attr}="{re.escape(name)}"', html)
    return m.group(1) if m else None


def main():
    public = pathlib.Path(sys.argv[1])
    html = normalise((public / "index.html").read_text())
    errors = []
    values = {}

    for kind, name in REQUIRED:
        v = value_of(html, kind, name)
        if v is None:
            errors.append(f"{name} is missing")
            continue
        if not v.strip():
            errors.append(f"{name} is present but empty")
            continue
        if v.strip().lower() in PLACEHOLDERS:
            errors.append(f"{name} is a placeholder: {v!r}")
        values[name] = v

    for name in MUST_BE_ABSOLUTE:
        v = values.get(name)
        if v and not re.match(r"^https?://", v):
            errors.append(
                f"{name} is {v!r}, which is relative. Sharing systems resolve these "
                f"with no document base, so it must be absolute."
            )

    # The page's own title and description are the single source.
    page_title = re.search(r"<title>(.*?)</title>", html, re.S)
    page_desc = value_of(html, "meta", "description")
    if page_title:
        for tag in ("og:title", "twitter:title"):
            if values.get(tag) and values[tag] != page_title.group(1):
                errors.append(
                    f"{tag} is {values[tag]!r} but the page title is "
                    f"{page_title.group(1)!r}; a preview must not contradict its page"
                )
    if page_desc:
        for tag in ("og:description", "twitter:description"):
            if values.get(tag) and values[tag] != page_desc:
                errors.append(f"{tag} disagrees with the page's own description")

    # The preview image must be a file the site actually serves.
    img = values.get("og:image")
    if img:
        # A cache-busting query is part of the URL, not of the filename. The
        # generated images sit at fixed paths and cannot carry a digest in the
        # name the way the bundled stylesheet does, so the digest rides in the
        # query instead.
        name = img.rsplit("/", 1)[-1].split("?", 1)[0]
        if not name.endswith(".png"):
            errors.append(
                f"og:image points at {name}; most sharing platforms show nothing "
                f"for an SVG, so the preview must be the rendered PNG"
            )
        if values.get("twitter:image") != img:
            errors.append("twitter:image is not the same image as og:image")
        if values.get("og:image:type") != "image/png":
            errors.append("og:image:type does not say image/png")
        if "?" not in img:
            errors.append(
                "og:image carries no cache-busting query, so a recoloured "
                "image would not reach readers who have visited before"
            )
        source = public / (name.rsplit(".", 1)[0] + ".svg")
        if not source.is_file():
            errors.append(f"the preview image's source {source.name} is not built")
        else:
            body = source.read_text()
            if "<path d=\"M" not in body:
                errors.append("the preview image contains no generated mark")
            if "var(--" in body:
                errors.append(
                    "the preview image still references custom properties, which a "
                    "standalone file cannot resolve"
                )
            size = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', body)
            declared = (values.get("og:image:width"), values.get("og:image:height"))
            if not size:
                errors.append(f"{source.name} declares no width and height")
            elif declared != size.groups():
                errors.append(
                    f"og:image:width/height say {declared}, the image is {size.groups()}"
                )

    # VACUOUS-PASS GUARD: if the tag patterns stopped matching, every lookup
    # would return None and the "missing" errors would fire, so this check
    # cannot pass by finding nothing. Asserted explicitly all the same.
    if not values:
        errors.append("no metadata tags matched at all, which means the patterns are wrong")

    if errors:
        for e in errors:
            print(f"metadata: FAIL {e}", file=sys.stderr)
        return 1

    print(f"metadata: ok, {len(values)} tags, all absolute where required, agreeing with the page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
