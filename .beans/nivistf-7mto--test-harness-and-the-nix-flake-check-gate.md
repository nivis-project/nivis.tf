---
# nivistf-7mto
title: Test harness and the nix flake check gate
status: completed
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T15:12:57Z
parent: nivistf-cpt6
blocked_by:
    - nivistf-gwla
openspec-link: openspec/changes/archive/2026-10-06-test-harness-completion
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

## Summary of Changes

Shipped as OpenSpec change `test-harness-completion`, capability `quality-gate`.

The check set was built incrementally, each check arriving with the work it
guards, which turned out better than building it all up front: a check written
before there is anything to check is a guess about what will break. Two never
arrived, and this closes them.

`html` runs the Nu validator, the same engine the W3C service uses, over every
generated HTML and SVG document. Writing an approximation would have meant
encoding a subset of the HTML specification into a grep and trusting it. It
justified the choice immediately by finding two defects neither a grep nor a
reviewer would have looked for: the generated favicon and social image were
invalid standalone SVG files. They inherit markup from the mark partial, which
emits INLINE svg; a standalone .svg file requires an xmlns, rejects aria-hidden
on its root, and takes its accessible name from a `<title>` child. Browsers load
SVGs leniently enough that nothing looked broken, so both would have shipped.

`links` is split, and says so in its own output. The sandbox has no network, so
the gated half checks what is verifiable offline: every external address is
absolute, uses https, and points at a host in an explicit allowlist, which
catches a typo in a repository name or a docs path. Resolution is
`nix run .#check-links-live`, a separate lychee app for before a release. A
sandboxed check that implied it had resolved a URL would be exactly the kind of
green tick this project has repeatedly had to correct.

The documentation was also wrong and is now right. docs/TESTING.md had been
listing `html`, `links`, `e2e` and `a11y` as planned while `e2e` had shipped and
`a11y` runs inside it. A testing document that misdescribes the gate is worse
than none, because it is what somebody consults to decide whether a concern is
already covered.

The most useful thing recorded here is the pattern four separate defects shared:
each component correct in its own context and wrong once composed. The CSS
cascade on code blocks, the `hidden` attribute beaten by an author `display`,
the oklch serialisation in a test helper, and the inline-versus-standalone SVG.
None was caught by reading source; every one was caught by running the real
artifact through a real tool.
