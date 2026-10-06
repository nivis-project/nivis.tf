---
# nivistf-gxj4
title: CSS pipeline through Hugo Pipes
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:12:02Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-w84z
openspec-link: openspec/changes/archive/2026-10-06-css-pipeline
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

## Summary of Changes

Shipped as OpenSpec change `css-pipeline`, capability `asset-pipeline`.

The page loads one stylesheet: tokens, base, layout, components and syntax
concatenated, minified and fingerprinted, with an SRI hash. Development builds
skip minification and fingerprinting, because a fingerprinted file and live
reload fight over the cache.

Fonts depart from the briefing's letter, deliberately and recorded in README.md
so the maintainer can overrule it. The briefing says to self-host in
`static/fonts/`, which reads as committing the woff2 files. Both typefaces are
already in nixpkgs as TrueType, so the build converts the six needed weights
with `woff2_compress`. No binaries in the repository, licences tracked by
nixpkgs, reproducible and offline. The cost: `hugo server` outside `nix develop`
falls back to the system face. Hind Regular is 272 KB TrueType and 97 KB woff2;
the six faces total 480 KB.

Font staging is one shared `stageSrc` preamble used by every site-building
check. Scattering the copy across five checks is how one of them quietly ends
up testing a fontless page.

Two defects in my own checks, both found by aiming them at the real artifact:

- `tokens` had been reading a standalone tokens.css. Once the bundle absorbed
  it, pointing the check at the shipped MINIFIED bundle exposed a second bug in
  the checker: minification drops the final semicolon before `}`, and the
  declaration regex required one, so it was silently missing the last token of
  every rule set. `--mark-core` dark was invisible to it. All four token probes
  were then re-proven against the minified bundle.
- `css-colors` flagged `white-space: pre` as the colour white. A check that
  rejects correct CSS is a check somebody disables, so named colours now only
  count as values: after a colon, not part of a longer identifier. Re-probed
  both ways.

`assets` asserts one fingerprinted stylesheet with integrity, exactly the six
font faces the design uses and no others, every face declaring `font-display:
swap`, and no external request. Five probes: a CDN stylesheet, a CDN script, a
protocol-relative URL, a `url()` in CSS and a dead preload. An anchor link is
deliberately not flagged, because a link to GitHub is the page doing its job
while a stylesheet from GitHub is the defect.

Per-section rules are deliberately absent. Writing CSS for markup that does not
exist is how dead rules are born; they arrive with their sections.
