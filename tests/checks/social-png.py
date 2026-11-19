#!/usr/bin/env python3
import pathlib
import re
import sys

import yaml
from coloraide import Color
from PIL import Image

TEXT_REGION = (500, 150, 1200, 480)
MARK_REGION = (60, 100, 480, 520)
MIN_INK_PIXELS = 2000
MIN_MARK_PIXELS = 40000


def token(root, name):
    for c in yaml.safe_load((root / "data/tokens.yaml").read_text())["colors"]:
        if c["name"] == name:
            rgb = Color(c["light"]).convert("srgb").fit("srgb")
            return tuple(round(v * 255) for v in rgb.coords())
    sys.exit(f"social-png: token {name} not found")


def near(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def count(img, box, pred):
    x0, y0, x1, y1 = box
    px = img.load()
    return sum(1 for x in range(x0, x1) for y in range(y0, y1) if pred(px[x, y][:3]))


def main():
    site, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    png, svg = site / "social.png", site / "social.svg"
    if not png.is_file():
        sys.exit("social-png: FAIL the site package serves no social.png")
    if png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("social-png: FAIL social.png is not a PNG")
    img = Image.open(png).convert("RGBA")
    size = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', svg.read_text())
    want = tuple(int(v) for v in size.groups())
    if img.size != want:
        sys.exit(f"social-png: FAIL social.png is {img.size}, its source declares {want}")

    errors = []
    ground, ink = token(root, "ground"), token(root, "ink")
    for corner in ((0, 0), (img.width - 1, 0), (0, img.height - 1), (img.width - 1, img.height - 1)):
        got = img.getpixel(corner)
        if got[3] != 255 or not near(got[:3], ground, 2):
            errors.append(f"corner {corner} is {got}, expected the ground {ground}, opaque")

    inked = count(img, TEXT_REGION, lambda p: near(p, ink, 24))
    if inked < MIN_INK_PIXELS:
        errors.append(
            f"only {inked} ink pixels where the name is drawn; the text did not render, "
            f"which is what resvg does when the face is missing"
        )
    marked = count(img, MARK_REGION, lambda p: not near(p, ground, 6))
    if marked < MIN_MARK_PIXELS:
        errors.append(f"only {marked} non-ground pixels where the mark is drawn")

    if errors:
        for e in errors:
            print(f"social-png: FAIL {e}", file=sys.stderr)
        return 1
    print(
        f"social-png: ok, {img.size[0]}x{img.size[1]} on the ground colour, "
        f"{inked} ink pixels of text, {marked} pixels of mark"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
