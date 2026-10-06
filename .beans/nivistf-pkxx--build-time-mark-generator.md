---
# nivistf-pkxx
title: Build-time mark generator
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:02:37Z
parent: nivistf-zxfw
blocked_by:
    - nivistf-0ro9
openspec-link: openspec/changes/archive/2026-10-06-mark-generator
---

Generate the SVG paths at build time in `partials/mark.html` from the
parameters in `data/marks.yaml`. No JavaScript ships, and no path data is
pasted by hand.

## Scope

The curve:

```
r(theta) = a + b * cos(k * theta),  with  b = a * amp / (k^2 + 1)
```

A layer is that curve sampled at 120 points, rotated by `rot` degrees, drawn as
a closed path in a `-100 -100 200 200` viewBox, coordinates to one decimal.

- `partials/mark.html` takes a mark key, a layer set and a size, and returns the
  SVG.
- Fills are CSS custom properties (`--mark-a`, `--mark-b`, `--mark-core`), never
  literal colors, so the single grey original logo remains one edit away.

## Done when

- [ ] A test compares the generated path for `nivis` against an independently
      computed reference, point by point, within rounding tolerance
- [ ] Changing `amp` in `marks.yaml` changes the path
- [ ] No `<script>` is involved and no path literal appears in any template

## Briefing

Section 7. The generator in `nivis-mockup-reference.html` is the reference
implementation to check against, not code to copy.

## Summary of Changes

Shipped as OpenSpec change `mark-generator`, capability `mark`.

`partials/mark.html` generates every mark at build time from `data/marks.yaml`.
Three variants: `full` (five layers), `project` (three), `footer` (three). No
JavaScript ships and no path data is written by hand. Every fill is a custom
property, so the colored mark becomes the original grey logo in one edit.

The layer sets live in the partial, not in the data. The data answers "what
shape is this mark"; the variant answers "how much of it does this spot on the
page show". Those change for different reasons, and mixing them would make
adding a project require a decision about the footer.

`tests/checks/mark.py` reimplements the curve in Python from the briefing's
formula and compares every one of the 120 points of every layer of every mark
against Hugo's output: 9 marks, 31 layers, 3720 points. Reusing anything from
the template would make it circular. Comparison is on the rendered string after
rounding, because that is what ships.

Six probes, all caught: a flipped rotation sign, an off-by-one sample count, a
changed layer radius, a color literal instead of a property, data changed after
rendering, and a mark rendered but absent from the data.

A seventh probe was not caught, by design. The check reads the parameters from
the data file, so editing a parameter moves the expectation with it; only the
formula and the layer sets are pinned. That is deliberate because the
per-project parameters are provisional and the maintainer may replace them. It
is the second probe in this project that proved nothing because it moved both
sides of a comparison, so docs/TESTING.md now names that failure shape.

The favicon is the same partial rendered to a standalone SVG, with the three
mark colors inlined from `data/tokens.yaml` and asserted against it, so
recolouring the tokens moves the favicon too. A hand-exported icon would be the
one mark that silently stayed behind. It does not follow dark mode: an SVG
served as a file cannot read the page's custom properties, and the alternative
is shipping two icons for 16 pixels of browser chrome.

Every destructive probe ran in a copied tree this time, and the real
`data/marks.yaml` was verified untouched afterwards.
