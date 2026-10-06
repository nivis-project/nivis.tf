---
# nivistf-arln
title: Header, hero and footer
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:15:58Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-gxj4
openspec-link: openspec/changes/archive/2026-10-06-header-hero-footer
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

## Summary of Changes

Shipped as OpenSpec change `header-hero-footer`, capability `page-chrome`.

The page now has a real frame: the header with the mark, wordmark, four
navigation links, the outline call to action and the theme switch button; the
hero with badge, heading, lead, primary button, text link, command block and the
440 pixel mark; the footer with the small mark variant, name, licence and
domain. Every string comes from `data/site.yaml`, `data/home/hero.yaml` or
`i18n/en.yaml`.

The theme switch renders but does nothing and is hidden by default. Wiring it,
and unhiding it when JavaScript runs, is nivistf-7yhs.

`page-chrome` catches a class of bug nothing else does: a same-page link to a
section somebody renamed. The address is syntactically fine and never leaves the
site, so no link checker flags it. The check collects every `#target` in the
built page and asserts each resolves.

Four targets do not resolve yet, because four sections are still empty partials.
Rather than switch the check off, it carries an explicit `UNBUILT_SECTIONS`
exemption that FAILS once every section in it resolves, so whoever lands the
last section is told to delete it. The design named that as the risk, so the
escape hatch closes itself.

It also watches heading structure continuously (exactly one h1, no skipped
ranks), which is the kind of thing that degrades one section at a time, and
asserts the chrome's strings really come from the data, probed by pointing the
check at a modified data file and confirming it notices the page disagreeing.

Six probes, all caught: a second h1, a skipped rank, a dangling navigation
target, missing focus rules, a broken skip link, stale chrome.

An honest limit: the check asserts `:focus-visible` and `:hover` rules exist.
Proving a focus ring is visible needs a real browser and belongs to
nivistf-c6h5. Absence is the common failure and worth catching now; visibility
is deferred, not assumed.

One test was found to be coupled to the wrong thing. The `reorder` fixture
asserts section dispatch follows content order, but it observed the real section
partials, so the moment hero.html became real markup it failed for a reason
unrelated to dispatch. The fixture now ships its own stubs, mounted ahead of the
real layouts. Adding `data-section` attributes to production markup so tests
could see the structure would have put test scaffolding into what ships.
