#!/usr/bin/env python3
"""Snippets and the data that references them must agree, in both directions.

The forward direction (every reference resolves) is obvious. The reverse
direction (every file is referenced) is the one that rots silently: a snippet
nobody references is either dead weight or, worse, a sample somebody edited
believing it was on the page.
"""
import pathlib
import re
import sys

import yaml

REFERENCE = re.compile(r"\bfile:\s*([A-Za-z0-9._-]+)")
# Markup, class attributes and style values have no business in content.
FORBIDDEN = [
    (re.compile(r"<\s*/?\s*(div|span|p|br|strong|em|a|section|ul|li|table|h[1-6])\b", re.I),
     "an HTML tag"),
    (re.compile(r'\bclass\s*=\s*["\']'), "a CSS class attribute"),
    (re.compile(r'\bstyle\s*=\s*["\']'), "a style attribute"),
    (re.compile(r"#[0-9a-fA-F]{6}\b|\b(rgba?|hsla?|oklch|oklab)\s*\("), "a color value"),
    (re.compile(r"\b\d+(\.\d+)?(px|rem|em|vw|vh)\b"), "a size value"),
]


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    data = root / "data"
    snippets = root / "snippets"
    errors = []

    data_files = sorted(p for p in data.rglob("*.yaml") if p.name != "tokens.yaml")
    text = {p: p.read_text() for p in data_files}

    referenced = set()
    for p, t in text.items():
        for name in REFERENCE.findall(t):
            referenced.add(name)
            if not (snippets / name).is_file():
                errors.append(f"{p.relative_to(root)} references snippets/{name}, which does not exist")

    on_disk = {p.name for p in snippets.iterdir() if p.is_file()}
    for orphan in sorted(on_disk - referenced):
        errors.append(f"snippets/{orphan} exists but no data file references it")

    # Content must stay free of markup and style values. tokens.yaml is exempt:
    # it is the one file whose entire purpose is to hold style values.
    content_sources = data_files + sorted(snippets.iterdir()) + sorted((root / "content").rglob("*.md"))
    for p in content_sources:
        if not p.is_file():
            continue
        body = p.read_text()
        for pattern, what in FORBIDDEN:
            # Snippets are code samples: HCL, Nix and shell legitimately contain
            # things that look like sizes, and the samples are quoted verbatim.
            if p.parent.name == "snippets" and what in ("a size value", "a color value"):
                continue
            m = pattern.search(body)
            if m:
                line = body[: m.start()].count("\n") + 1
                errors.append(f"{p.relative_to(root)}:{line} contains {what}: {m.group(0)!r}")

    # Every project must resolve to a mark that has parameters.
    import json
    projects = (data / "home" / "projects.yaml").read_text()
    # Parsed rather than pattern-matched: an entry may be written as a block
    # when it carries an animation range, and a regex for the one-line form
    # silently stops seeing it.
    marks = yaml.safe_load((data / "marks.yaml").read_text()) or {}
    declared = set(marks.get("marks") or {})
    used = set(re.findall(r"^\s+mark:\s*([a-z0-9-]+)\s*$", projects, re.M))
    for m in sorted(used - declared):
        errors.append(f"data/home/projects.yaml uses mark {m!r}, which has no parameters in data/marks.yaml")

    if errors:
        for e in errors:
            print(f"snippets: FAIL {e}", file=sys.stderr)
        return 1

    print(f"snippets: ok, {len(on_disk)} files, all referenced and all present; "
          f"{len(used)} project marks resolve; no markup or style values in content")
    return 0


if __name__ == "__main__":
    sys.exit(main())
