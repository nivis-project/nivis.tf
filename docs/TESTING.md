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
| `snippets`                   | snippets and their references agree both ways; no markup or style values in content | present |
| `snippets-unformatted`       | the formatter never rewrites approved copy        | present |
| `mark`                       | every generated mark matches an independent evaluation of the curve | present |
| `assets`                     | one fingerprinted stylesheet, the right font set, nothing external | present |
| `page-chrome`                | heading structure, same-page link targets, chrome strings from data | present |
| `sections`                   | the page agrees with the data, section by section  | present |
| `acceptance`                 | the briefing's add-a-project criterion, replayed literally | present |
| `syntax`                     | highlighting resolves to tokens, prompt not copyable, no wrapping | present |
| `theming`                    | the theme mechanism: pre-paint ordering, one script, guarded storage | present |
| `contrast`                   | every pairing meets its minimum, computed from the tokens | present |
| `warm-is-a-fill`             | `--warm` is never used as a text colour          | present |
| `e2e`                        | a real browser: layout, keyboard, theme, motion, axe-core | present |
| `metadata`                   | sharing metadata agrees with the page and is absolute | present |
| `font-coverage`              | every rendered character exists in the served fonts | present |
| `separation`                 | no copy in templates, no inline style in the output | present |
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
| `snippets`                   | five probes: a dangling reference, an orphan file, an HTML tag, a color value, an unresolvable mark |
| `snippets-unformatted`       | running the formatter without its exclusion, which really did rewrite a snippet |
| `mark`                       | six probes: flipped rotation, off-by-one sample count, changed radius, colour literal, data changed after render, undeclared mark |
| `assets`                     | five probes: a CDN stylesheet, a CDN script, a protocol-relative URL, a `url()` in CSS, a dead preload |
| `page-chrome`                | six probes: a second h1, a skipped rank, a dangling nav target, missing focus rules, a broken skip link, stale chrome |
| `sections`                   | seventeen probes, including a div pretending to be a table, a moved highlight, a stray `overflow-x`, a hard-coded subject column, a nested link, an unlabelled section |
| `acceptance`                 | three probes: a template rendering only the first six items, a hard-coded destination, a non-generated mark |
| `syntax`                     | six probes: a reclassified token, an inline style, an unmapped class, a selectable prompt, an unselectable block, a wrapping rule |
| `theming`                    | seven probes, including moving the pre-paint snippet below the stylesheet and removing the storage guard |
| `contrast`                   | three probes: a lowered light value, a lowered dark-only value, warm used as text |
| `e2e`                        | found three real defects on its first run, see below |
| `metadata`                   | seven probes: a missing tag, a relative image, a drifted title, an empty tag, a placeholder, a missing image, an unresolved custom property |
| `font-coverage`              | caught two real uncovered characters on its first run |
| `separation`                 | four probes: a hard-coded label, a hard-coded accessible name, an inline style, a blinded fixture |

### What the browser found that nothing else could

The end-to-end suite caught three defects on its first run. Two were shipped
bugs; one was a bug in the tests themselves. None of them could have been caught
by reading the output.

**Code blocks had no background.** `figure.code .chroma { background: transparent }`
outranks `figure.code pre { background: var(--code-bg) }` on specificity,
`(0,2,1)` against `(0,1,2)`, and `.chroma` *is* the `<pre>`. All seven samples
rendered on the page background at **1.14:1**. Every individual rule was
correct; the cascade was not. `css-colors` passed, `syntax` passed, and
`contrast` passed, because the token *pairings* are fine, it is the resolved
background that was wrong.

**The theme button was visible without JavaScript.** An author `display: flex`
overrides the `hidden` attribute's UA `display: none`. The `theming` check
confirmed the attribute was present and stopped there, so the control was
present and inert, which is the exact failure its spec requirement forbids.

**A test passed for the wrong reason.** Chromium serialises `oklch()` in
computed style as `oklch()`, not `rgb()`. The helper that decided "is this
palette dark" averaged the numbers in the string, so `oklch(0.975 0.008 275)`
averaged to about 92 and read as dark. The "follows the system" test was green
while asserting nothing.

It now compares the resolved `--ground` against the token values exactly. Those
values come from `data/tokens.yaml` through the flake, and the `tokens` check
already pins them against the briefing, so there is still one source.

