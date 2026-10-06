#!/usr/bin/env python3
"""Assertions over the GENERATED tokens stylesheet.

Parsing the output rather than the template matters. Proving the two dark rule
sets agree by reading the template would only restate that the template has one
loop in it. Parsing the output catches a Hugo change, a minifier, or a later
edit that splits the loop.
"""
import pathlib
import re
import sys

BRIEFING = {
    "ground": ("oklch(0.985 0.006 230)", "oklch(0.17 0.035 255)"),
    "surface": ("oklch(0.998 0.003 230)", "oklch(0.21 0.04 255)"),
    "ink": ("oklch(0.26 0.05 258)", "oklch(0.94 0.015 230)"),
    "muted": ("oklch(0.46 0.04 252)", "oklch(0.77 0.035 230)"),
    "line": ("oklch(0.88 0.02 240)", "oklch(0.34 0.045 250)"),
    "accent": ("oklch(0.45 0.19 265)", "oklch(0.80 0.12 230)"),
    "accent-soft": ("oklch(0.93 0.045 235)", "oklch(0.30 0.07 250)"),
    "cta": ("oklch(0.455 0.228 270)", "oklch(0.54 0.19 262)"),
    "on-cta": ("oklch(0.99 0.004 230)", None),
    "code-bg": ("oklch(0.24 0.045 258)", "oklch(0.13 0.03 258)"),
    "code-ink": ("oklch(0.93 0.015 230)", None),
    "code-dim": ("oklch(0.76 0.045 225)", None),
    "band-bg": ("oklch(0.30 0.10 258)", "oklch(0.26 0.09 258)"),
    "band-ink": ("oklch(0.97 0.012 220)", None),
    "band-muted": ("oklch(0.86 0.045 215)", None),
    "band-line": ("oklch(0.50 0.09 250)", None),
    "band-code": ("oklch(0.21 0.06 258)", "oklch(0.17 0.05 258)"),
    "tok-keyword": ("oklch(0.80 0.13 268)", None),
    "tok-string": ("oklch(0.85 0.12 190)", None),
    "tok-func": ("oklch(0.83 0.11 235)", None),
    "tok-literal": ("oklch(0.89 0.085 210)", None),
}

# The last declaration in a minified block has no trailing semicolon, so the
# terminator is a semicolon OR the closing brace. Requiring the semicolon
# silently dropped the last token of every rule set.
DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;}]+)\s*[;}]")


def block_after(css, marker):
    """The declarations of the first rule whose selector matches `marker`.

    `marker` is a regex, because the stylesheet this parses is the shipped
    bundle, which is minified: `:root {` becomes `:root{` and
    `prefers-color-scheme: dark` becomes `prefers-color-scheme:dark`. Parsing
    the minified bundle rather than a readable intermediate is deliberate, it
    is what reaches the reader.
    """
    m = re.search(marker, css)
    if not m:
        return None
    i = m.start()
    start = css.index("{", i)
    depth, j = 0, start
    while j < len(css):
        if css[j] == "{":
            depth += 1
        elif css[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return dict(DECL.findall(css[start : j + 1]))


def main():
    path = pathlib.Path(sys.argv[1])
    css = path.read_text()
    errors = []

    light = block_after(css, r":root\s*\{")
    explicit = block_after(css, r':root\[data-theme=["\']?dark["\']?\]')
    system = block_after(css, r"prefers-color-scheme\s*:\s*dark")

    for name, got in (("light", light), ("explicit dark", explicit), ("system dark", system)):
        if got is None:
            errors.append(f"could not find the {name} rule set in {path}")
    if errors:
        for e in errors:
            print(f"tokens: FAIL {e}", file=sys.stderr)
        return 1

    # The system-dark block is nested, so block_after picks up the outer media
    # rule; its declarations are the inner ones, which is what we want.
    if explicit != system:
        only_e = {k: v for k, v in explicit.items() if system.get(k) != v}
        only_s = {k: v for k, v in system.items() if explicit.get(k) != v}
        errors.append(f"the two dark rule sets disagree: explicit-only {only_e}, system-only {only_s}")

    for name, (want_light, want_dark) in BRIEFING.items():
        if light.get(name) != want_light:
            errors.append(f"--{name} light is {light.get(name)!r}, the briefing says {want_light!r}")
        if want_dark is None:
            if name in explicit:
                errors.append(f"--{name} is the same in both themes but is overridden in dark")
        elif explicit.get(name) != want_dark:
            errors.append(f"--{name} dark is {explicit.get(name)!r}, the briefing says {want_dark!r}")

    for name, value in explicit.items():
        if light.get(name) == value:
            errors.append(f"--{name} is overridden in dark with the value it already has in light")

    missing = set(BRIEFING) - set(light)
    if missing:
        errors.append(f"tokens named in the briefing are missing: {sorted(missing)}")

    if errors:
        for e in errors:
            print(f"tokens: FAIL {e}", file=sys.stderr)
        return 1

    print(f"tokens: ok, {len(light)} tokens, {len(explicit)} dark overrides, both dark rule sets identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
