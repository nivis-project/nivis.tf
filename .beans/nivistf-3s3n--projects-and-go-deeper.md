---
# nivistf-3s3n
title: Projects and go deeper
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:26:25Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-pbee
openspec-link: openspec/changes/archive/2026-10-06-projects-docs
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

## Summary of Changes

Shipped as OpenSpec change `projects-docs`, capability `page-sections`
(modified). All seven sections now render.

The briefing's acceptance criterion is executed, not paraphrased.
`tests/checks/acceptance.sh` really adds a project to a copy of the data, really
rebuilds, and then diffs `layouts/` and `assets/` to prove neither changed. The
diff is the load-bearing part: without it the test could pass while somebody had
quietly added a special case to the template for the new project, which is
exactly the failure the criterion exists to prevent. Probed with a template
rendering only the first six items, a hard-coded destination and a non-generated
mark.

A new assertion found a real accessibility gap in work already shipped:
requiring every section to be labelled by its own heading failed immediately on
the hero, which had no accessible name at all. A reader listing the page's
regions would have seen an unnamed one. Fixed by labelling it from the h1.

The `UNBUILT_SECTIONS` exemption is deleted rather than emptied. All six
same-page links now resolve unconditionally. An empty exemption set reads like a
disabled guard and invites somebody to put an entry back in it.

Five more probes caught: a nested link, two links in one card, an unlabelled
section, a label pointing at a missing id, a dropped documentation link.

Each project card is one link, not a card with a link on the title and another
on the mark, which would read as one thing visually and as three to a keyboard.
