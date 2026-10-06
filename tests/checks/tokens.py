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
    "ground": ("oklch(0.975 0.008 275)", "oklch(0.17 0.03 275)"),
    "surface": ("oklch(0.995 0.003 275)", "oklch(0.21 0.035 275)"),
    "ink": ("oklch(0.24 0.04 275)", "oklch(0.94 0.012 275)"),
    "muted": ("oklch(0.45 0.035 275)", "oklch(0.76 0.035 275)"),
    "line": ("oklch(0.88 0.02 275)", "oklch(0.34 0.04 275)"),
    "accent": ("oklch(0.42 0.19 275)", "oklch(0.78 0.12 275)"),
    "accent-soft": ("oklch(0.93 0.04 275)", "oklch(0.3 0.07 275)"),
    "warm": ("oklch(0.8 0.14 78)", None),
    "on-warm": ("oklch(0.17 0.03 275)", None),
    "code-bg": ("oklch(0.23 0.045 275)", "oklch(0.13 0.025 275)"),
    "code-ink": ("oklch(0.93 0.015 275)", None),
    "code-dim": ("oklch(0.74 0.05 275)", None),
    "band-bg": ("oklch(0.235 0.09 275)", "oklch(0.23 0.08 275)"),
    "band-ink": ("oklch(0.96 0.01 275)", None),
    "band-muted": ("oklch(0.84 0.04 275)", None),
    "band-line": ("oklch(0.46 0.08 275)", None),
    "band-code": ("oklch(0.19 0.05 275)", "oklch(0.15 0.04 275)"),
    "mark-a": ("oklch(0.6 0.16 250)", "oklch(0.72 0.13 250)"),
    "mark-b": ("oklch(0.55 0.2 305)", "oklch(0.7 0.16 305)"),
    "mark-core": ("oklch(0.37 0.19 275)", "oklch(0.82 0.1 275)"),
    "tok-keyword": ("oklch(0.8 0.13 320)", None),
    "tok-string": ("oklch(0.85 0.11 160)", None),
    "tok-func": ("oklch(0.83 0.1 240)", None),
    "tok-literal": ("oklch(0.85 0.12 78)", None),
}

DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);")


def block_after(css, marker):
    """The declarations of the first rule whose selector contains `marker`."""
    i = css.find(marker)
    if i < 0:
        return None
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

    light = block_after(css, ":root {")
    explicit = block_after(css, ':root[data-theme="dark"]')
    system = block_after(css, "prefers-color-scheme: dark")

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
