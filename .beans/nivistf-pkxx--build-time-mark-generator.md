---
# nivistf-pkxx
title: Build-time mark generator
status: todo
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zxfw
blocked_by:
    - nivistf-0ro9
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
