# Testing

Thorough testing is a requirement of this project, not a nice-to-have. A change
that renders something and has no test proving it renders correctly is not
finished.

Everything runs offline inside the Nix sandbox. `nix flake check` is the gate,
and `scripts/ship-change.sh` refuses to archive a change that does not pass it.

## The check set

Each check is its own `checks.<system>.<name>` in `flake.nix`, so a failure
names the thing that broke rather than reporting "the tests failed".

| Check | Owns | Status |
|------------------------------|---------------------------------------------------|---------|
| `hugo-version-pin`           | nixpkgs Hugo matches `.hugo-version`              | present |
| `hugo-extended`              | the pinned Hugo is the extended build             | present |
| `hugo-math`                  | `math.Cos` / `math.Sin` / `math.Pi` compute the mark curve correctly | present |
| `hugo-version-single-source` | the version number appears only in `.hugo-version` | present |
| `build`                      | the site builds with no Hugo warnings             | present |
| `unit`                       | Hugo template assertions over fixture sites       | present |
| `tokens`                     | the generated token stylesheet matches the briefing and the two dark rule sets agree | present |
| `css-colors`                 | no color value outside `assets/css/tokens.css`    | present |
| `invariants`                 | the content / style / template separation rules   | planned |
| `html`                       | the generated HTML is valid and semantic          | planned |
| `links`                      | every external link resolves                      | planned |
| `e2e`                        | Playwright against the built `public/`            | planned |
| `a11y`                       | axe-core over the built page in both themes       | planned |

"planned" means the epic that owns it has not shipped yet. Milestone 01, epic
`nivistf-7mto`, builds the harness and wires the remaining checks. Milestone 02,
epic `nivistf-rs19`, fills in `invariants`.

### What each present check guards, and how it was proven to bite

A check nobody has seen fail is a check nobody has tested. Each of these was
run against a deliberate violation before being trusted.

| Check | Proven by |
|------------------------------|------------------------------------------------|
| `hugo-version-pin`           | caught a real drift during bootstrap, where `.hugo-version` recorded 0.163.3 and nixpkgs had moved on |
| `hugo-extended`              | a stub `hugo` on `PATH` reporting a non-extended version string |
| `hugo-math`                  | overriding `EXPECTED_PATH_DATA` to a wrong value |
| `hugo-version-single-source` | a fixture tree with the version copied into a second file |
| `build`                      | restoring the deprecated `languageCode` key, which makes Hugo warn |
| `unit`                       | three separate probes, see below               |
| `tokens`                     | four probes: disagreeing dark rule sets, a drifted light value, a redundant override, a missing token |
| `css-colors`                 | a permanent negative fixture, plus blinding the scan's own pattern |

### Checks that test themselves

`css-colors` carries its own negative fixture at `tests/fixtures/stray-color/`,
which contains a color in each of the five notations the rule forbids. The check
asserts the fixture **is** caught before reporting the real tree clean, and
asserts that the fixture's own `tokens.css` is **not** flagged, because an
exemption that does not work is a rule that blocks legitimate work.

That self-test was itself proven: blinding the scan's pattern makes the check
report "the scan has a hole" rather than passing silently. A scan that has never
fired is a scan nobody has tested.

### The fixture harness

A fixture is a miniature Hugo site under `tests/fixtures/<name>/` that mounts the
project's **real** `layouts/` and `i18n/`, and supplies only its own content.
What is tested is therefore what Hugo actually does with the real templates.
Template logic errors (a wrong range variable, a missing `with`) only ever show
up in output, which is why these build a site rather than parse a template.

Mount order matters: a fixture's own `layouts` mount must come first so it can
override one template, with the project's layouts behind it for everything else.

| Fixture | Proves |
|-------------------|--------------------------------------------------------|
| `reorder`         | section order follows content, a repeated section renders twice, an absent one does not render |
| `code`            | a rendered code block equals its source file exactly, highlighted with CSS classes and no inline styles |
| `unknown-section` | a section named in content with no template fails the build, naming the section |
| `missing-snippet` | a referenced snippet that does not exist fails the build, naming the snippet |

