---
# nivistf-gwla
title: Hugo site skeleton that builds
status: todo
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:02:40Z
parent: nivistf-cpt6
blocked_by:
    - nivistf-zmev
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
