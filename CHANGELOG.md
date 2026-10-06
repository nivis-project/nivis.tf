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
