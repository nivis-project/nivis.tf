#!/usr/bin/env python3
"""Release readiness: the briefing's acceptance checklist, made executable.

Three things, each closing a gap found by auditing the checklist against the
gate rather than assuming it was covered:

  1. Every one of the seven real snippets matches its file byte for byte. The
     existing test proved this for ONE fixture sample, which is a different and
     much weaker claim than the checklist makes.
  2. The deployment configuration publishes the right directory and takes the
     Hugo version from .hugo-version rather than carrying a second copy.
  3. Every checklist item names a check that exists, or is marked manual. An
     item claiming automated verification with no such check fails here, so the
     checklist cannot drift away from the gate.
"""
import html as htmllib
import pathlib
import re
import sys

# The briefing's section 11, each item mapped to what proves it. "manual" means
# a person has to look; the check reports those as outstanding rather than
# letting a silent pass imply they were verified.
CHECKLIST = [
    ("the site builds with no Hugo warnings", "build"),
    ("no copy in layouts/", "separation"),
    ("no style attribute in the generated HTML", "separation"),
    ("no colour, font or size value in content/, data/ or snippets/", "snippets"),
    ("no colour value in CSS outside tokens.css", "css-colors"),
    ("reordering sections reorders the page", "unit"),
    ("adding a project adds a card with a generated mark, no template change", "acceptance"),
    ("light, dark and system modes work and persist without a flash", "e2e"),
    ("all seven snippets render highlighted and match their files byte for byte", "release"),
    ("usable by keyboard only and at 360px", "e2e"),
    ("the deployment config builds with the pinned Hugo and publishes public/", "release"),
    ("the README explains running, content, tokens, and adding a section or project", "manual"),
]


def rendered_snippets(page_html):
    """Each rendered code block's text, keyed by its position on the page."""
    out = []
    for m in re.finditer(r"<code[^>]*>(.*?)</code>", page_html, re.S):
        text = htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        out.append(text)
    return out


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    page = (public / "index.html").read_text()
    errors = []
    notes = []

    # 1. Every real snippet, not one representative.
    snippet_files = sorted((root / "snippets").iterdir())
    rendered = rendered_snippets(page)
    rendered_norm = [r.rstrip("\n") for r in rendered]
    matched = {}
    for f in snippet_files:
        want = f.read_text().rstrip("\n")
        if want in rendered_norm:
            matched[f.name] = rendered_norm.count(want)
        else:
            near = min(
                rendered_norm,
                key=lambda r: abs(len(r) - len(want)),
                default="",
            )
            errors.append(
                f"snippets/{f.name} does not appear on the page byte for byte. "
                f"Closest rendered block starts {near[:60]!r}"
            )
    if len(matched) != len(snippet_files):
        errors.append(
            f"only {len(matched)} of {len(snippet_files)} snippets were matched exactly"
        )

    # 2. The deployment configuration.
    amplify = root / "amplify.yml"
    if not amplify.is_file():
        errors.append("amplify.yml is missing")
    else:
        conf = amplify.read_text()
        if not re.search(r"baseDirectory:\s*public\b", conf):
            errors.append("amplify.yml does not publish `public`")
        # A command must actually READ the file. Matching the bare filename also
        # matched the comment above it, so the check would have passed on a
        # config that merely mentioned .hugo-version while using something else.
        commands = "\n".join(
            line for line in conf.splitlines() if line.lstrip().startswith("-")
        )
        if not re.search(r"(cat|<)\s+\.hugo-version", commands):
            errors.append(
                "no command in amplify.yml reads .hugo-version, so the deployed Hugo "
                "can differ from the one the gate used. Mentioning it in a comment "
                "is not reading it."
            )
        pinned = (root / ".hugo-version").read_text().strip()
        if pinned in conf:
            errors.append(
                f"amplify.yml contains the literal version {pinned}; it must read "
                f".hugo-version instead of carrying a second copy"
            )
        if not re.search(r"hugo.*--minify|--minify.*hugo", conf, re.S):
            errors.append("amplify.yml does not build with --minify")

    # 3. The checklist cannot drift from the gate.
    flake = (root / "flake.nix").read_text()
    for item, by in CHECKLIST:
        if by == "manual":
            notes.append(item)
            continue
        if not re.search(rf"^\s+{re.escape(by)} =", flake, re.M):
            errors.append(
                f"the checklist item {item!r} claims to be proven by the {by!r} check, "
                f"which does not exist in flake.nix"
            )

    if errors:
        for e in errors:
            print(f"release: FAIL {e}", file=sys.stderr)
        return 1

    automated = len(CHECKLIST) - len(notes)
    print(
        f"release: ok, {len(snippet_files)} snippets match byte for byte, "
        f"the deployment config is single-sourced, and "
        f"{automated} of {len(CHECKLIST)} checklist items are proven by a check that exists"
    )
    for n in notes:
        print(f"release: outstanding, needs a person: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
