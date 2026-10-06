#!/usr/bin/env python3
"""Verify every generated mark against an independent evaluation of the curve.

The formula comes from section 7 of the briefing:

    r(theta) = a + b * cos(k * theta),   b = a * amp / (k^2 + 1)

sampled at 120 points, rotated, closed, in a -100 -100 200 200 viewBox.

This reimplements it rather than reusing anything from the template. Two
independent implementations of the same formula agreeing is evidence; one
implementation agreeing with itself is not.

Comparison is on the rendered string after rounding, because that is what ships.
Comparing floats before rounding would pass on a Hugo whose formatting changed,
and the formatting is part of the output.
"""
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

SAMPLES = 120

VARIANTS = {
    "full": [
        (84.0, -24.0, "mark-a", "0.3"),
        (80.0, -11.0, "mark-b", "0.3"),
        (78.0, 12.0, "mark-a", "0.3"),
        (74.0, 25.0, "mark-b", "0.3"),
        (64.0, 0.0, "mark-core", "1"),
    ],
    "footer": [
        (80.0, -11.0, "mark-b", "0.3"),
        (78.0, 12.0, "mark-a", "0.3"),
        (64.0, 0.0, "mark-core", "1"),
    ],
    "project": [
        (84.0, -16.0, "mark-a", "0.35"),
        (80.0, 16.0, "mark-b", "0.35"),
        (64.0, 0.0, "mark-core", "1"),
    ],
}


def path_for(a, k, amp, rot_deg):
    b = a * amp / (k * k + 1)
    r0 = math.radians(rot_deg)
    out = []
    for i in range(SAMPLES):
        t = 2 * math.pi * i / SAMPLES
        r = a + b * math.cos(k * t)
        x = r * math.cos(t + r0)
        y = r * math.sin(t + r0)
        out.append(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}")
    return "".join(out) + "Z"


def parse_marks(text):
    marks = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z][a-z0-9-]*):\s*\{\s*k:\s*(-?[\d.]+),\s*amp:\s*(-?[\d.]+),\s*rot:\s*(-?[\d.]+)\s*\}", line)
        if m:
            marks[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    return marks


def blocks(html):
    """Each rendered mark, keyed by (name, variant)."""
    found = {}
    for m in re.finditer(
        r'data-mark="([a-z0-9-]+)" data-variant="([a-z]+)">(.*?)</div>', html, re.S
    ):
        found[(m.group(1), m.group(2))] = m.group(3)
    return found


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    html = normalise(pathlib.Path(sys.argv[2]).read_text())
    marks = parse_marks((root / "data" / "marks.yaml").read_text())
    if not marks:
        print("mark: FAIL could not parse data/marks.yaml", file=sys.stderr)
        return 1

    rendered = blocks(html)
    # VACUOUS-PASS GUARD: with no marks matched there is nothing to compare and
    # the check would report success having verified nothing.
    if not rendered:
        print("mark: FAIL no marks matched in the fixture output", file=sys.stderr)
        return 1
    errors = []
    compared = 0

    for (name, variant), svg in sorted(rendered.items()):
        layer_spec = VARIANTS.get("full" if variant == "labelled" else variant)
        if layer_spec is None:
            errors.append(f"unknown variant {variant!r} in the fixture")
            continue
        if name not in marks:
            errors.append(f"{name!r} is rendered but absent from data/marks.yaml")
            continue
        k, amp, rot = marks[name]

        paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)" fill-opacity="([^"]+)"', svg)
        if len(paths) != len(layer_spec):
            errors.append(
                f"{name}/{variant}: {len(paths)} layers, expected {len(layer_spec)}"
            )
            continue

        for idx, ((got_d, got_fill, got_op), (a, drot, fill, op)) in enumerate(
            zip(paths, layer_spec)
        ):
            want_d = path_for(a, k, amp, rot + drot)
            if got_d != want_d:
                # Report the first differing point, not the whole 120-point path.
                gp = got_d.replace("M", "|M").replace("L", "|L").split("|")[1:]
                wp = want_d.replace("M", "|M").replace("L", "|L").split("|")[1:]
                where = next(
                    (i for i, (g, w) in enumerate(zip(gp, wp)) if g != w), None
                )
                detail = (
                    f"point {where}: got {gp[where]!r}, want {wp[where]!r}"
                    if where is not None
                    else f"length {len(gp)} vs {len(wp)}"
                )
                errors.append(f"{name}/{variant} layer {idx}: {detail}")
            if got_fill != f"var(--{fill})":
                errors.append(f"{name}/{variant} layer {idx}: fill is {got_fill!r}, expected var(--{fill})")
            if got_op != op:
                errors.append(f"{name}/{variant} layer {idx}: opacity {got_op!r}, expected {op!r}")
            compared += 1

    if re.search(r"#[0-9a-fA-F]{3,8}\b|rgb\(|oklch\(", html):
        errors.append("a color literal appears in the generated mark markup")

    # Accessibility: a mark with no text alternative must be hidden.
    for (name, variant), svg in rendered.items():
        has_label = 'role="img"' in svg
        hidden = 'aria-hidden="true"' in svg
        if variant == "labelled":
            if not has_label:
                errors.append(f"{name}/{variant}: expected a text alternative")
        elif not hidden:
            errors.append(f"{name}/{variant}: a decorative mark must be aria-hidden")

    if errors:
        for e in errors:
            print(f"mark: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"mark: ok, {len(rendered)} marks, {compared} layers, "
        f"{compared * SAMPLES} points all match an independent evaluation"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
