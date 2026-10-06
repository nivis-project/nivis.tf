# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffolding: a plain-Nix flake with a pinned Hugo extended, an
  OpenSpec store, a beans backlog of five milestones and twenty epics, and a
  gated ship script.
- A reproducible site build. `nix build` renders the site offline, and
  `nix develop -c hugo server` serves it with the pinned Hugo.
- The Hugo version is single-sourced in `.hugo-version`. The flake, the dev
  shell and `amplify.yml` all read it, and the gate fails when a second copy
  appears or when nixpkgs drifts away from it.
- The gate proves up front that the pinned Hugo is the extended build and can
  compute the mark curve, so the mark work cannot be blocked by a late
  surprise.
- The page is assembled from an ordered section list in `content/_index.md`.
  Reordering or removing a section is a content edit, and a section named with
  no template fails the build instead of vanishing silently.
- Interface strings live in `i18n/en.yaml`, so a second language needs no
  template change.
- Code samples live in `snippets/` as files in their own language and render
  byte for byte, highlighted with CSS classes.
- Every color, font size and spacing value is a design token. The palette is
  generated from one list, so the light and dark rule sets cannot drift apart,
  and the gate fails if a color appears in any other stylesheet.
- The site's copy and all seven code samples are in `data/` and `snippets/`.
  A reference to a snippet that does not exist, a snippet nothing references,
  and a project whose mark has no parameters all fail the gate.
- Documentation links resolve through a single `docs_base`, so moving the docs
  is a one-line change.
- The mark is generated at build time from the curve in `data/marks.yaml`: the
  full, project and footer variants, plus an SVG favicon from the same partial.
  No JavaScript ships and no path data is written by hand. Every fill is a
  custom property, so the whole family recolours in one edit.
- The site loads one minified, fingerprinted stylesheet with an integrity hash,
  and serves its own fonts. Nothing on the page reaches another host, and the
  gate fails if anything ever does.
- The page has a header, a hero and a footer, all rendered from data. A skip
  link reaches the content, every control shows focus, and a navigation link
  pointing at a section that does not exist fails the gate.
- The audiences and quick start sections render from data. Step numbers follow
  position, so inserting a step renumbers the rest, and adding a card or a step
  needs no template change.
- The round trip band and the comparison table render from data. The table is a
  real table with scoped headers, the highlighted column follows a flag in the
  data, and it scrolls inside its own box so the page never scrolls sideways.
- The projects and go deeper sections render from data. Adding a project to
  `data/home/projects.yaml` and `data/marks.yaml` adds a card with a generated
  mark and no template change, which the gate proves by doing it.
- Code samples are syntax highlighted through CSS classes mapped onto the
  design tokens. Shell prompts are visible but left out of a copied selection,
  so dragging across a sample and pasting gives a runnable command.
- The theme follows your system by default, and the header button overrides it
  and remembers the choice. The chosen palette is applied before the page
  paints, so there is no flash. Without JavaScript the system preference still
  decides and the button is not shown.

- The page declares a canonical address and carries Open Graph and card
  metadata, with a preview image generated from the mark, so a shared link
  shows what the page is.

- The fonts are subset to what the site can actually render, cutting a first
  visit from 467 KB to 189 KB. A weight no rule applied is no longer served.

- The architectural rule is now fully enforced: the gate fails if a template
  gains a word a reader would see, or if any inline style reaches the HTML.

- Every generated document, HTML and SVG alike, is validated against its
  format, and external links are checked for scheme and host. Resolving them is
  a separate `nix run .#check-links-live` before a release.

- The briefing's acceptance checklist runs as part of the gate. Every item
  names the check that proves it, and an item whose check disappears fails, so
  the checklist cannot quietly describe a gate that no longer matches it.

### Fixed

- Eleven checks inspected a build that is never deployed, because they omitted
  the minification the deployment uses. One of them, the link checker, was
  matching nothing at all and would have passed indefinitely while verifying
  nothing. The site itself was unaffected; the defect was in the verification.

- Code samples rendered on the page background instead of their own dark one,
  at a contrast ratio of 1.14 to 1. A transparent-background rule intended for
  Chroma's line wrappers also matched the code block itself and outranked it.
- The theme button was visible and did nothing when JavaScript was unavailable,
  because a layout rule overrode the attribute that should have hidden it.
- The generated favicon and social image were invalid as standalone SVG files:
  they lacked the XML namespace and carried an accessible name in a form a
  document root does not allow.
- The byte-for-byte snippet guarantee covered one example snippet rather than
  all seven, and the deployment configuration was never checked at all.
