---
# nivistf-zmev
title: Nix flake, dev shell and supported systems
status: todo
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T13:02:11Z
parent: nivistf-cpt6
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
