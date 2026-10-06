---
# nivistf-bwlv
title: Performance budget and self-hosted fonts
status: in-progress
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:51:09Z
parent: nivistf-wrli
blocked_by:
    - nivistf-gxj4
---

## Scope

- Lighthouse 95 or above for performance, accessibility and best practices,
  measured in CI against the built site.
- CSS bundled, minified and fingerprinted. No unused rules.
- Fonts woff2, `font-display: swap`, the two most used weights preloaded.
- No external request at runtime, asserted by a test rather than by reading.

## Done when

- [ ] A Lighthouse run is part of the check set, with the thresholds as the
      pass condition
- [ ] The total transferred bytes for a cold load are recorded in
      `docs/TESTING.md`, so a regression is visible

## Briefing

Section 10.
