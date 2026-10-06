---
# nivistf-3s3n
title: Projects and go deeper
status: todo
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-pbee
---

## Scope

- Projects at `id="projects"`, on `--surface`: h2 and lead, then a grid of
  cards at `minmax(min(320px, 100%), 1fr)` on `--ground`. Each whole card is
  one link to `<github_org>/<name>`, containing a 64px mark variant, the mono
  repo name, a small outlined status pill and a muted description.
- Go deeper: two columns. Left is h2, text and the warm primary button. Right
  is a two-column list of doc links, each with a top divider.

## Done when

- [ ] Adding an entry to `projects.yaml` and `marks.yaml` adds a card with a
      generated mark, with no template change
- [ ] The card is one link, not nested links
- [ ] Doc links resolve through `docs_base`, and the Demos link uses its
      literal `href`

## Briefing

Sections 4, 6.7 and 6.8. Depends on the mark generator in milestone 04.
