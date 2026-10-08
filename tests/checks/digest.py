#!/usr/bin/env python3
"""The generated images' cache-busting reference tracks what they are built from.

The favicon lives at a fixed path, so it cannot carry a content digest in its
filename the way the bundled stylesheet does, and browsers cache it more
persistently than almost anything else. A query derived from the image's inputs
is the whole mechanism, and it fails silently: when the derivation names a value
the build no longer produces, it goes on resolving to empty and the query holds
one value while the image is redrawn underneath it.

That is not hypothetical. It hashed `.k` and `.amp`, removed when the mark became
a nested series, and colour tokens prefixed "mark-", which moved into the span
when the palette changed. Setting the Nivis ratio from 12 to 9 redrew the favicon
and left the query at 665b42f9.

So every input is perturbed one at a time and the reference must move. The half
that matters as much is the last one: an unchanged rebuild must leave it alone,
or it is a random number rather than a cache key, and every other assertion here
would pass.
"""
import copy
import pathlib
import re
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise

REF = re.compile(r"(?:favicon\.svg|social\.svg)\?v=([0-9a-f]+)")


def build(root, work, tag):
    out = pathlib.Path(work) / tag
    r = subprocess.run(
        ["hugo", "--minify", "--environment", "production",
         "--destination", str(out), "--cacheDir", f"{work}/cache"],
        cwd=root, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None, (r.stdout + r.stderr)[-600:]
    refs = set(REF.findall(normalise((out / "index.html").read_text())))
    if len(refs) != 1:
        return None, f"expected one digest on the page, found {sorted(refs)}"
    return refs.pop(), None


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    marks_p = root / "data" / "marks.yaml"
    tokens_p = root / "data" / "tokens.yaml"
    marks_src, tokens_src = marks_p.read_text(), tokens_p.read_text()
    marks, tokens = yaml.safe_load(marks_src), yaml.safe_load(tokens_src)

    errors = []
    with tempfile.TemporaryDirectory() as work:
        base, err = build(root, work, "base")
        if base is None:
            print(f"digest: FAIL the baseline did not build: {err}", file=sys.stderr)
            return 1

        # Every parameter the Nivis mark resolves to, and every field of the
        # span. These are exactly the inputs the favicon is drawn from.
        #
        # The span's structural fields are left out deliberately. `max_copies`
        # is a bound on what may be asked for, not an input to what is drawn.
        # `ramp_steps` does not change a colour either: a copy selects
        # round(steps * i / (copies - 1)) and its hue is centre +
        # (idx/steps - 0.5) * spread, so the step count cancels and doubling it
        # gives the same hue. Both still enter the digest, because whole maps
        # are hashed; they are not asserted here because they have nothing to
        # assert.
        SPAN_NUDGE = {"hue_centre": 1, "hue_spread": 1, "saturation": 1,
                      "lightness": 1, "opacity": 0.05}
        probes = []
        for key in {**marks["default"], **marks["marks"]["nivis"]}:
            probes.append(("mark", key, None))
        for key, delta in SPAN_NUDGE.items():
            probes.append(("span", key, delta))

        # VACUOUS-PASS GUARD: with nothing to perturb this reports success
        # having proved nothing at all.
        if len(probes) < 8:
            print(f"digest: FAIL only {len(probes)} inputs found to perturb",
                  file=sys.stderr)
            return 1

        try:
            # Nudged to a specific value, not incremented: every one has to stay
            # inside the formula's bounds, or the build fails for a reason that
            # has nothing to do with the digest.
            MARK_NUDGE = {"lobes": 4, "ratio": 11, "copies": 3,
                          "rot": 25, "fit": -0.1}
            for where, key, delta in probes:
                m, t = copy.deepcopy(marks), copy.deepcopy(tokens)
                if where == "mark":
                    m["marks"]["nivis"][key] = MARK_NUDGE[key]
                    marks_p.write_text(yaml.safe_dump(m, sort_keys=False))
                else:
                    t["mark_span"][key] = t["mark_span"][key] + delta
                    tokens_p.write_text(yaml.safe_dump(t, sort_keys=False))

                got, err = build(root, work, "probe")
                marks_p.write_text(marks_src)
                tokens_p.write_text(tokens_src)

                if got is None:
                    errors.append(f"changing {where} {key!r} broke the build: {err}")
                elif got == base:
                    errors.append(
                        f"changing {where} {key!r} left the image reference at "
                        f"{got}, so a reader who has visited before keeps the "
                        f"old image"
                    )

            # A reference that moves on every build is not a cache key.
            again, err = build(root, work, "again")
            if again is None:
                errors.append(f"the unchanged rebuild failed: {err}")
            elif again != base:
                errors.append(
                    f"an unchanged rebuild moved the reference from {base} to "
                    f"{again}, so every visit is a cache miss"
                )
        finally:
            marks_p.write_text(marks_src)
            tokens_p.write_text(tokens_src)

    if errors:
        for e in errors:
            print(f"digest: FAIL {e}", file=sys.stderr)
        return 1

    print(f"digest: ok, {len(probes)} inputs each move the image reference, "
          f"and an unchanged rebuild leaves it at {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
