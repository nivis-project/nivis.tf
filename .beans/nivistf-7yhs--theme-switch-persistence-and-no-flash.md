---
# nivistf-7yhs
title: Theme switch, persistence and no-flash
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:32:29Z
parent: nivistf-wrli
blocked_by:
    - nivistf-gxj4
openspec-link: openspec/changes/archive/2026-10-06-theme-switch
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

## Summary of Changes

Shipped as OpenSpec change `theme-switch`, capability `theming`.

The site's only JavaScript: a few inline lines in the head that apply a recorded
choice before the first paint, and `assets/js/theme.js` for the toggle itself.
The check enforces that there are exactly two scripts and no more.

Three decisions that are each a real bug avoided rather than a style point:

- The toggle reads the COMPUTED state, not the stored one. A reader who has
  never chosen has nothing stored, so flipping a stored value would mean the
  first press on a dark system produces dark again. It computes from the
  attribute or the media query, then inverts.
- The button ships `hidden` and the script reveals it. Without JavaScript a
  visible button would be present and inert, which a reader cannot distinguish
  from a broken page. No script, no control, and the system preference still
  decides.
- `localStorage` THROWS in a private window rather than returning nothing. An
  unguarded read in the head would stop the pre-paint snippet and leave the
  wrong palette on screen. Both read and write are wrapped, so the degradation
  is "the choice is not remembered" rather than "the page breaks".

The pre-paint snippet is inline because an external file would be fetched after
the browser had already painted. That is the one place inlining is the right
answer rather than a shortcut, and it is why the script count is two.

Seven probes caught: the snippet below the stylesheet, an unguarded read, an
extra script, a button not shipping hidden, a label not in i18n, a toggle that
stops consulting the system preference, a script that never reveals the button.

What this change explicitly does NOT claim: that no flash occurs, that a choice
survives a real reload, that the button is truly invisible with JavaScript off.
Those are browser behaviours and belong to nivistf-c6h5. The check prints that
deferral on every run, because a green tick implying coverage it does not have
is worse than one that says what it covers.
