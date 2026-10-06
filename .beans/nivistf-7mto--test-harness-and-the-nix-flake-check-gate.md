---
# nivistf-7mto
title: Test harness and the nix flake check gate
status: completed
type: epic
priority: critical
created_at: 2026-10-06T13:02:11Z
updated_at: 2026-10-06T15:26:48Z
parent: nivistf-cpt6
blocked_by:
    - nivistf-gwla
openspec-link: openspec/changes/archive/2026-10-06-check-the-deployed-artifact
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

## Addendum: the gate was checking an artifact that is never deployed

Shipped as OpenSpec change `check-the-deployed-artifact`, found AFTER the
project was declared finished.

`amplify.yml` deploys with `hugo --minify`. Eleven checks built without it. The
minifier drops quotes around an attribute value containing no space, so
`class="project-card"` became `class=project-card` while
`class="card stack audience-card"` survived. Patterns written against readable
markup matched nothing on the real page.

`links.py` found ZERO external links and would have reported "ok, 0 external
links, all https" on every run forever. It failed only because of one line added
almost as an afterthought:

    if not external:
        errors.append("the page has no external links at all, which cannot be right")

Only `assets` and `acceptance` failed loudly. The rest would have stayed green,
some asserting against zero matched elements.

How it was found: an ad hoc inspection of `nix build` printed `code: 0` and
`table rows: 0`. The easy explanation was a bad regex in the throwaway command.
The byte count had also moved, 69,883 to 57,764. Two unexplained numbers in one
place is a signal, and chasing the second found the first.

Three rules now in docs/TESTING.md:

1. Build what deploys, fixtures included, so there is no convenient dialect for
   tests.
2. Normalise once (`tests/checks/htmlnorm.py`) rather than teaching twenty
   patterns both spellings, where missing one is silent.
3. A check that finds nothing fails. Guards are labelled VACUOUS-PASS GUARD.

This is sharper than the negative-fixture rule I had already written. A negative
fixture proves a check CAN fail; it does not prove the check is LOOKING at
anything, because the fixture and the real artifact can be different dialects.

A fourth, about my own process: applying the normaliser I wrote the affected
list by hand and omitted links.py, the very file whose failure exposed the
problem. The audit is now derived from the checks themselves.
