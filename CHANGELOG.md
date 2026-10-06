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
