#!/usr/bin/env python3
"""What can be proven about theming without a browser.

Provable here: the pre-paint code is in the head and above the stylesheet, the
control is a real button with a name, it ships hidden, storage access is
guarded, the toggle reads the computed state, and nothing else ships.

NOT provable here, and deliberately deferred to the end-to-end epic: that no
flash actually occurs, that a choice survives a real reload, that the button is
genuinely invisible with JavaScript off. Those are browser behaviours. This
asserts the mechanism and says plainly which half is deferred.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise


def main():
    public = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    html = normalise((public / "index.html").read_text())
    errors = []

    head = html.split("</head>", 1)[0]

    inline = [m for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)]
    external = re.findall(r"<script[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", html)

    if len(inline) != 1:
        errors.append(f"{len(inline)} inline scripts, expected exactly 1 (the pre-paint snippet)")
    if len(external) != 1:
        errors.append(f"{len(external)} external scripts, expected exactly 1 (the theme switch)")

    if inline:
        snippet = inline[0]
        if snippet.group(0) not in head:
            errors.append("the pre-paint snippet is not in the head, so it cannot run before paint")
        else:
            link = head.find("rel=\"stylesheet\"")
            if link != -1 and head.find(snippet.group(0)) > link:
                errors.append(
                    "the pre-paint snippet comes after the stylesheet link; "
                    "the browser can paint the wrong palette first"
                )
        if "data-theme" not in snippet.group(1):
            errors.append("the pre-paint snippet does not set the theme attribute")
        if "try" not in snippet.group(1) or "catch" not in snippet.group(1):
            errors.append(
                "the pre-paint snippet reads storage unguarded; localStorage throws "
                "in a private window and would stop the script"
            )

    # The control: a real button, named from i18n, shipped hidden.
    button = re.search(r"<button[^>]*data-theme-switch[^>]*>", html)
    if not button:
        errors.append("no theme control, or it is not a button element")
    else:
        tag = button.group(0)
        if "hidden" not in tag:
            errors.append(
                "the theme button does not ship hidden; without JavaScript it would "
                "be present and inert, which a reader cannot tell from a broken page"
            )
        label = re.search(r'aria-label="([^"]*)"', tag)
        if not label or not label.group(1).strip():
            errors.append("the theme button has no accessible name")
        else:
            i18n = (root / "i18n" / "en.yaml").read_text()
            if label.group(1) not in i18n:
                errors.append(
                    f"the theme button's name {label.group(1)!r} is not in i18n/en.yaml, "
                    f"so it is copy living in a template"
                )

    # The script itself.
    js_files = list(public.rglob("*.js"))
    if not js_files:
        errors.append("no JavaScript file in the built site")
    else:
        js = "".join(p.read_text() for p in js_files)
        if "prefers-color-scheme" not in js:
            errors.append(
                "the toggle does not consult the system preference, so the first press "
                "on an unvisited page will pick the wrong direction"
            )
        if "setItem" in js and not re.search(r"try\s*\{[^}]*setItem", js, re.S):
            errors.append("the toggle writes storage unguarded")
        if "hidden" not in js:
            errors.append("the script never reveals the button")

    if errors:
        for e in errors:
            print(f"theming: FAIL {e}", file=sys.stderr)
        return 1

    print(
        "theming: ok, pre-paint snippet in head above the stylesheet, "
        "2 scripts total, button real/named/hidden, storage access guarded"
    )
    print("theming: note, no-flash and persistence across a real reload are browser behaviours, deferred to the e2e epic")
    return 0


if __name__ == "__main__":
    sys.exit(main())
