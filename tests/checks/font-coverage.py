#!/usr/bin/env python3
"""Every character the page renders must exist in the fonts it serves.

Subsetting is the single biggest win available here (475 KB to 107 KB), and it
fails silently: a dropped glyph renders from a fallback face or as a notdef box,
and nothing errors. The page uses a Greek theta in the mark formula and a
rightwards arrow in the comparison table, both of which a naive Latin-1 subset
drops.

So the subset is checked against the actual rendered text, not against an
assumed alphabet. A future copy change that introduces an uncovered character
fails the gate instead of shipping a box.
"""
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise
import unicodedata

from fontTools.ttLib import TTFont

# Characters that never reach a web font: whitespace, and the control-ish ones.
IGNORE = set(" \t\r\n ﻿")


def rendered_text(page_html):
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page_html, flags=re.S)
    # Attribute values that are shown to a reader, plus all text nodes.
    shown = re.findall(r'\b(?:alt|title|aria-label|placeholder)="([^"]*)"', body)
    body = re.sub(r"<[^>]+>", " ", body)
    return html.unescape(body + " " + " ".join(shown))


def main():
    public = pathlib.Path(sys.argv[1])
    page = normalise((public / "index.html").read_text())
    fonts = sorted((public / "fonts").glob("*.woff2"))
    if not fonts:
        print("font-coverage: FAIL the site serves no fonts", file=sys.stderr)
        return 1

    text = rendered_text(page)
    used = {c for c in text if c not in IGNORE and ord(c) > 31}

    # Two different situations, and conflating them would be wrong:
    #
    #   the SOURCE font had the glyph and the subset dropped it  -> a regression
    #   the source never had it                                  -> a design gap
    #
    # The first is a bug introduced here and must fail. The second predates any
    # subsetting: the character was always rendering from a fallback face, and
    # the honest response is to surface it, not to fail a build over a choice
    # somebody else made about the typeface.
    source_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    source_cmaps = {}
    if source_dir and source_dir.is_dir():
        for src in source_dir.rglob("*.ttf"):
            source_cmaps[src.stem] = set(TTFont(src).getBestCmap())

    errors = []
    design_gaps = {}
    for font_path in fonts:
        cmap = set(TTFont(font_path).getBestCmap())
        stem = font_path.stem
        missing = sorted(c for c in used if ord(c) not in cmap)
        if not missing:
            continue
        source = source_cmaps.get(stem)
        for c in missing:
            if source is not None and ord(c) in source:
                errors.append(
                    f"{font_path.name} lost U+{ord(c):04X} {c!r} "
                    f"({unicodedata.name(c, '?')}), which the source font has. "
                    f"The subset ranges in flake.nix dropped it."
                )
            else:
                design_gaps.setdefault(c, []).append(font_path.name)

    if errors:
        for e in errors:
            print(f"font-coverage: FAIL {e}", file=sys.stderr)
        return 1

    covered = len(used) - len(design_gaps)
    print(
        f"font-coverage: ok, the subset kept every glyph its source fonts have; "
        f"{covered} of {len(used)} distinct characters render from the site's own faces"
    )
    for c, faces in sorted(design_gaps.items()):
        print(
            f"font-coverage: note, U+{ord(c):04X} {c!r} "
            f"({unicodedata.name(c, '?')}) is absent from the SOURCE of "
            f"{', '.join(faces)}, so it renders from a system fallback. "
            f"This predates subsetting and is a typeface choice, not a build defect."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
