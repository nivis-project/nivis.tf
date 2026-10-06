---
# nivistf-0ro9
title: Layout skeleton and data-driven section dispatch
status: todo
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:40Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-gwla
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
