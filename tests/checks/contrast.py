#!/usr/bin/env python3
"""Compute contrast ratios from the token values, in both palettes.

Judging contrast by eye, or from a screenshot, tests the screenshot. Computing
it from the defined colours means a token edit that breaks a pairing fails the
gate immediately, naming the pairing and the ratio.

The conversion is OKLCH to Oklab to linear sRGB to relative luminance, following
the CSS Color 4 definitions rather than an approximation, because a wrong
conversion would quietly shift every ratio.
"""
import math
import pathlib
import re
import sys

import yaml

# Pairings the design actually uses, with the minimum each must meet.
# 3.0 where the text is 24px or larger, 4.5 otherwise.
PAIRINGS = [
    ("ink", "ground", 4.5, "body text on the page"),
    ("ink", "surface", 4.5, "body text on an alternating section"),
    ("muted", "ground", 4.5, "secondary text on the page"),
    ("muted", "surface", 4.5, "secondary text on an alternating section"),
    ("accent", "ground", 4.5, "links on the page"),
    ("accent", "surface", 4.5, "links on an alternating section"),
    ("ink", "accent-soft", 4.5, "text in the highlighted table column"),
    ("on-warm", "warm", 4.5, "text on a primary button"),
    ("code-ink", "code-bg", 4.5, "code"),
    ("code-dim", "code-bg", 4.5, "comments and prompts in code"),
    ("code-ink", "band-code", 4.5, "code on the band"),
    ("code-dim", "band-code", 4.5, "comments and prompts on the band"),
    ("band-ink", "band-bg", 4.5, "text on the band"),
    ("band-muted", "band-bg", 4.5, "secondary text on the band"),
    ("tok-keyword", "code-bg", 4.5, "keywords in code"),
    ("tok-string", "code-bg", 4.5, "strings in code"),
    ("tok-func", "code-bg", 4.5, "functions in code"),
    ("tok-literal", "code-bg", 4.5, "literals in code"),
]

OKLCH = re.compile(r"oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)")


def oklch_to_linear_srgb(l, c, h):
    """CSS Color 4: OKLCH -> Oklab -> LMS -> linear sRGB."""
    hr = math.radians(h)
    a = c * math.cos(hr)
    b = c * math.sin(hr)

    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b

    lc, mc, sc = l_ ** 3, m_ ** 3, s_ ** 3

    r = +4.0767416621 * lc - 3.3077115913 * mc + 0.2309699292 * sc
    g = -1.2684380046 * lc + 2.6097574011 * mc - 0.3413193965 * sc
    bl = -0.0041960863 * lc - 0.7034186147 * mc + 1.7076147010 * sc
    return r, g, bl


def relative_luminance(r, g, b):
    """WCAG relative luminance from LINEAR sRGB, clamped to the gamut."""
    r, g, b = (min(max(v, 0.0), 1.0) for v in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    l1, l2 = relative_luminance(*c1), relative_luminance(*c2)
    lo, hi = sorted((l1, l2))
    return (hi + 0.05) / (lo + 0.05)


def parse(value, where):
    m = OKLCH.match(value.strip())
    if not m:
        raise SystemExit(f"contrast: FAIL {where} is {value!r}, which is not an oklch() value")
    return oklch_to_linear_srgb(float(m.group(1)), float(m.group(2)), float(m.group(3)))


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    data = yaml.safe_load((root / "data" / "tokens.yaml").read_text())
    by_name = {c["name"]: c for c in data["colors"]}

    errors = []
    checked = 0
    for theme in ("light", "dark"):
        resolved = {}
        for name, entry in by_name.items():
            value = entry.get("dark", entry["light"]) if theme == "dark" else entry["light"]
            resolved[name] = parse(value, f"{name} ({theme})")

        for fg, bg, minimum, what in PAIRINGS:
            if fg not in resolved or bg not in resolved:
                errors.append(f"{theme}: pairing {fg}/{bg} names a token that does not exist")
                continue
            ratio = contrast(resolved[fg], resolved[bg])
            checked += 1
            if ratio < minimum:
                errors.append(
                    f"{theme}: {what} ({fg} on {bg}) is {ratio:.2f}:1, "
                    f"below the required {minimum}:1"
                )

    # The warm accent is a fill, never a text colour on the page or a surface.
    #
    # An earlier version of this check asserted that warm FAILS contrast in both
    # palettes, and that was wrong: in dark it is around 10:1. The briefing's
    # "insufficient contrast" is about the light palette, where it is under 2:1.
    # The rule still holds in both, because warm is a fill, but contrast is not
    # what enforces it. The CSS does, in tests/checks/warm-is-a-fill.sh.
    #
    # Reported rather than asserted, so the number that motivates the rule stays
    # visible instead of becoming folklore.
    light = {}
    for name, entry in by_name.items():
        light[name] = parse(entry["light"], name)
    warm_note = ", ".join(
        f"warm on {bg} is {contrast(light['warm'], light[bg]):.2f}:1"
        for bg in ("ground", "surface")
    )

    if errors:
        for e in errors:
            print(f"contrast: FAIL {e}", file=sys.stderr)
        return 1

    print(f"contrast: ok, {checked} pairings across both palettes meet their minimums")
    print(f"contrast: note, in the light palette {warm_note}, which is why warm is a fill and never a text colour")
    return 0


if __name__ == "__main__":
    sys.exit(main())
