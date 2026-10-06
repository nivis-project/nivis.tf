---
# nivistf-nr5s
title: Site data, i18n and the snippet pipeline
status: todo
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-0ro9
---

The data and snippet files every later section epic reads from. Create them in
one pass so the sections can be built in any order.

## Scope

- `data/site.yaml`, exactly as the briefing gives it.
- `data/home/` with `hero.yaml`, `audiences.yaml`, `quickstart.yaml`,
  `roundtrip.yaml`, `compare.yaml`, `projects.yaml`, `docs.yaml`.
- `data/marks.yaml`.
- `i18n/en.yaml` with the skip link text, the theme switch aria-label, the
  copy button label and the nav label.
- `snippets/` with all seven files, byte for byte as the briefing gives them.
- A `doc:` link resolves to `<docs_base>/<doc>`; an `href:` link is used as is.
  Implement that resolution once, in a partial or a template function.

## Done when

- [ ] A test asserts every rendered code block matches its file in `snippets/`
      byte for byte
- [ ] A test covers both link forms
- [ ] No HTML and no style value appears in any of these files

## Briefing

Section 4.
