---
# nivistf-gwla
title: Hugo site skeleton that builds
status: completed
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:45:32Z
parent: nivistf-cpt6
blocked_by:
    - nivistf-zmev
openspec-link: openspec/changes/archive/2026-10-06-hugo-site-skeleton
---

The smallest Hugo site that builds and serves, so later epics have something to
hang tests on. No copy, no styling beyond what the skeleton needs.

## Scope

- `hugo.yaml` with the site title, base URL `https://nivis.tf/`, language `en`,
  Chroma configured for CSS classes (`noClasses: false`), and `snippets/`
  mounted as an assets directory.
- `content/_index.md` with the front matter from the briefing, including the
  ordered `sections` list.
- `layouts/` with a baseof and a home template that does nothing yet beyond
  rendering the title.
- `i18n/en.yaml` created, even if nearly empty.

## Done when

- [ ] `nix develop -c hugo server` serves a page
- [ ] `hugo --minify` builds into `public/` with zero warnings
- [ ] Hugo's layout directory conventions match the pinned version, not an
      older release

## Briefing

Sections 2 and 3.

## Summary of Changes

Shipped as OpenSpec change `hugo-site-skeleton`, capability `site-structure`.

The page is now assembled from the `sections` list in `content/_index.md`. The
home template ranges over it and dispatches to a partial per type, so
reordering or removing a section is a content edit. A section named with no
template fails the build with a message naming the section, not a template
path: a section silently vanishing is exactly what a content editor would not
notice.

Interface strings (skip link, theme switch label, nav label) live in
`i18n/en.yaml`, separate from page copy in `data/`. Both are outside
`layouts/`, which is what the hard rule requires; the split is about which file
an editor opens when the language changes versus when the message changes.

`partials/code.html` reads a snippet from the mounted `snippets/` directory and
highlights it with Chroma CSS classes. A missing snippet fails the build.

The `unit` check builds four fixture sites against the real layouts and asserts
six things. Each was proven to bite before being trusted: reordering the
fixture's list, making `code.html` lossy, and making the negative fixture
resolvable.

Two things worth recording:

- A probe that looked reasonable proved nothing. Editing the snippet file does
  not trip the byte-for-byte assertion, because both sides of the comparison
  move together. Corrupting the renderer is the probe that counts. Without
  noticing that, an untested assertion would have been recorded as tested.
- Hugo mount precedence is first-wins, so a fixture's own layouts mount has to
  come before the project's for an override to take effect.
