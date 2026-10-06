# nivis.tf

The public website for the Nivis project (https://github.com/nivis-project),
served at nivis.tf. One page, built with Hugo extended. No theme, no JS
framework, no CSS framework, no build step beyond Hugo Pipes. The only
JavaScript on the site is the theme switch.

The audience knows Nix, Terraform, or both. The page has to get them trying
Nivis within minutes and tell them what it is.

## The one hard architectural rule

**Content, style and template are strictly separated.**

- **Content** lives in `content/`, `data/` and `snippets/`. No HTML, no CSS
  classes, no colors, no sizes. Inline Markdown (bold, code, links) is allowed.
- **Templates** live in `layouts/`. No copy at all, not even button labels or
  aria-labels: those come from `data/` or `i18n/`. No `style=""` attributes.
- **Style** lives in `assets/css/`. Every color, font and spacing value is a
  design token in `tokens.css`. No hex and no oklch value exists outside that
  file.

A person must be able to change every word on the site without opening
`layouts/` or `assets/`, and restyle the site without touching `content/` or
`data/`.

This is not a guideline. `nix flake check` fails when it is broken, and every
change that touches rendering carries a test that proves it still holds.

## The briefing is the source of copy

`nivis-tf-hugo-briefing.md` holds the complete approved copy, the design
tokens, the page anatomy and the mark formula. Read it before writing anything.

`nivis-mockup-reference.html` is the tie-breaker for exact spacing and sizes. It
is a design-tool file, not production code: never copy its inline styles or its
structure into the site. Its embedded mark generator is a reference to check the
Hugo implementation against, not code to port.

`Nivis website.html` is a bundled render of that mockup. It is there to look at,
nothing more.

## Commands

```bash
nix develop                         # dev shell with the pinned Hugo and test tools
nix develop -c hugo server          # serve the site locally
nix build                           # build the site into ./result
nix flake check                     # the full gate: build, invariants, e2e, a11y
nix fmt                             # format Nix files

openspec list                       # active changes (they live in the nivis-tf store)
openspec validate <change> --strict # must pass before implementing
openspec archive <change> --yes     # fold the deltas into specs/

beans list --ready                  # what is unblocked and workable right now
beans show <id>                     # read an epic in full
beans prime                         # relearn the beans workflow

scripts/ship-change.sh <change> "<subject>" --bean <id>   # the gated ship
```

## OpenSpec

Changes and specs for this project do **not** live in this repo. They live in
the `nivis-tf` store at
`~/gh.nivis-project/nivis-openspec-stores/nivis.tf`, a separate git repo shared
with the org's other projects. `openspec/config.yaml` here holds only the
`store:` pointer, and the OpenSpec CLI follows it automatically.

Per change:

1. Propose: scaffold the change folder.
2. Write `proposal.md` (why, what, explicit non-goals), `tasks.md` (ordered
   work) and the spec deltas under `specs/<capability>/spec.md`, marked ADDED,
   MODIFIED or REMOVED, each with GIVEN / WHEN / THEN scenarios. Add `design.md`
   when the technical approach is non-trivial.
3. `openspec validate <change> --strict` must pass. Do not implement first.
4. Implement `tasks.md` in order. Every task that changes behaviour gets a test
   in the same change. See `docs/TESTING.md`.
5. `nix flake check` must pass.
6. Ship with `scripts/ship-change.sh`, which gates, archives, closes the bean,
   commits, publishes the store and pushes, in that order.

Keep each change small enough to review and archive on its own.

## Testing

Thorough testing is a requirement of this project, not a nice-to-have. A change
that renders something and has no test proving it renders correctly is not
finished.

The check set, each wired as its own `checks.<system>.<name>` so a failure names
what broke:

- `build` the site builds with no Hugo warnings
- `unit` Hugo template assertions driven by fixture sites under `tests/fixtures/`
- `invariants` the separation rules above, as greps over the source tree and the
  generated HTML, each with a negative fixture proving the check actually bites
- `html` the generated HTML is valid and semantic
- `links` every external link resolves
- `e2e` Playwright against the built `public/`, served statically. Browsers come
  from nixpkgs through `PLAYWRIGHT_BROWSERS_PATH`, never downloaded at test time
- `a11y` axe-core over the built page in both themes

Everything runs offline inside the Nix sandbox.

There is no line-coverage floor here. A Hugo site has no meaningful line
coverage, so the gate is the full check set plus the acceptance checklist in
section 11 of the briefing.

## Nix

Plain Nix. **Do not add flake-utils.** Supported systems are a literal list that
the flake maps over with its own `forAllSystems` helper built from
`nixpkgs.lib.genAttrs`.

The Hugo version is pinned in `.hugo-version` and read from there by both the
flake and `amplify.yml`. The `hugo-version-pin` check fails when nixpkgs drifts
away from it. Never update one of the three without the other two.

## Version control

`jj` (Jujutsu), colocated with git. git remains the backing store and the push
transport. Remote: `git@github.com:nivis-project/nivis.tf.git`.

Commit after every archived OpenSpec change, through `scripts/ship-change.sh`.
Commits are authored by Pim Snel alone: no `Co-authored-by`, no "Generated with"
trailer, no agent attribution of any kind.

`nix flake check` evaluates the **git** tree, so a file git does not know about
is invisible to it. The ship script stages the working tree before gating for
exactly this reason.

## Prose

No em dashes, no en dashes, no curly quotes, anywhere: not in the site copy, not
in a spec, not in a commit message. Name the relation instead ("because", "but",
"for example"), use a comma, a colon or parentheses, or write two sentences.
Hyphens and dashes inside code, commands, paths and URLs are not prose and stay
as they are.

## Beans

When I refer to issues like nivistf-rn3b checkout the task
in @.beans/nivistf-rn3b-*.md

In this project we will use these tasks as epics for making openspec proposals.

WHEN you create a proposal at a link to this task in the proposal.md.
WHEN a bean is used to create an proposal change the status to "in-progress"
WHEN a proposal is archived add the link to the archived proposal in the frontmatter of this task like this:

```
openspec-link: openspec/changes/archive/....
```

You are allowed to update these statuses in the task frontmatter:

- in-progress
- todo
- draft
- completed
- scrapped

When making changes you are allowed to update the date/time in `updated_at` in the task frontmatter

Besides updating status and openspec-link, you are NOT ALLOWED to modify the contents of the task file.

### Why openspec-link is written by the ship script

`beans` rewrites the whole bean file on every update and drops front-matter keys
it does not recognise, `openspec-link` among them. Writing the link before the
last `beans update` therefore loses it silently.

`scripts/ship-change.sh` writes it after closing the bean, through
`scripts/link-bean.py`, and takes the name from the archive directory rather
than guessing it: `openspec archive` adds a date prefix, so the real name is
only knowable after the archive has run. Do not write the key by hand before
shipping.
