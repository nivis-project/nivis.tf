---
# nivistf-7mto
title: Test harness and the nix flake check gate
status: in-progress
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T15:06:53Z
parent: nivistf-cpt6
blocked_by:
    - nivistf-gwla
---

The gate every later change passes through. Build this before there is a site
worth testing, so no change can land untested.

## Scope

Wire each of these as a separate `checks.<system>.<name>` in the flake, so a
failure names the thing that broke:

- `build`: the site builds with no Hugo warnings.
- `invariants`: the separation rules of milestone 02, as greps over the source
  tree and over the generated HTML. Owned by milestone 02, scaffolded here.
- `html`: the generated HTML is valid and semantic.
- `links`: every external link in the generated HTML resolves. Must be
  skippable offline, because `nix flake check` has no network: run it against a
  recorded allowlist in the sandbox and against the live web in a separate
  non-sandboxed target.
- `e2e`: Playwright against the built `public/` served by a static file server.
  Headless Chromium from nixpkgs, never downloaded at test time.
- `a11y`: axe-core over the built page in both themes.
- `unit`: Hugo template assertions, driven by building fixture sites under
  `tests/fixtures/` and asserting on their output.

Write `docs/TESTING.md`: how to run one check, how to add a case, and which
check owns which guarantee.

## Done when

- [ ] `nix flake check` runs all of the above
- [ ] Every check runs offline inside the Nix sandbox
- [ ] A deliberately broken fixture makes exactly one check fail, and the
      message says what broke
- [ ] `docs/TESTING.md` exists and is accurate

## Note on the coverage gate

The shipping gate documented for other Nivis repos is a line coverage
percentage. A Hugo site has no meaningful line coverage. Here the gate is the
full `nix flake check` set above plus the acceptance checklist of milestone 05.
Agree this with the maintainer before the first ship.

## Briefing

Sections 10 and 11.
