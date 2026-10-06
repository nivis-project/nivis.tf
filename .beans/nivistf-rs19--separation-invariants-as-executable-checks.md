---
# nivistf-rs19
title: Separation invariants as executable checks
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T15:07:02Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-7mto
    - nivistf-0ro9
openspec-link: openspec/changes/archive/2026-10-06-separation-invariants
---

Make the one hard architectural rule a thing the build enforces, not a thing
reviewers remember.

## Scope

Each of these is a test that fails the build:

- No literal English copy in `layouts/`. Scan every template for word
  characters outside Go template actions, HTML tag names, attribute names and
  comments. Maintain an explicit allowlist and keep it short.
- No `style=""` attribute anywhere in the generated HTML.
- No color, font or size value in `content/`, `data/` or `snippets/`.
- No color value in any CSS file outside `tokens.css`.
- No `<script>` in the output except the theme switch and its inline
  no-flash preamble.
- Every snippet referenced from `data/` exists in `snippets/`, and every file
  in `snippets/` is referenced.

## Done when

- [ ] All six checks run under `nix flake check`
- [ ] Each check has a negative fixture proving it actually catches the
      violation
- [ ] The allowlist for the copy scan is documented in `docs/TESTING.md`

## Briefing

Sections 1 and 11.

## Summary of Changes

Shipped as OpenSpec change `separation-invariants`, capability `separation`.

This closed a real gap. Three of the four separation rules had been enforced as
they became relevant (colour values outside tokens.css, style values in content,
snippet references), but the copy-in-templates rule, the half that matters most
to an editor, was never implemented. The site satisfied it; nothing stopped the
next change breaking it.

The scan reads only the two places text reaches a reader: text nodes, and the
values of reader-perceived attributes. A scan that treats every word in a
template as copy rejects `<section class="hero">` and gets switched off within a
week, so it deliberately ignores element names, attribute names, class names and
template logic.

Order matters, and getting it wrong produced two false positives on the first
run:

- Go template actions can contain quotes. `aria-label="{{ i18n "theme_switch" }}"`
  stopped the attribute regex at the inner quote and reported `{{ i18n` as
  hard-coded copy. Actions must be stripped BEFORE attributes are matched.
- Script and style blocks are code, not language. The theme switch's pre-paint
  snippet was read as a sentence.

The style scan runs on the GENERATED HTML rather than on templates, because a
template can compose a style attribute from variables without containing one.

Four probes caught: a hard-coded button label, a hard-coded accessible name, an
inline style in the output, and a blinded fixture. `good.html` is the same
markup written correctly and must NOT be flagged, because a rule with no
counter-example becomes an obstacle.

The allowlist is empty and documented in docs/TESTING.md. Every future entry is
a hole in the rule and needs a reason written beside it.
