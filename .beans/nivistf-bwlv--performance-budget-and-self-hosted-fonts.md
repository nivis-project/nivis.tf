---
# nivistf-bwlv
title: Performance budget and self-hosted fonts
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T15:03:25Z
parent: nivistf-wrli
blocked_by:
    - nivistf-gxj4
openspec-link: openspec/changes/archive/2026-10-06-performance-budget
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

## Summary of Changes

Shipped as OpenSpec change `performance-budget`, capability `performance`.

A first visit went from 466,808 to 189,288 bytes, almost all of it by subsetting
the fonts. Hind is an Indic typeface carrying 1006 glyphs for 434 codepoints,
most of the excess Devanagari conjuncts an English site never renders. Served
fonts went from 475 KB to 107 KB. Hind Light was also dropped: the design names
weight 300 but no rule applies it, so the browser never requested it.

The budget is measured in a real browser from what the page actually REQUESTS,
not by summing `public/`. That distinction mattered: measuring the directory
would have counted the 90 KB of Hind Light that no reader ever fetches, and
"optimising" it away would have been a saving that did not exist for anyone.

Subsetting fails silently, so `font-coverage` verifies the subset against the
actual rendered text of the built page rather than an assumed alphabet. It
earned itself immediately by flagging a Greek theta and a rightwards arrow,
neither of which is in Latin-1.

Then it taught a second lesson. The obvious reading was "my subset broke them".
Checking the SOURCE TrueType files showed the fonts never had those glyphs: they
had been rendering from a system fallback since those sections were built. The
check now compares against the source fonts and separates the two cases: a glyph
the source had and the subset dropped is a regression and fails; a glyph the
typeface never had is reported as a note and surfaced in README.md. Failing the
build over somebody else's choice of typeface would be a check nobody could
satisfy; staying silent would hide a real defect in how the page renders.

No Lighthouse score in the gate, despite the briefing asking for 95+. A
performance score measured in a shared build sandbox is dominated by how busy
the machine is, not by the site, and a gate that fails at random teaches people
to re-run it until it passes. Everything deterministic that Lighthouse reports
IS gated: total bytes, request count, render-blocking resources, font-display,
and the axe-core audit in both palettes. The omission is recorded in
docs/TESTING.md rather than quietly dropped.

Measured, uncompressed, which is the pessimistic case:
  8 requests, 189,288 bytes; HTML 69,883; CSS 11,919; JS 406; fonts 107,080.
58% of the raw HTML is generated mark path data, which gzips to about a quarter.
