---
# nivistf-7yhs
title: Theme switch, persistence and no-flash
status: todo
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-wrli
blocked_by:
    - nivistf-gxj4
---

## Scope

- Default follows `prefers-color-scheme`.
- The header button toggles light and dark, sets `data-theme` on `<html>`, and
  stores the choice in `localStorage`.
- A tiny inline script in `<head>` applies the stored choice before first paint.
- Without JavaScript the site still follows the system setting, and the button
  is hidden.
- The button is a real `<button>` with an `aria-label` from `i18n/en.yaml`.
- This is the only JavaScript on the site.

## Done when

- [ ] An e2e test loads the page, toggles, reloads, and finds the choice kept
- [ ] An e2e test with JavaScript disabled finds the system theme applied and
      the button hidden
- [ ] An e2e test asserts no flash: the first painted frame already carries the
      stored theme
- [ ] A test asserts the page ships no other script

## Briefing

Section 8.
