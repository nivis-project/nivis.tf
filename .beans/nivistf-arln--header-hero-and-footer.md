---
# nivistf-arln
title: Header, hero and footer
status: todo
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-gxj4
---

## Scope

- Header: 40px mark and wordmark linking to top, four muted nav links, a GitHub
  outline pill with a 1.5px accent border, and a 44px round theme switch
  button. The row wraps on narrow screens. `nav` carries a label from i18n.
- Hero: two columns at `minmax(min(420px, 100%), 1fr)`, 48px gap, vertically
  centred. Left is the mono badge pill, the h1, the lead at max 34em, the warm
  primary button, a text link, and the one line command as a code block. Right
  is the mark at up to 440px.
- Footer: top border, 26px mark with name, license and domain on the left,
  text links on the right.
- A skip link to main content, first in the tab order.

## Done when

- [ ] All copy comes from `data/site.yaml`, `data/home/hero.yaml` and i18n
- [ ] The h1 is the only h1 on the page
- [ ] Buttons and links have visible `:hover` and `:focus-visible` states
- [ ] Touch targets are at least 44px
- [ ] A test asserts the skip link works with the keyboard

## Briefing

Sections 4, 6.1, 6.2 and 6.9.
