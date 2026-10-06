---
# nivistf-pbee
title: Mark variants and favicon
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T15:10:58Z
parent: nivistf-zxfw
blocked_by:
    - nivistf-pkxx
openspec-link: openspec/changes/archive/2026-10-06-mark-generator
---

## Scope

- Main mark, five layers back to front: a=84 rot -24 mark-a 0.3, a=80 rot -11
  mark-b 0.3, a=78 rot 12 mark-a 0.3, a=74 rot 25 mark-b 0.3, core a=64 rot 0
  mark-core 1. k=3, amp=1.
- Header uses the same five layers at 40px. Footer uses layers 2, 3 and core at
  26px. Hero uses all five, up to 440px wide, with a `role="img"` and the
  `mark_alt` label from `hero.yaml`.
- Project marks have three layers: a=84 at rot-16 (mark-a, 0.35), a=80 at
  rot+16 (mark-b, 0.35), core a=64 at rot.
- An SVG favicon generated from the main mark.
- Decorative marks are `aria-hidden`; the hero mark is labelled.

## Done when

- [ ] All six project marks render and differ from each other
- [ ] The favicon is generated, not hand drawn
- [ ] A test asserts the layer counts and opacities per variant

## Note

The per-project parameters and the colored mark are both provisional. The
maintainer may replace them. Keep every fill a custom property.

## Briefing

Section 7.

## Summary of Changes

Delivered in full by OpenSpec change `mark-generator`
(`openspec/changes/archive/2026-10-06-mark-generator`), proposed against the
sibling epic nivistf-pkxx. Writing the generator and writing its variants turned
out to be one piece of work: a generator with no variants produces nothing the
page can use.

Closed without a separate change rather than manufacturing one. Every scope item
is in the tree and tested:

- the `full` variant's five layers with the briefing's radii, rotations and
  opacities, and the `footer` and `project` variants
- the hero mark labelled from `mark_alt`; every other mark `aria-hidden`
- an SVG favicon generated from the same partial, with the token colours
  inlined and asserted against `data/tokens.yaml`

All three acceptance criteria are covered by `tests/checks/mark.py`, which
compares every one of the 120 points of every layer of all 9 rendered marks
(3720 points) against an independent Python evaluation of the curve, and asserts
the layer count and opacity per variant.

One thing the mark work did NOT get right, found later by the HTML validator in
nivistf-7mto: the favicon is generated from a partial that emits INLINE svg, and
a standalone .svg file needs an xmlns and takes its accessible name from
`<title>` rather than `aria-label`. Browsers load SVGs leniently enough that
nothing looked broken. Fixed in the test-harness change.
