#!/usr/bin/env python3
"""The project's one hard architectural rule, as something the build enforces.

Two scans:

  1. No human-readable copy in a template. Every string a reader sees or hears
     comes from content, data or the translation table.
  2. No style attribute in the generated HTML.

The first is the hard one. A template is mostly things that are NOT copy:
element names, attribute names, class names, template actions. A scan that
treats any word as copy rejects `<section class="hero">` and gets disabled
within a week. So it looks only where text actually reaches a reader: text
nodes, and the values of attributes a reader perceives.

The second scans the OUTPUT rather than the templates, because a template can
compose a style attribute from variables without containing one.
"""
import pathlib
import re
import sys

# Strings a template may contain. Each entry is a hole in the rule and needs a
# reason. It is empty: everything the page shows comes from data or i18n.
ALLOWLIST: set[str] = set()

READER_ATTRS = ("alt", "title", "aria-label", "aria-description", "aria-placeholder", "placeholder")

TEMPLATE_ACTION = re.compile(r"\{\{.*?\}\}", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
# Two or more letters in a row, which is what language looks like. A lone "x"
# or a stray punctuation mark is not copy.
WORDS = re.compile(r"[A-Za-z]{2,}")


def copy_in(path):
    """Text a reader would see or hear, if this template contained any.

    Order matters here, and getting it wrong produced two false positives on the
    first run:

      * Template actions must be removed BEFORE attributes are matched. A Go
        action can contain quotes, as in `aria-label="{{ i18n "theme_switch" }}"`,
        so an attribute regex run first stops at the inner quote and reports the
        fragment as copy.
      * Script and style blocks are code, not language. The theme switch's
        pre-paint snippet was read as a sentence.

    Replacing actions with a letter-free sentinel keeps offsets roughly intact
    so reported line numbers stay useful.
    """
    text = path.read_text()
    text = HTML_COMMENT.sub(" ", text)
    text = SCRIPT_OR_STYLE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = TEMPLATE_ACTION.sub(lambda m: "\x00" * len(m.group(0)), text)

    found = []

    for attr in READER_ATTRS:
        for m in re.finditer(rf'\b{attr}\s*=\s*"([^"]*)"', text):
            value = m.group(1).replace("\x00", "").strip()
            if value and WORDS.search(value):
                line = text[: m.start()].count("\n") + 1
                found.append((line, attr, value))

    for m in re.finditer(r">([^<>]+)<", text):
        chunk = m.group(1).replace("\x00", " ")
        words = [w for w in WORDS.findall(chunk) if w.lower() not in ALLOWLIST]
        if words:
            line = text[: m.start()].count("\n") + 1
            found.append((line, "text", " ".join(words)))

    return found


def scan_templates(root, label):
    errors = []
    templates = sorted(pathlib.Path(root).rglob("*.html"))
    for t in templates:
        for line, where, text in copy_in(t):
            errors.append(f"{t}:{line} has copy in a template ({where}): {text!r}")
    return errors, len(templates)


def scan_output(public):
    errors = []
    pages = sorted(pathlib.Path(public).rglob("*.html"))
    for page in pages:
        html = page.read_text()
        for m in re.finditer(r"<[^>]*\sstyle\s*=", html):
            line = html[: m.start()].count("\n") + 1
            errors.append(f"{page.name}:{line} has an inline style attribute")
            break
    return errors, len(pages)


def main():
    layouts = pathlib.Path(sys.argv[1])
    public = pathlib.Path(sys.argv[2])
    fixtures = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None

    # Prove each scan fires before trusting it on the real tree. A grep with a
    # typo in its pattern passes silently forever.
    if fixtures and fixtures.is_dir():
        copy_fx = fixtures / "copy-in-template"
        style_fx = fixtures / "inline-style"
        if copy_fx.is_dir():
            caught, _ = scan_templates(copy_fx, "fixture")
            if len(caught) < 2:
                print(
                    f"separation: FAIL the copy fixture yielded {len(caught)} hits, "
                    f"expected at least 2 (a label and an accessible name). "
                    f"The scan has a hole.",
                    file=sys.stderr,
                )
                return 1
        if style_fx.is_dir():
            caught, _ = scan_output(style_fx)
            if not caught:
                print(
                    "separation: FAIL the inline-style fixture was not caught; "
                    "the scan has a hole.",
                    file=sys.stderr,
                )
                return 1

    errors, n_templates = scan_templates(layouts, "layouts")
    out_errors, n_pages = scan_output(public)
    errors += out_errors

    if errors:
        for e in errors:
            print(f"separation: FAIL {e}", file=sys.stderr)
        print(
            "separation: move the text to data/ or i18n/en.yaml. Templates hold "
            "markup; content holds words.",
            file=sys.stderr,
        )
        return 1

    print(
        f"separation: ok, {n_templates} templates contain no copy, "
        f"{n_pages} page(s) contain no inline style, both scans proved against fixtures"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
