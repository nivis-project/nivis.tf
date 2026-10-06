---
# nivistf-w84z
title: Design tokens as the single source of style values
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:52:11Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-gwla
openspec-link: openspec/changes/archive/2026-10-06-design-tokens
---

One file holds every color, font size and spacing value in the project. Nothing
else may contain one.

## Scope

- `assets/css/tokens.css` with the full token table from the briefing.
- Light values on bare `:root`.
- Dark values under both `:root[data-theme="dark"]` and
  `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`.
- The two dark rule sets come from a single list, so they cannot drift. Use a
  Hugo-templated CSS file with the list in `data/`, or an equivalent that keeps
  one source.
- Spacing tokens for the 16 / 24 / 32 / 40 / 48px gaps, the radii and the
  section padding, so `layout.css` carries no bare pixel values either.

## Done when

- [ ] Every token in the briefing's table exists with the stated value
- [ ] Flipping `data-theme` on `<html>` swaps the whole palette
- [ ] A test proves the two dark rule sets resolve to identical values
- [ ] No `oklch(`, no `#` hex and no `px` literal appears in any CSS file
      other than `tokens.css`

## Briefing

Section 5.

## Summary of Changes

Shipped as OpenSpec change `design-tokens`, capability `design-tokens`.

`data/tokens.yaml` is the single source: 24 colors from the briefing's table,
the full type scale and the shape and space values. `assets/css/tokens.css` is a
Hugo-templated asset that renders three rule sets from that one list, so the
explicit-dark and system-dark sets are identical by construction rather than by
review. 66 tokens, 13 dark overrides.

The briefing warned that the two dark rule sets must not drift. Hand-writing
them and relying on review is the thing it warned against, and no test can
enforce it: a checker comparing two hand-written blocks goes out of date exactly
as easily as the blocks do. Generating both from one list removes the
possibility instead of policing it.

Two checks, each proven to bite:

- `tokens` parses the GENERATED stylesheet, not the template. Reading the
  template would only restate that it has one loop in it; parsing the output
  catches a Hugo change, a minifier, or a later edit that splits the loop. Four
  probes: disagreeing dark rule sets, a light value drifted from the briefing,
  a redundant dark override, and a missing token.
- `css-colors` rejects a color in any notation outside tokens.css. Probed with
  hex, rgb(), hsl(), oklch() and a named color. It carries a permanent negative
  fixture and asserts the fixture is caught before reporting the tree clean, so
  blinding its own pattern makes it report a hole rather than pass.

Three things found while implementing:

- `site.Data` is deprecated in Hugo 0.156 and later. The build check caught it,
  because it treats warnings as failures.
- `$` inside `{{ with }}` refers to the page, not the loop item, which silently
  emptied the dark rule sets until Hugo errored on the field access.
- Adding the stylesheet to head.html broke every fixture, which did not mount
  `assets/` or `data/`. The two negative fixtures still failed, as they are
  meant to, but for the wrong reason. Only the assertion on the failure
  MESSAGE caught it. A negative test that checks just "did it fail" passes
  happily while testing nothing.

Deferred by design: bundling, minifying and fingerprinting belong to
nivistf-gxj4, and contrast verification to nivistf-c6h5. The spec records that
--warm is a fill and never text on ground or surface, so that rule survives the
gap between here and the accessibility work.
