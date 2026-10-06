---
# nivistf-0ro9
title: Layout skeleton and data-driven section dispatch
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:46:38Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-gwla
openspec-link: openspec/changes/archive/2026-10-06-hugo-site-skeleton
---

The home template loops over the `sections` list in `content/_index.md` and
calls `partials/sections/<type>.html` for each. Reordering or removing a section
is then a content change and nothing else.

## Scope

- `layouts/baseof` and the home template.
- `partials/head.html`, `header.html`, `footer.html`.
- `partials/code.html`: reads a snippet file from the mounted assets directory,
  highlights it with `transform.Highlight`, and renders the optional mono
  filename label above it.
- `partials/sections/` with one empty but valid partial per section type, so
  the dispatch works before the sections have content.
- Every string the templates emit comes from `data/` or `i18n/en.yaml`.

## Done when

- [ ] Reordering `sections` in `content/_index.md` reorders the page, with no
      template change
- [ ] Removing a section from that list removes it from the page
- [ ] An unknown section type fails the build loudly rather than rendering
      nothing

## Briefing

Section 3.

## Summary of Changes

Delivered in full by OpenSpec change `hugo-site-skeleton`
(`openspec/changes/archive/2026-10-06-hugo-site-skeleton`), which was proposed
against the sibling epic nivistf-gwla. The two epics overlapped: writing a Hugo
skeleton that builds and writing the data-driven section dispatch turned out to
be one piece of work, not two, because a skeleton without the dispatch is just
the stub it replaced.

Closed without a separate change rather than manufacturing one. Every scope
item exists in the tree:

- `layouts/baseof.html` and `layouts/home.html`
- `layouts/_partials/head.html`, `header.html`, `footer.html`, `code.html`
- `layouts/_partials/sections/` with all seven section partials
- every template string comes from `i18n/en.yaml` or page front matter

All three acceptance criteria are covered by assertions in the `unit` check,
each proven to fail against a deliberate violation:

- reordering `sections` reorders the page, with no template change
- a section removed from the list does not render
- an unknown section type fails the build, naming the section rather than a
  template path

The one thing deferred: the filename label above a code block renders as a
`<figcaption>`, but its mono styling is a style concern and belongs to
nivistf-gxj4.
