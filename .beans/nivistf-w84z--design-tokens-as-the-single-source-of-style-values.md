---
# nivistf-w84z
title: Design tokens as the single source of style values
status: in-progress
type: epic
priority: high
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:46:45Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-gwla
---

One file holds every color, font size and spacing value in the project. Nothing
else may contain one.

## Scope

- `assets/css/tokens.css` with the full token table from the briefing.
- Light values on bare `:root`.
- Dark values under both `:root[data-theme="dark"]` and
  `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`.
- The two dark rule sets come from a single list, so they cannot drift. Use a
  Hugo-templated CSS file with the list in `data/`, or an equivalent that keeps
  one source.
- Spacing tokens for the 16 / 24 / 32 / 40 / 48px gaps, the radii and the
  section padding, so `layout.css` carries no bare pixel values either.

## Done when

- [ ] Every token in the briefing's table exists with the stated value
- [ ] Flipping `data-theme` on `<html>` swaps the whole palette
- [ ] A test proves the two dark rule sets resolve to identical values
- [ ] No `oklch(`, no `#` hex and no `px` literal appears in any CSS file
      other than `tokens.css`

## Briefing

Section 5.
