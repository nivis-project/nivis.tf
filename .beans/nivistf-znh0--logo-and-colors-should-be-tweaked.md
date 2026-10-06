---
# nivistf-znh0
title: logo and colors should be tweaked
status: completed
type: task
priority: normal
created_at: 2026-10-06T15:24:50Z
updated_at: 2026-10-06T17:08:08Z
openspec-link: openspec/changes/archive/2026-10-06-mark-nested-copies
---

## Summary of Changes

Shipped as tinychange `teal-blue-ui-palette`, capability `design-tokens`.

Scoped to the UI palette only. The brief also replaces the mark's GEOMETRY, not
just its colours, and that is not a tiny change: the spec encodes
`r(theta) = a + b*cos(k*theta)` with five independently-sized concentric layers,
while the brief specifies nested self-similar copies scaled by
`perfectFit^(1-5f)` derived from sampling 720 angles. The `mark` check that
verifies 3720 points against an independent implementation would be rewritten
with it. That needs its own spec-driven change, as does the animated hero.

The brief's anchors convert to oklch hues 187 (teal), 245 (sky), 270 (deep
blue). oklch rather than the brief's HSL because the pipeline and every contrast
assertion already speak it; the rendered colours are the same. The three mark
tokens are the anchors verbatim; every other token sits inside that hue range.

Text tokens are deliberately NOT the raw anchors, exactly as the brief
anticipates: teal on white is 1.89:1 and sky is 3.59:1. `--ink` and `--muted`
are darkened members of the same family, and all 36 pairings meet WCAG AA in
both palettes.

`--warm` is removed, since the new family has no amber, and `--cta` replaces it.
Its dark value needed solving rather than guessing: the first choice gave
3.95:1 against the button text, so the passing lightness range was computed and
0.54 taken. `warm-is-a-fill.sh` and its flake check are deleted; the rule
existed because amber on a light ground was unreadable, and the new palette
removes the condition rather than the rule.

A new guard rejects any token whose hue falls outside the family, with
near-neutrals exempt because they have no meaningful hue. Probed by
reintroducing the old amber.

One defect found on the way: the e2e suite's palette comparison read its token
values from a hand-copied pair of strings in flake.nix, under a comment claiming
they came from data/tokens.yaml "so there is one source". They did not, and they
drifted the moment the palette changed. `tests/checks/ground-tokens.py` now
actually reads the data file. That is the third hand-maintained copy in this
project to drift from its source.

Not verifiable here: whether the result READS as deliberate. The four syntax
colours now sit inside a 90 degree hue range instead of across the wheel,
because the brief asks for code colours from the blue family. They are pushed as
far apart as the family allows, but they are closer together than the set they
replace. Worth a human eye.