The last two are negative fixtures: the check asserts they **fail**. A check
that only ever sees passing input is a check that has never been tested.

`unit` was proven to bite three ways: reordering the `reorder` fixture's list,
making `code.html` lossy so the rendered text no longer matches its source, and
making the `unknown-section` fixture resolvable so its build stops failing.

A regression worth recording: when `head.html` started generating the tokens
stylesheet, the fixtures did not mount `assets/` or `data/`, so every fixture
failed on a nil resource. The two negative fixtures still "failed", which is
what they are supposed to do, but for the wrong reason. The check caught it only
because it asserts on the failure **message**, not just on the exit code. A
negative test that checks only "did it fail" will happily pass while testing
nothing.

One probe was rejected as too weak: editing the snippet file itself does not
trip the byte-for-byte assertion, because both sides of the comparison move
together. That is correct behaviour for a faithfulness test, but it means the
probe proves nothing. Corrupting the renderer is the probe that counts.

`hugo-math` renders one point of the mark curve and compares it to a literal.
The expected value matches the generator in `nivis-mockup-reference.html` to the
decimal: `M92.4 0.0L92.2 4.8L91.5 9.6L90.4 14.3L88.8 18.9L86.9 23.3`. Comparing
against a value rather than "it rendered" also catches a Hugo whose float
formatting changes, which would silently alter every path in every mark.

Keep this table current. It is the one place that says what is actually
guarded.

## Running one check

```bash
nix flake check                        # everything
nix build .#checks.x86_64-linux.e2e    # one check, with its log
nix develop                            # the tools, to iterate by hand
```

## The separation invariants

These are the executable form of the one hard architectural rule. Each is a
grep over the source tree or over the generated HTML, and each has a negative
fixture under `tests/fixtures/` that proves the check actually bites. A check
with no negative fixture is not finished: a grep with a typo in its pattern
passes silently forever.

1. No literal English copy in `layouts/`.
2. No `style=""` attribute anywhere in the generated HTML.
3. No color, font or size value in `content/`, `data/` or `snippets/`.
4. No color value in any CSS file outside `assets/css/tokens.css`.
5. No `<script>` in the output except the theme switch and its inline no-flash
   preamble.
6. Every snippet referenced from `data/` exists in `snippets/`, and every file
   in `snippets/` is referenced.

### The copy-scan allowlist

Check 1 cannot be a blanket ban on word characters: templates legitimately
contain HTML tag names, attribute names, Go template identifiers and class
names. The scan therefore works on text nodes and on the values of
human-readable attributes (`alt`, `title`, `aria-label`, `placeholder`), and
allows only what this list names. Keep the list short; every entry is a hole in
the rule.

| Allowed | Why |
|---------|-----|
| (empty) | Nothing is allowed yet. Add a row with a reason, or move the string to `data/` or `i18n/en.yaml`. |

## Playwright

Browsers come from nixpkgs through `PLAYWRIGHT_BROWSERS_PATH`, which the dev
shell sets. They are never downloaded at test time, because the sandbox has no
network and a downloaded browser is not reproducible.

The end-to-end suite runs against the built `public/` served by a static file
server, not against `hugo server`. The dev server rewrites things the real
deployment does not.

## The link check

`nix flake check` has no network, so `links` runs in two forms:

- in the sandbox, against a recorded allowlist of the URLs the site is allowed
  to contain, which catches a typo in a `docs:` key or a stale repo name;
- outside the sandbox, as a separate target that actually resolves every URL.
  Run it before a release, not on every change.

## There is no coverage floor

Other Nivis repos gate on a line coverage percentage. A Hugo site has no
meaningful line coverage, so the gate here is the full check set above plus the
acceptance checklist in section 11 of `nivis-tf-hugo-briefing.md`.

## Performance budget

Record the cold-load transferred bytes here once milestone 05 lands, so a
regression is visible in a diff rather than in a Lighthouse run nobody opened.

| Metric | Budget | Measured |
|-------------------------|--------|----------|
| Cold load, transferred  | TBD    | not yet  |
| Lighthouse performance  | >= 95  | not yet  |
| Lighthouse a11y         | >= 95  | not yet  |
| Lighthouse best practices | >= 95 | not yet  |