That third one is the lesson of this project in miniature: a green check that
means less than it appears to. It took a *different* test failing to expose it.

### Why contrast is computed, not eyeballed

`contrast.py` converts OKLCH to Oklab to linear sRGB to relative luminance,
following CSS Color 4 rather than approximating, and checks 18 pairings in both
palettes. The conversion was validated against known values: white, black and
pure red all round-trip exactly.

A dark-only regression is the case a light-mode-only check misses, so both
palettes are computed separately, and the probe that proves it lowers a
`dark:` value specifically.

**`--warm` is enforced in the CSS, not by contrast.** An earlier version of the
check asserted warm *fails* contrast in both palettes. That was wrong: in dark
it is about 10:1. The briefing's "insufficient contrast" is about the light
palette, where it is 1.76:1. The rule holds in both because warm is a fill, so
`warm-is-a-fill` greps the stylesheet instead, and `contrast` reports the light
ratio as a note so the number that motivates the rule stays visible.

### Say which half is deferred, on every run

`theming` proves the theme switch's **mechanism**: the pre-paint snippet is in
the head above the stylesheet, the control is a real button named from the
translation table, it ships hidden so it exists only when it works, storage
access is guarded, the toggle consults the system preference, and the page ships
exactly two scripts.

It cannot prove the **behaviour**. That is now settled by `e2e`, which exercises
no-flash, persistence across a reload, and the control's absence with scripting
disabled in a real browser. The static check still prints its deferral note,
because it remains true of that check on its own.

Three failure modes it does catch, each a real bug rather than a style point:

- **The toggle reading the stored value instead of the computed one.** A reader
  with nothing stored on a dark system would press once and get dark again.
- **A visible button with no script.** Present and inert is worse than absent: a
  reader cannot tell it from a broken page.
- **An unguarded `localStorage` read.** It throws in a private window rather
  than returning nothing, which would stop the pre-paint snippet and leave the
  wrong palette on screen.

### A gap reported out loud beats a test that quietly asserts less

`--tok-func` has a rule in `syntax.css` and **nothing on the page triggers it**.

The briefing warned this would happen: Chroma's Nix lexer may not classify
`lib.mkResource` as a function, and the instruction was to accept what the lexer
gives rather than adding markup to force it. Measuring all seven samples
confirmed it: across every language Chroma emits keywords, strings, escapes,
constants, prompts and comments, and no function or builtin token at all.

Three options existed. Deleting the token discards a value the briefing's
palette defines and would have to be restored the moment a sample uses a
builtin. Adding markup to the samples breaks the guarantee that a sample renders
byte for byte from its file. So the rule stays and `syntax` prints the gap on
every run:

    syntax: note, --tok-func is mapped but no sample currently produces it

The alternative was a test asserting "five token colours are used", which would
have been either false or quietly weakened until it passed. A visible gap is
worth more than a green check that means less than it looks like it means.

### Guard against a silent reclassification

`syntax` asserts that **specific** Chroma classes appear in **specific**
languages, measured from real output rather than transcribed from a published
list. A Hugo bump that reclassifies a token would otherwise restyle the page
with nothing failing. Now it fails the gate and names the language and the class.

### Execute the acceptance criterion, do not paraphrase it

Section 11 of the briefing says: *"Adding a project to
`data/home/projects.yaml` and `data/marks.yaml` adds a card with a generated
mark, with no template change."*

`tests/checks/acceptance.sh` replays that sentence rather than restating it as a
property. It really adds a project to a copy of the data, really rebuilds, and
then **diffs `layouts/` and `assets/`**.

The diff is the load-bearing part. Without it, the test could pass while
somebody had quietly added a special case to the template for the new project,
which is precisely the failure the criterion is written to prevent.

### The exemption was deleted, not emptied

While sections were still stubs, `page-chrome` carried an `UNBUILT_SECTIONS`
set, and it was built to **fail once every section in it resolved**, so it could
not quietly outlive its purpose. The last section landed and the constant and
its branch were removed, not left as an empty set. An empty exemption reads like
a disabled guard and invites somebody to put an entry back in it.

### Test the mechanism, not the outcome

`data/home/compare.yaml` flags which tool is the subject of the comparison.
Asserting "the Nivis column is highlighted" would pass against a template that
hard-codes the first column, which is exactly the implementation the flag exists
to prevent.

