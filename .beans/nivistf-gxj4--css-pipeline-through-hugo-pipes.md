---
# nivistf-gxj4
title: CSS pipeline through Hugo Pipes
status: in-progress
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:02:37Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-w84z
---

CSS reaches the browser as one bundled, minified, fingerprinted file through
Hugo Pipes. No framework, no external build step.

## Scope

- `assets/css/` split into `tokens.css`, `base.css`, `layout.css`,
  `components.css`, `syntax.css`.
- `partials/head.html` concatenates, minifies and fingerprints them, and emits
  an integrity attribute.
- Fonts self-hosted as woff2 under `static/fonts/`, `font-display: swap`, the
  two most used weights preloaded. No request leaves the page at runtime.

## Done when

- [ ] The built page loads exactly one stylesheet, fingerprinted
- [ ] A test asserts the generated HTML makes no request to any external host
- [ ] Hind and IBM Plex Mono render from local files with the system fallback
      stacks the briefing names

## Briefing

Sections 2, 5 and 10.
