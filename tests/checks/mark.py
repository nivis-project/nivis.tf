#!/usr/bin/env python3
"""Verify every generated mark against an independent evaluation of the curve.

    h(theta) = A + cos(k*theta)          B is fixed at 1, k is the lobe count
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
import html as html_mod
import json
import math
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

FIT_SAMPLES = 720     # must match layouts/_partials/mark-fit.html
PATH_POINTS = 120     # must match layouts/_partials/mark.html
FIT_BOUND = 0.2       # above this, step > 1 and the nesting inverts
# A rotation of a whole period leaves the curve unchanged, so the scale is 1 and
# every copy is drawn at its parent's size. Not tested against 1 exactly: the two
# cosines are mathematically equal there but are computed separately, so the
# ratio lands a few bits under. This is a tolerance for that arithmetic, not a
# visibility threshold. Must match layouts/_partials/mark.html.
DEGENERATE_STEP = 0.999


def R(a, k, t):
    return a + math.cos(k * t)


def perfect_fit(a, k, phi):
    m = float("inf")
    for i in range(FIT_SAMPLES):
        t = 2 * math.pi * i / FIT_SAMPLES
        child = R(a, k, t - phi)
        if child > 1e-4:
            m = min(m, R(a, k, t) / child)
    return m


def copy_points(a, k, rot, s):
    """The rounded coordinates of one copy, in order."""
    out = []
    for i in range(PATH_POINTS + 1):
        t = 2 * math.pi * i / PATH_POINTS
        h = R(a, k, t)
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
    """Every entry in data/marks.yaml that describes a mark.

    An entry may carry an `animate` block alongside its parameters. That block
    is the hero's sweep and says nothing about the shape the build draws, so it
    is ignored here.
    """
    marks = {}
    for name, p in (yaml.safe_load(text) or {}).items():
        if not isinstance(p, dict) or "ratio" not in p:
            continue
        marks[name] = dict(
            lobes=int(p.get("lobes", 3)),
            ratio=float(p["ratio"]), copies=int(p["copies"]),
            rot=float(p["rot"]), fit=float(p["fit"]),
        )
    return marks


def tone(i, copies, steps):
    """The ramp step a copy selects, matching layouts/_partials/mark.html.

    Rounded away from zero rather than with Python's half-to-even, because Go's
    math.Round does that. Every supported copy count divides the ramp exactly,
    so this only matters if that stops being true, and then it should disagree
    loudly rather than quietly.
    """
    return int(math.floor((steps * i) / (copies - 1) + 0.5))


def check_animated(path):
    """The animated mark on the real page rests at the pose it declares.

    The fixture cannot cover this: the hero carries an animation range, and the
    claim is that what the build drew is the resting end of that range. If it
    were not, the mark would snap the moment the script ran, and the browser
    suite's no-jump test would be comparing two wrong shapes to each other.
    """
    html = normalise(path.read_text())
    m = re.search(r'<svg[^>]*data-mark-animation="([^"]*)"[^>]*>(.*?)</svg>', html, re.S)
    if not m:
        return ["no animated mark in the built page"]

    cfg = json.loads(html_mod.unescape(m.group(1)))
    rest = cfg["rest"]
    a, copies, fit = float(rest["ratio"]), int(rest["copies"]), float(rest["fit"])
    k = int(rest["lobes"])
    phi = math.radians(float(rest["rot"]))
    steps = int(cfg["rampSteps"])

    paths = re.findall(
        r'<path d="([^"]+)" fill="([^"]+)" fill-opacity="([^"]+)"', m.group(2)
    )
    if len(paths) != copies:
        return [f"the animated mark draws {len(paths)} copies, declares {copies}"]

    errors = []
    step = perfect_fit(a, k, phi) ** (1 - 5 * fit)
    scale = 170.0 / (a + 1.0)
    for i, (got_d, got_fill, got_op) in enumerate(paths):
        want = copy_points(a, k, phi * i, scale * step ** i)
        got = parse_points(got_d)
        if got != want:
            where = next((j for j, (g, w) in enumerate(zip(got, want)) if g != w), None)
            errors.append(
                f"the animated mark's copy {i} does not rest at its declared pose: "
                + (f"point {where}: got {got[where]}, want {want[where]}"
                   if where is not None else f"{len(got)} points vs {len(want)}")
            )
        want_fill = f"var(--mark-ramp-{tone(i, copies, steps)})"
        if got_fill != want_fill:
            errors.append(
                f"the animated mark's copy {i}: fill is {got_fill!r}, want {want_fill!r}"
            )
        if abs(float(got_op) - float(rest["opacity"])) > 1e-9:
            errors.append(
                f"the animated mark's copy {i}: opacity is {got_op}, "
                f"declares {rest['opacity']}"
            )

    for key in ("ratio", "copies", "rot", "fit", "opacity"):
        lo, hi = cfg["range"][key]
        if not (lo <= float(rest[key]) <= hi):
            errors.append(
                f"the resting {key} is {rest[key]}, outside its own sweep {lo} to {hi}"
            )
    return errors


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    html = normalise(pathlib.Path(sys.argv[2]).read_text())
    marks = parse_marks((root / "data" / "marks.yaml").read_text())
    span = yaml.safe_load((root / "data" / "tokens.yaml").read_text())["mark_span"]
    ramp_steps = int(span["ramp_steps"])
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
        a, fit, k = p["ratio"], p["fit"], p["lobes"]
        phi = math.radians(p["rot"])
        if fit > FIT_BOUND:
            errors.append(f"{name}: fit {fit} is above the {FIT_BOUND} bound")
            continue
        step = perfect_fit(a, k, phi) ** (1 - 5 * fit)
        if step >= DEGENERATE_STEP:
            errors.append(
                f"{name}: step is {step:.4f}, at or above {DEGENERATE_STEP}. "
                f"Every copy is drawn at its parent's size, so the series is "
                f"not visible"
            )

        paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)" fill-opacity="([^"]+)"', svg)
        if len(paths) != copies:
            errors.append(f"{name}/{copies}: {len(paths)} copies rendered, expected {copies}")
            continue

        scale = 170.0 / (a + 1.0)
        extents = []
        for i, (got_d, got_fill, got_op) in enumerate(paths):
            s = scale * step ** i
            want = copy_points(a, k, phi * i, s)
            got = parse_points(got_d)
            if got != want:
                where = next((j for j, (g, w) in enumerate(zip(got, want)) if g != w), None)
                detail = (f"point {where}: got {got[where]}, want {want[where]}"
                          if where is not None else f"{len(got)} points vs {len(want)}")
                errors.append(f"{name}/{copies} copy {i}: {detail}")
            want_fill = f"var(--mark-ramp-{tone(i, copies, ramp_steps)})"
            if got_fill != want_fill:
                errors.append(
                    f"{name}/{copies} copy {i}: fill is {got_fill!r}, want {want_fill!r}"
                )
            # How far the copy reaches from the centre. NOT max(|x|, |y|):
            # that is an axis-aligned box, every copy is drawn rotated, and a
            # box is not rotation-invariant. A two-lobed copy rotated back
            # towards an axis has a larger box than its parent while sitting
            # entirely inside it, so the box measure failed correct marks.
            extents.append(max(math.hypot(x, y) for x, y in got))
            compared += 1

        # Copies must actually nest: each is contained within the one before.
        for i in range(1, len(extents)):
            if extents[i] > extents[i - 1] + 1e-6:
                errors.append(
                    f"{name}/{copies}: copy {i} reaches further from the centre "
                    f"than copy {i-1} ({extents[i]:.1f} vs {extents[i-1]:.1f}); "
                    f"the nesting is inverted"
                )

    counts = {p["lobes"] for p in marks.values()}
    if len(counts) < 2:
        errors.append(
            f"every mark has the same lobe count {counts}, so the lobe count is "
            f"not being exercised and this check is testing one case while "
            f"reporting several"
        )

    for n in range(2, int(span["max_copies"]) + 1):
        if ramp_steps % (n - 1) != 0:
            errors.append(
                f"the ramp has {ramp_steps} steps, which {n} copies does not "
                f"divide evenly, so an animated mark cannot land on the same "
                f"colours the build chose"
            )

    if re.search(r"#[0-9a-fA-F]{3,8}\b|rgb\(|oklch\(|hsl\(", html):
        errors.append("a colour literal appears in the generated mark markup")

    animated = 0
    if len(sys.argv) > 3:
        found = check_animated(pathlib.Path(sys.argv[3]))
        errors.extend(found)
        animated = 1

    if errors:
        for e in errors:
            print(f"mark: FAIL {e}", file=sys.stderr)
        return 1

    if animated:
        print("mark: the animated mark rests at the pose it declares, and that "
              "pose lies inside its own sweep")

    print(
        f"mark: ok, {len(rendered)} marks, {compared} copies, "
        f"{compared * (PATH_POINTS + 1)} points all match an independent evaluation, "
        f"and every series nests"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