So the test moves the flag to a different tool, rebuilds, and asserts the
distinction moved with it. Then that test was itself verified: hard-coding
`eq .key "nivis"` in a copy of the template makes it report "the template is
hard-coding the column instead of reading the flag".

The same shape applies to step numbers and phase ordinals: both are proven by
reordering the data, not by checking that the first one says "1".

### Two accessibility rules that are easy to break later

**Scrolling regions are enumerated.** Only `figure.code pre` and `.table-scroll`
may scroll sideways. The check parses the bundled stylesheet for every
`overflow-x: auto` and asserts the selector set matches exactly. A stray one
anywhere else fails, naming the selector, and so does losing it on the table.
This is stricter than measuring document width in a browser and it catches the
regression before it ships. The browser-side proof belongs to the end-to-end
epic.

**The qualified tone is not meaning carried by colour.** Cells marked
`tone: weak` render in `--muted`, which on its own would fail for a reader who
cannot distinguish it. It is acceptable only because those cells say "No",
"Partly" and "In progress" in words: the colour is emphasis on a distinction the
text already makes. The check fails if a qualified cell is ever empty, so nobody
can later "simplify" the text to a tick and a cross.

### Compare counts, do not transcribe values

`sections` asserts that the number of items the page renders equals the number
in the data. It deliberately does not assert what those items contain.

"The audiences section has two cards" is the data copied into the test. It
passes forever, and fails only when somebody edits the data and forgets the
test, which is the wrong trigger. Comparing counts fails when the **template**
drops an item, which is the bug worth catching.

Two properties keep it honest as the site grows:

- A section listed in `content/_index.md` with no entry in the check fails the
  check. A new section therefore cannot arrive unguarded, it forces a decision.
- The step-numbering assertion builds the site a **second time from reordered
  data** and asserts the numbers follow positions rather than items. Asserting
  "the first step is numbered 1" would pass against a hard-coded `1`.

The collapse rule is tested as the briefing states it rather than as "it looks
right at 360 pixels": the bundled stylesheet must contain no width media query
at all, because collapsing is supposed to happen through
`minmax(min(N, 100%), 1fr)`. Whether it looks right is the end-to-end epic.

### The same-page link nothing else catches

`page-chrome` collects every `#target` in the built page and asserts each one
resolves to a real element. A navigation link to a section somebody renamed is
syntactically fine and never leaves the site, so no link checker will ever flag
it.

Four targets do not resolve yet, because four sections are still empty partials.
The check carries an explicit `UNBUILT_SECTIONS` exemption rather than being
switched off. The exemption **fails once every section in it resolves**, so it
cannot quietly outlive its purpose: whoever lands the last section is told to
delete it.

What it does not do: prove a focus ring is visible. It asserts `:focus-visible`
and `:hover` rules exist, because total absence is the common failure and is
cheap to catch. Visibility needs a real browser and belongs to the end-to-end
epic. That is deferred, not assumed.

### A test must be coupled to what it tests

The `reorder` fixture asserts that section dispatch follows content order. It
observed the real section partials, so the moment `hero.html` became real markup
instead of a stub, it failed for a reason that had nothing to do with dispatch.

The fixture now ships its own section stubs, mounted ahead of the real layouts.
The alternative, adding `data-section` attributes to production markup so tests
can see the structure, would have put test scaffolding into what ships.

### Check the artifact that ships, not a convenient stand-in

Three separate bugs in this project were found by pointing a check at the real
output instead of something easier to parse.

`tokens` originally read a standalone `tokens.css`. Once the stylesheets were
bundled, that file no longer existed, and pointing the check at the shipped
minified bundle immediately exposed a second bug in the checker itself:
minification drops the final semicolon before `}`, and the declaration regex
required one, so it was silently missing the **last** token of every rule set.
`--mark-core` dark was invisible to it.

The same reasoning runs through the suite:

- `tokens` parses the minified production bundle, not a readable intermediate.
- `mark` compares rendered, rounded path strings, not floats, because the
  rounding is part of the output.
- `snippets-unformatted` runs the formatter and compares bytes, instead of
  checking the formatter's source for an exclusion flag it might ignore.
