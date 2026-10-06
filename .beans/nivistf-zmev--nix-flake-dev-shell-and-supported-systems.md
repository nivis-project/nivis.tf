---
# nivistf-zmev
title: Nix flake, dev shell and supported systems
status: completed
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:38:26Z
parent: nivistf-cpt6
openspec-link: openspec/changes/archive/2026-10-06-nix-flake-dev-shell
---

Plain Nix, no flake-utils. Supported systems are a literal list that the flake
maps over with its own helper.

## Scope

- `flake.nix` with `systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ]`
  and a local `forAllSystems` helper built from `nixpkgs.lib.genAttrs`.
- `packages.<system>.default`: the built site, produced by `hugo --minify`
  into `$out`. Fully offline: no network during the build.
- `devShells.<system>.default`: Hugo extended at the pinned version, plus the
  tools the test harness needs.
- The Hugo version is pinned once and read from one place. `amplify.yml` and
  the dev shell must not be able to drift apart.
- `formatter.<system>` so `nix fmt` works.

## Done when

- [ ] `nix develop -c hugo version` prints the pinned extended version
- [ ] `nix build` produces a `public/` tree in the store with no network access
- [ ] `nix flake check` runs and passes
- [ ] The pinned Hugo version appears in exactly one source file
- [ ] `math.Cos`, `math.Sin` and `math.Pi` are confirmed present in the pinned
      version (the mark generator in milestone 04 needs them)

## Briefing

Sections 2 and 3.

## Summary of Changes

Shipped as OpenSpec change `nix-flake-dev-shell`, capability `build-environment`.

The flake now builds the site, not just a shell. `nix build` renders it offline
into the store; `nix develop -c hugo server` serves it with the pinned Hugo
extended build.

Five checks run under `nix flake check`, each proven to fail against a
deliberate violation before being trusted:

- `hugo-version-pin` caught a real drift on its first run (`.hugo-version` recorded
  0.163.3 and the flake's nixpkgs had moved on).
- `hugo-version-single-source` stops a second copy of the version number from
  appearing, which is how the flake, the dev shell and `amplify.yml` would
  quietly disagree.
- `hugo-extended` fails on a non-extended Hugo.
- `hugo-math` renders one point of the mark curve with `math.Cos`, `math.Sin`
  and `math.Pi` and compares it to a literal. It matches the generator in
  `nivis-mockup-reference.html` to the decimal, so milestone 04 has no surprise
  waiting in it.
- `build` fails on any Hugo warning, not just a non-zero exit. Hugo exits 0 on
  a deprecation, so the warnings themselves had to become the failure
  condition. Two real warnings were fixed to get there: the deprecated
  `languageCode` key, and a missing taxonomy layout.

Two things found while implementing:

- Hugo writes `.hugo_build.lock` next to its source, which fails in the
  read-only Nix store. Both the build check and the site package copy the
  source to a writable directory first.
- Supported systems are a literal list mapped by a local `forAllSystems` built
  from `nixpkgs.lib.genAttrs`. No flake-utils, directly or transitively.
