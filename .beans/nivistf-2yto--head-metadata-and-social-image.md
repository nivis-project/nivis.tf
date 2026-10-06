---
# nivistf-2yto
title: Head metadata and social image
status: completed
type: epic
priority: low
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:51:16Z
parent: nivistf-wrli
blocked_by:
    - nivistf-0ro9
openspec-link: openspec/changes/archive/2026-10-06-head-metadata
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

## Summary of Changes

Shipped as OpenSpec change `head-metadata`, capability `page-metadata`.

The page declares a canonical address and carries Open Graph and card metadata,
all reading the SAME title and description the page itself uses. A second copy
is how a preview ends up contradicting the page it previews, so the check
asserts they agree rather than asserting each is non-empty.

The preview image is an SVG generated from the same mark partial as the favicon,
with the token colours inlined, so recolouring the tokens moves it too.

That choice has a real cost, recorded in README.md as a maintainer decision:
several platforms will not render an SVG preview and will show no image. The
alternatives were worse. Rasterising needs a new build dependency and a new
failure mode for something nobody asked to be perfect. A hand-exported PNG would
break the rule that recolouring the tokens moves everything, and would be the
one asset that silently stayed behind when the mark changed, which is exactly
the failure the favicon work was designed to avoid.

Seven probes caught: a missing tag, a relative image address, a drifted title,
an empty tag, a placeholder value, a missing image file, and an unresolved
custom property in the standalone SVG.

Adding the canonical link exposed an over-broad rule in `no-external`: it
treated every `<link href>` as a resource load, so `rel="canonical"` tripped it.
A canonical link is metadata, not a fetch, and as written the rule was
impossible to satisfy for any site with an absolute canonical address. It now
distinguishes by `rel`, and was re-probed in both directions: five real external
fetches still caught, two metadata links correctly ignored.

That is the second over-broad rule in this project (the first read
`white-space: pre` as the colour white). Both times the fix was to make the rule
match what it means rather than what is easy to grep for.