- `assets` builds with the production environment, because fingerprinting and
  minification only happen there.

### A rule that rejects correct work gets turned off

This has now happened twice, and both times the fix was the same shape: make the
rule match what it *means* rather than what is easy to grep for, then re-probe
the narrowed version in **both** directions, because narrowing is how you create
a blind spot.

**`css-colors` flagged `white-space: pre`** as the colour "white". Named colours
now count only as values: after a colon, not part of a longer identifier.

**`no-external` flagged `rel="canonical"`.** It treated every `<link href>` as a
resource load, but a canonical link is metadata: it describes the page, it does
not fetch anything. As written the rule was impossible to satisfy for any site
with an absolute canonical address, which is every site. It now distinguishes by
`rel`: `stylesheet`, `preload`, `icon`, `preconnect` and friends fetch;
`canonical`, `alternate`, `author`, `license` do not. Re-probed with five real
external fetches (still caught) and two metadata links (correctly ignored).

### Metadata drift is the failure worth guarding

`metadata` asserts the sharing tags **agree with the page**, not merely that
they are non-empty. The failure it exists for is duplication drift: a title in
the page, a different one in `og:title`, a third in `twitter:title`, diverging
until a shared link contradicts the thing it links to.

It also catches a relative `og:image`, which looks perfectly correct in the
markup and fails only once somebody actually shares the link, because sharing
systems resolve those with no document base.



`css-colors` flagged `white-space: pre` as the colour "white". That is a false
positive on ordinary CSS, and a check that blocks legitimate work is a check
somebody disables.

Named colours now only count as **values**: after a colon, on the same
declaration, not part of a longer identifier. Re-probed in both directions, five
real colour notations still caught, and `white-space`, `.greenish-name`,
`var(--ink)` and `transparent` all correctly clean.

### Why the mark check reimplements the formula

`tests/checks/mark.py` evaluates `r(theta) = a + b * cos(k * theta)` in Python
from the briefing's formula, and compares every one of the 120 points of every
layer of every mark against Hugo's output. 9 marks, 31 layers, 3720 points.

Reusing anything from the template would make this circular. Two independent
implementations of the same formula agreeing is evidence; one implementation
agreeing with itself is not.

Comparison is on the rendered string after rounding, because that is what ships.
Comparing floats before rounding would pass on a Hugo whose number formatting
changed, and the formatting is part of the output.

Whole paths, not spot checks: sampling the first point catches a wrong radius,
but not a flipped rotation sign, an off-by-one in the sample count, or a `k`
that only diverges after a quarter turn. All 120 points cost nothing to compare.

**The parameters are deliberately not pinned.** The check reads them from
`data/marks.yaml`, so editing a parameter moves the expectation with it and the
check still passes. Only the formula and the layer sets are pinned. This is
intended: the per-project parameters are provisional and the maintainer may
replace them. It does mean a probe that edits a parameter before rendering
proves nothing. The probe that counts changes the data **after** rendering, so
output and data disagree.

### Why `snippets-unformatted` exists

`snippets/` holds three `.nix` files. `flake.nix` is a complete flake whose
exact line breaks are the approved copy a reader sees, and `roundtrip-note.nix`
is a fragment that is not valid Nix on its own. `nix fmt` reflowed the first and
errored on the second the first time it ran over them.

Both failures are invisible from a reader's point of view: the page simply shows
something other than what was approved. So the formatter excludes `snippets/`,
and this check proves the exclusion works by **running** the formatter and
comparing bytes. Checking the formatter's source for an exclusion would test the
wrong thing: it would pass for a formatter that has the flag and ignores it.

A warning for whoever probes this check next. The probe that proves it bites
runs the formatter without its exclusion, and the first time it was run it was
pointed at the real tree and corrupted `snippets/flake.nix` for real. Run
destructive probes on a copy.

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

### Two probes that proved nothing

Twice now a probe looked like a test and was not one. Both share a shape: the
probe moved both sides of a comparison, so the check had nothing to notice.

- Editing a snippet file does not trip the byte-for-byte assertion, because the
  expected value **is** the file.
- Editing a mark parameter does not trip the geometry check, because the
  expected path is computed from that parameter.

In each case the real probe corrupts the thing under test (the renderer, the
output) rather than the thing it is compared against. Treat a probe that passes
as a result needing an explanation, not as reassurance.

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

