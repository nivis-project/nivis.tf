#!/usr/bin/env python3
"""Verify every generated mark against an independent evaluation of the curve.

    h(theta) = A + cos(3*theta)          B is fixed at 1
    copy i   = rotated i*phi, scaled step^i
    step     = perfectFit(A, phi) ** (1 - 5*fit)
    perfectFit = min over theta of R(theta)/R(theta - phi)

This reimplements it rather than reusing anything from the template. Two
independent implementations of the same formula agreeing is evidence; one
agreeing with itself is not.

The sampling is stated here, not inherited: perfectFit is a minimisation over a
sampled domain, so this and the template must agree on sample count or they
differ in the last decimal for reasons that have nothing to do with the shape.

Comparison is on the rendered string after rounding, because that is what ships.
"""
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

FIT_SAMPLES = 720     # must match layouts/_partials/mark-fit.html
PATH_POINTS = 120     # must match layouts/_partials/mark.html
FIT_BOUND = 0.2       # above this, step > 1 and the nesting inverts


def R(a, t):
    return a + math.cos(3 * t)


def perfect_fit(a, phi):
    m = float("inf")
    for i in range(FIT_SAMPLES):
        t = 2 * math.pi * i / FIT_SAMPLES
        child = R(a, t - phi)
        if child > 1e-4:
            m = min(m, R(a, t) / child)
    return m


def copy_points(a, rot, s):
    """The rounded coordinates of one copy, in order."""
    out = []
    for k in range(PATH_POINTS + 1):
        t = 2 * math.pi * k / PATH_POINTS
        h = R(a, t)
        out.append((round(s * h * math.cos(t + rot), 1),
                    round(-(s * h * math.sin(t + rot)), 1)))
    return out


# Hugo's minifier rewrites path data four distinct ways, all of which defeat a
# string comparison and the first three of which defeat a naive number scan:
#
#   separators dropped     "M-154.7 0.0" -> "M-154.7.0"  (a second decimal
#                          point starts a new number, so this is valid)
#   absolute -> relative   "L147 -65.5"  -> "l-5-7.1"
#   axis shorthands        a segment moving in one axis -> "V0" or "H70"
#   scientific notation    "-100"        -> "-1e2"
#
# So the path is interpreted rather than scanned: commands are applied, relative
# positions accumulated, and the resulting absolute points compared. The
# comparison is still on rounded coordinates, which was the point of comparing
# strings in the first place.
SVG_TOKEN = re.compile(r"([MmLlHhVvZz])|(-?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][+-]?\d+)?)")


def parse_points(d):
    """Absolute points of a path built from move, line and close commands.

    The minifier uses the shorthands too: H and V for a segment that only moves
    in one axis, and lower-case for relative. All of them have to be applied,
    not merely tokenised, or the positions drift silently partway through.
    """
    pts = []
    x = y = 0.0
    cmd = None
    nums = []

    def flush():
        nonlocal x, y
        if cmd is None:
            nums.clear()
            return
        if cmd in ("H", "h", "V", "v"):
            for n in nums:
                if cmd == "H":
                    x = n
                elif cmd == "h":
                    x += n
                elif cmd == "V":
                    y = n
                else:
                    y += n
                pts.append((round(x, 1), round(y, 1)))
        else:
            for i in range(0, len(nums) - 1, 2):
                dx, dy = nums[i], nums[i + 1]
                if cmd in ("m", "l"):
                    x, y = x + dx, y + dy
                else:
                    x, y = dx, dy
                pts.append((round(x, 1), round(y, 1)))
        nums.clear()

    for letter, number in SVG_TOKEN.findall(d):
        if letter:
            flush()
            cmd = None if letter in ("Z", "z") else letter
        else:
            nums.append(float(number))
    flush()
    return pts


def parse_marks(text):
    marks = {}
    for line in text.splitlines():
        m = re.match(
            r"^([a-z][a-z0-9-]*):\s*\{\s*ratio:\s*(-?[\d.]+),\s*copies:\s*(\d+),"
            r"\s*rot:\s*(-?[\d.]+),\s*fit:\s*(-?[\d.]+)\s*\}",
            line,
        )
        if m:
            marks[m.group(1)] = dict(
                ratio=float(m.group(2)), copies=int(m.group(3)),
                rot=float(m.group(4)), fit=float(m.group(5)),
            )
    return marks


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    html = normalise(pathlib.Path(sys.argv[2]).read_text())
    marks = parse_marks((root / "data" / "marks.yaml").read_text())
    if not marks:
        print("mark: FAIL could not parse data/marks.yaml", file=sys.stderr)
        return 1

    rendered = {}
    for m in re.finditer(r'data-mark="([a-z0-9-]+)" data-copies="(\d+)">(.*?)</div>', html, re.S):
        rendered[(m.group(1), int(m.group(2)))] = m.group(3)

    # VACUOUS-PASS GUARD: with nothing matched there is nothing to compare and
    # the check would report success having verified nothing.
    if not rendered:
        print("mark: FAIL no marks matched in the fixture output", file=sys.stderr)
        return 1

    errors, compared = [], 0
    for (name, copies), svg in sorted(rendered.items()):
        if name not in marks:
            errors.append(f"{name!r} is rendered but absent from data/marks.yaml")
            continue
        p = marks[name]
        a, fit = p["ratio"], p["fit"]
        phi = math.radians(p["rot"])
        if fit > FIT_BOUND:
            errors.append(f"{name}: fit {fit} is above the {FIT_BOUND} bound")
            continue
        step = perfect_fit(a, phi) ** (1 - 5 * fit)
        if step > 1.0 + 1e-9:
            errors.append(f"{name}: step is {step:.4f}; above 1 the nesting inverts")

        paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)" fill-opacity="([^"]+)"', svg)
        if len(paths) != copies:
            errors.append(f"{name}/{copies}: {len(paths)} copies rendered, expected {copies}")
            continue

        scale = 170.0 / (a + 1.0)
        extents = []
        for i, (got_d, got_fill, got_op) in enumerate(paths):
            s = scale * step ** i
            want = copy_points(a, phi * i, s)
            got = parse_points(got_d)
            if got != want:
                where = next((j for j, (g, w) in enumerate(zip(got, want)) if g != w), None)
                detail = (f"point {where}: got {got[where]}, want {want[where]}"
                          if where is not None else f"{len(got)} points vs {len(want)}")
                errors.append(f"{name}/{copies} copy {i}: {detail}")
            if got_fill != f"var(--mark-{copies}-{i})":
                errors.append(f"{name}/{copies} copy {i}: fill is {got_fill!r}")
            extents.append(max(max(abs(x), abs(y)) for x, y in got))
            compared += 1

        # Copies must actually nest: each is contained within the one before.
        for i in range(1, len(extents)):
            if extents[i] > extents[i - 1] + 1e-6:
                errors.append(
                    f"{name}/{copies}: copy {i} extends further than copy {i-1} "
                    f"({extents[i]:.1f} vs {extents[i-1]:.1f}); the nesting is inverted"
                )

    if re.search(r"#[0-9a-fA-F]{3,8}\b|rgb\(|oklch\(|hsl\(", html):
        errors.append("a colour literal appears in the generated mark markup")

    if errors:
        for e in errors:
            print(f"mark: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"mark: ok, {len(rendered)} marks, {compared} copies, "
        f"{compared * (PATH_POINTS + 1)} points all match an independent evaluation, "
        f"and every series nests"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
