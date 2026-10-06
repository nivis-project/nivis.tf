---
# nivistf-pbee
title: Mark variants and favicon
status: todo
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zxfw
blocked_by:
    - nivistf-pkxx
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