### The copy scan, and why it reads only two places

`separation` enforces the half of the rule that matters most to an editor: no
template contains a word a reader sees or hears.

It cannot be a blanket ban on word characters. Templates legitimately contain
element names, attribute names, class names and template logic, and a scan that
treats all of it as copy rejects `<section class="hero">` and gets switched off
within a week. So it reads exactly the two places text reaches a reader:

- **text nodes**, after template actions, comments, and script and style blocks
  are removed,
- **the values of reader-perceived attributes**: `alt`, `title`, `aria-label`,
  `aria-description`, `placeholder`.

**Order matters, and getting it wrong produced two false positives on the first
run.** Template actions must be stripped *before* attributes are matched,
because a Go action can contain quotes: `aria-label="{{ i18n "theme_switch" }}"`
stops an attribute regex at the inner quote and reports `{{ i18n` as hard-coded
copy. And script blocks are code, not language: the theme switch's pre-paint
snippet was read as a sentence.

The style scan runs on the **generated HTML**, not on templates, because a
template can compose a style attribute from variables without containing one.

| Allowed | Why |
|---------|-----|
| (empty) | Nothing is allowed. Add a row with a reason, or move the string to `data/` or `i18n/en.yaml`. |

Both scans assert their negative fixtures are caught before reporting the real
tree clean, and `tests/fixtures/copy-in-template/good.html` is the same markup
written correctly, which must **not** be flagged. A rule with no counter-example
becomes an obstacle.

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

Measured in a real browser from what the page actually requests, not by summing
the published directory. A browser downloads a font only when an element needs
that weight, so a declared-but-unused face costs a reader nothing; measuring the
directory would have counted 90 KB nobody ever fetches.

Numbers are uncompressed, the pessimistic case: the test server does not
compress, production does, and fonts gain nothing from it.

| Metric | Budget | Measured |
|------------------------|-----------|-----------|
| Cold load, transferred | 220 KB    | 189,288 B |
| Requests               | 10        | 8         |
| HTML                   | 80 KB     | 69,883 B  |
| CSS                    | 16 KB     | 11,919 B  |
| JavaScript             | 4 KB      | 406 B     |
| Render-blocking        | 1         | 1         |

Each budget sits a little above its measurement, so ordinary churn passes and a
real regression fails. Raising one should be a visible decision in a diff.

58% of the raw HTML is generated mark path data, 32 paths of 120 sampled points
each. It gzips to roughly a quarter, which is why the budget is on transferred
bytes rather than raw.

### Why there is no Lighthouse score in the gate

The briefing asks for 95+. A Lighthouse performance score measured in a shared
build sandbox is dominated by how busy the machine is, not by the site: the same
commit scores differently on consecutive runs. A gate that fails at random
teaches people to re-run it until it passes, which is worse than not having one.

The deterministic parts of what Lighthouse reports are gated directly: total
bytes, request count, render-blocking resources, `font-display`, and the full
accessibility audit `e2e` already runs with axe-core. The timing-derived score is
the part left out, and it belongs in a non-gating run against the deployed site
where the numbers mean something.

### Subsetting, and the check it needed

Hind is an Indic typeface: 1006 glyphs for 434 codepoints, most of the excess
Devanagari conjuncts an English site never renders. Subsetting took the served
fonts from **475 KB to 107 KB**, and the cold load from 466,808 to 189,288 bytes.

Subsetting fails silently: a dropped glyph renders from a fallback or as a
notdef box, and nothing errors. So `font-coverage` verifies the subset against
the **actual rendered text** of the built page rather than an assumed alphabet.

It earned itself immediately, and then taught a second lesson. It flagged a
Greek theta and a rightwards arrow. The obvious reading was "the subset broke
them". Checking the source TrueType files showed the fonts never had those
glyphs: they had been rendering from a system fallback since those sections were
built.

The check now compares against the source fonts and separates the two:

| Situation | Response |
|---|---|
| Source had the glyph, subset dropped it | **fail**, a regression introduced here |
| Source never had it | **note**, a typeface choice, surfaced in the README |

Failing the build over somebody else's choice of typeface would be a check
nobody could satisfy. Staying silent about it would hide a real defect in how
the page renders. Reporting it is the only honest option.
