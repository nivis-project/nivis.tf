---
# nivistf-c6h5
title: Accessibility and responsive conformance
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:45:52Z
parent: nivistf-wrli
blocked_by:
    - nivistf-arln
    - nivistf-30a3
    - nivistf-8b4w
    - nivistf-3s3n
    - nivistf-6wvw
openspec-link: openspec/changes/archive/2026-10-06-a11y-responsive
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

## Summary of Changes

Shipped as OpenSpec change `a11y-responsive`, capability `accessibility`.

A real browser now runs against the built site inside the sandbox: 14 tests
covering layout at three widths, the keyboard path, the theme's observable
behaviour, reduced motion, and axe-core in both palettes. Browsers come from
nixpkgs; axe-core is a fixed-output derivation with a pinned hash, the same way
nixpkgs fetches every other source.

The suite justified itself on its first run by finding three defects that all
seventeen static checks had passed. Two were shipped bugs.

1. Code blocks had NO background. `figure.code .chroma { background: transparent }`
   outranks `figure.code pre { background: var(--code-bg) }` on specificity,
   (0,2,1) against (0,1,2), and `.chroma` IS the `<pre>`. All seven samples
   rendered on the page background at 1.14:1, effectively unreadable. I
   introduced it in the syntax-highlighting change. Every individual rule was
   correct; the cascade was not, which is why no static check could see it.

2. The theme button was visible without JavaScript. An author `display: flex`
   overrides the `hidden` attribute's UA `display: none`. The `theming` check
   confirmed the attribute was present and stopped there, so the site shipped
   exactly the failure that check's spec requirement forbids.

3. A test of mine passed for the wrong reason. Chromium serialises `oklch()` in
   computed style as `oklch()`, not `rgb()`. The helper deciding "is this
   palette dark" averaged the numbers in the string, so oklch(0.975 0.008 275)
   averaged to about 92 and read as dark. The "follows the system" test was
   green while asserting nothing. It now compares the resolved `--ground`
   against the token values exactly.

The third is the one worth remembering: it was only exposed because a different
test failed and made me look at the helper they shared.

Contrast is computed from the tokens, not eyeballed: OKLCH to Oklab to linear
sRGB to relative luminance per CSS Color 4, with the conversion validated
against known values because a wrong conversion would shift every ratio and
still look like a passing test. 18 pairings in both palettes, computed
separately, because a dark-only regression is what a light-only check misses.

The `--warm` rule moved to where it is actually broken. The first version
asserted warm fails contrast in both palettes; that was wrong, in dark it is
about 10:1. The briefing's "insufficient contrast" is about light, where it is
1.76:1. `warm-is-a-fill` greps the stylesheet, and `contrast` reports the light
ratio as a note so the number motivating the rule stays visible.
