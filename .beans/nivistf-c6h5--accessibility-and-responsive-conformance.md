---
# nivistf-c6h5
title: Accessibility and responsive conformance
status: todo
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-wrli
blocked_by:
    - nivistf-arln
    - nivistf-30a3
    - nivistf-8b4w
    - nivistf-3s3n
    - nivistf-6wvw
---

Prove the quality bar end to end rather than asserting it.

## Scope

- Semantic HTML: one h1, every section labelled by its heading, `nav` labelled,
  lists as lists, the table as a real table.
- Text contrast at least 4.5:1 in both themes, 3:1 for text 24px and larger.
  Compute it from the tokens, so a token change fails the test.
- `--warm` is never a text color on `--ground` or `--surface`.
- Usable with the keyboard alone: skip link, focus order, visible focus.
- No horizontal page scroll from 360px upward. Only code blocks and the table
  scroll, inside their own boxes.
- `prefers-reduced-motion` turns smooth scrolling off.

## Done when

- [ ] axe-core reports zero violations in both themes
- [ ] A contrast test runs over the token pairs, not over screenshots
- [ ] An e2e test walks the page with the keyboard and reaches every control
- [ ] An e2e test at 360px, 768px and 1440px asserts `scrollWidth` equals
      `clientWidth` on the document

## Briefing

Sections 6 and 10.
