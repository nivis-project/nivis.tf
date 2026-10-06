---
# nivistf-2yto
title: Head metadata and social image
status: todo
type: epic
priority: low
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-wrli
blocked_by:
    - nivistf-0ro9
---

## Scope

- `<head>`: title and description from `content/_index.md`, canonical URL,
  Open Graph and Twitter card tags.
- A generated social image if feasible, built from the mark and the site title
  at build time. If it is not feasible with the pinned Hugo, say so in the
  change's proposal and drop it rather than shipping a hand made PNG.

## Done when

- [ ] A test asserts the canonical URL, the OG tags and the Twitter tags are
      present and non-empty
- [ ] No copy for these tags lives in a template

## Briefing

Section 10.
