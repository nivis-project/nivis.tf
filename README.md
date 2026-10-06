# nivis.tf

The public website for the [Nivis project](https://github.com/nivis-project),
served at [nivis.tf](https://nivis.tf).

One page. Hugo extended, no theme, no JS framework, no CSS framework, no build
step beyond Hugo Pipes. The only JavaScript on the site is the theme switch.

## Run it locally

```bash
nix develop -c hugo server     # http://localhost:1313
nix build                      # the built site, in ./result
nix flake check                # the full gate
```

The Hugo version is pinned in `.hugo-version`. The `hugo-version-pin` check
fails when nixpkgs drifts away from it, so the dev shell, the build and the
deployment cannot quietly disagree.

## Where things live

Content, style and template are strictly separated. This is the project's one
hard architectural rule, and `nix flake check` fails when it is broken.

| You want to change | Open |
|-----------------------------------|------------------------------|
| A word on the page                | `data/`, `content/`, `i18n/` |
| A code sample                     | `snippets/`                  |
| A color, a font, a spacing value  | `assets/css/tokens.css`      |
| Other styling                     | `assets/css/`                |
| Markup                            | `layouts/`                   |

`layouts/` contains no copy, not even a button label or an aria-label. Those
come from `data/` or `i18n/en.yaml`. `tokens.css` is the only file in the
project that may contain a color value.

So: you can change every word on the site without opening `layouts/` or
`assets/`, and restyle the site without touching `content/` or `data/`.

## Add a section

1. Add `data/home/<name>.yaml` with its copy.
2. Add `layouts/partials/sections/<name>.html` to render it.
3. Add `<name>` to the `sections` list in `content/_index.md`, in the position
   you want it.

Reordering that list reorders the page. Removing an entry removes the section.
Neither needs a template change.

## Add a project card

1. Add the entry to `data/home/projects.yaml`.
2. Add its mark parameters to `data/marks.yaml`.

The mark is generated at build time from the polar curve
`r(theta) = a + b * cos(k * theta)`. No template change, and no JavaScript.

## How work is organised

- **Beans** hold the milestones and epics. `beans list --ready` says what is
  workable right now.
- **OpenSpec** holds the proposals, tasks and specs. They live in the `nivis-tf`
  store, a separate repo shared with the org's other projects, not in this one.
- `scripts/ship-change.sh` is the gated tail: it stages, gates, archives, closes
  the bean, commits, publishes the store and pushes, in that order, and aborts
  before archiving if the gate fails.

`AGENTS.md` has the full working agreement. `docs/TESTING.md` says what each
check guards.

## The design source

`nivis-tf-hugo-briefing.md` holds the approved copy, the design tokens, the page
anatomy and the mark formula. `nivis-mockup-reference.html` is the tie-breaker
for exact spacing and sizes; it is a design-tool file, so its inline styles and
structure never go into the site.

## Open points for the maintainer

These are decisions the briefing leaves to you. Nothing in the test suite can
settle them, and none of them block building the site.

1. **The code samples and the comparison table are unverified.** They were
   assembled from summaries of the READMEs, and `snippets/main.tf` was written
   as a counterpart for this page. The gate proves they render faithfully and
   that every link resolves; it cannot prove a flag was not renamed or that a
   claim about another project is still true. Check them against the
   repositories before launch.
2. **Hosting is assumed to be Amplify,** because the domain showed an Amplify
   placeholder. `amplify.yml` is written for it.
3. **The mark is coloured here; the original logo is a single grey**
   (`#4d4d4d`) with translucent layers. Every fill is a custom property, so
   this is one edit either way.
4. **The per-project mark parameters are provisional** and may be replaced.
   They live in `data/marks.yaml`.
5. **Whether the site grows beyond one page.** The structure allows docs or a
   blog; this build does not add them.
6. **The social preview image is an SVG,** generated from the mark at build
   time. Several platforms will not render SVG previews and will show no image.
   The alternatives were worse: rasterising needs a new build dependency and a
   new failure mode, and a hand-exported PNG would be the one asset that
   silently stayed behind when the mark changed. Say so if a raster preview
   matters and it becomes a small follow-up change.
7. **Fonts are built from nixpkgs, not committed.** The briefing says to
   self-host them in `static/fonts/`, which reads as committing the woff2
   files. Hind comes from `google-fonts` and IBM Plex Mono from `ibm-plex`,
   both as TrueType, and the build converts them with `woff2_compress`. That
   keeps binaries out of the repository and licences tracked by nixpkgs, but it
   means `hugo server` run outside `nix develop` falls back to the system face.
   Say so if you would rather commit the files.

## License

Apache-2.0.
