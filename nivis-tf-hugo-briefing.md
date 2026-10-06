# Briefing: build nivis.tf in Hugo

You are implementing the public website for **Nivis** (https://github.com/nivis-project) at **nivis.tf**. A designed mockup of the homepage exists; this briefing describes it completely, so you can build without access to the mockup. The file `nivis-mockup-reference.html` (if present next to this briefing) is the mockup's source and is the tie-breaker for exact spacing and sizes. It is a design-tool file, not production code: do not copy its inline styles or structure into the site.

## 1. Goal

A single-page site, the counterpart of the GitHub organisation, that gets people who know **Nix and/or Terraform** trying Nivis within minutes and tells them what it is.

The one hard architectural rule:

> **Content, style and template are strictly separated.**

- **Content** lives in `content/`, `data/` and snippet files. It contains no HTML, no CSS classes, no colors, no sizes. Inline Markdown (bold, code, links) is allowed.
- **Templates** live in `layouts/`. They contain no copy (not even button labels or aria-labels; those come from data or `i18n/`) and no `style=""` attributes.
- **Style** lives in `assets/css/`. All colors, fonts and spacing come from design tokens (CSS custom properties). No hex or oklch value appears outside the tokens file.

A person must be able to change every word on the site without opening `layouts/` or `assets/`, and restyle the site without touching `content/` or `data/`.

## 2. Context and constraints

- **Repository:** `nivis-project/nivis.tf` (currently holds only a README).
- **Hosting:** the domain currently shows an AWS Amplify placeholder, so Amplify is assumed. Add an `amplify.yml` whose `baseDirectory` is `public`. Confirm the hosting choice with the maintainer before changing it.
- **Hugo:** use the current Hugo **extended** release and pin the exact version in both the dev shell and `amplify.yml`. Follow that version's layout-directory conventions. The mark generator (section 7) needs `math.Cos`, `math.Sin` and `math.Pi`; check they exist in the pinned version.
- **Dev environment:** provide a `flake.nix` with a dev shell containing Hugo, so `nix develop -c hugo server` works. This project's audience expects it.
- **No theme dependency.** Write the layouts in the repo itself.
- **No JS framework, no CSS framework, no build step beyond Hugo Pipes.** The only JavaScript is the theme switch (section 8).
- **No external requests at runtime.** Self-host the fonts.
- **Language:** English. Put UI strings in `i18n/en.yaml` so a second language can be added later.

## 3. Suggested structure

Adapt names to the pinned Hugo version's conventions, but keep the separation.

```
hugo.yaml
flake.nix
amplify.yml
content/
  _index.md                 # page title, description, ordered list of sections
data/
  site.yaml                 # nav, footer, repo base URL
  marks.yaml                # mark parameters (section 7)
  home/
    hero.yaml
    audiences.yaml
    quickstart.yaml
    roundtrip.yaml
    compare.yaml
    projects.yaml
    docs.yaml
snippets/                   # mounted as assets; one file per code sample
  hero-run.console
  main.tf
  flake-excerpt.nix
  quickstart-tour.console
  flake.nix
  quickstart-apply.console
  roundtrip-note.nix
i18n/en.yaml                # UI strings: skip link, theme switch label, etc.
layouts/
  baseof / home templates
  partials/
    head.html  header.html  footer.html
    mark.html               # generates the SVG mark from parameters
    code.html               # reads a snippet file, highlights it, adds optional filename label
    sections/
      hero.html  audiences.html  quickstart.html  roundtrip.html
      compare.html  projects.html  docs.html
assets/
  css/
    tokens.css              # the only file with color/font/space values
    base.css  layout.css  components.css  syntax.css
  js/theme.js
static/fonts/               # Hind, IBM Plex Mono (woff2)
```

`content/_index.md` front matter lists the sections in order. The home template loops over that list and calls `partials/sections/<type>.html` with the matching data file. Reordering or removing a section is then a content change.

```yaml
---
title: "Nivis: Terraform providers as first-class Nix values"
description: "Describe real infrastructure in a Nix flake instead of HCL. Nivis drives unmodified Terraform and OpenTofu providers and feeds their outputs back into Nix."
sections: [hero, audiences, quickstart, roundtrip, compare, projects, docs]
---
```

Code samples are separate files so they can be copied, linted and tested on their own. Data files reference them by filename. `partials/code.html` reads the file and highlights it with Hugo's built-in highlighter (`transform.Highlight`), language taken from the data entry.

## 4. Content

This is the complete copy. Put it in the data files as shown. Strings may contain inline Markdown; render them with `markdownify` (or `.RenderString`).

**Before launch, the maintainer must check all code samples and the comparison table against the repositories.** They were assembled from summaries of the READMEs and docs, and `main.tf` was written as a counterpart for this page.

### data/site.yaml

```yaml
name: Nivis
domain: nivis.tf
license: Apache-2.0
github_org: https://github.com/nivis-project
docs_base: https://github.com/nivis-project/nivis/blob/HEAD/docs
nav:
  - { label: Quick start, href: "#start" }
  - { label: Round trip,  href: "#roundtrip" }
  - { label: Compare,     href: "#compare" }
  - { label: Projects,    href: "#projects" }
nav_cta: { label: GitHub, href: https://github.com/nivis-project }
footer_links:
  - { label: GitHub, href: https://github.com/nivis-project }
  - { label: Issues, href: https://github.com/nivis-project/nivis/issues }
```

### data/home/hero.yaml

```yaml
badge: "early but real · Apache-2.0"
title: "Terraform providers as first-class Nix values."
lead: >-
  Describe real infrastructure in a flake instead of HCL. A thin Go executor
  drives unmodified Terraform and OpenTofu provider binaries, and what the
  cloud returns flows back into Nix.
primary:   { label: "Try it in five minutes",    href: "#start" }
secondary: { label: "How the round trip works",  href: "#roundtrip" }
snippet:   { file: hero-run.console, lang: console }
mark_alt: "The Nivis mark: layered shapes drawn from h(θ) = a + b · cos 3θ"
```

### data/home/audiences.yaml

```yaml
title: "You already know half of it."
cards:
  - title: "Coming from Nix"
    lead: "The missing half is the provider ecosystem."
    points:
      - "A **provider** is a plugin binary that speaks to one cloud API. Nivis runs any OpenTofu-compatible provider as-is."
      - "**plan** previews what would change, **apply** makes it so, and **state** remembers what exists."
      - "A resource is an attrset built with `mkResource`. Compose it with the functions and modules you already write."
  - title: "Coming from Terraform"
    lead: "The missing half is the language."
    points:
      - "Same providers, same **plan / apply / destroy**. A `flake.nix` takes the place of your `.tf` files."
      - "`aws_s3_bucket.demo.id` becomes `bucket.refAttr \"id\"`, an ordinary value you can pass to any function."
      - "Nix also builds machines. A NixOS image and the cloud resources that boot it can live in one expression."
compare_snippets:
  - { label: "main.tf",             file: main.tf,           lang: hcl }
  - { label: "flake.nix (excerpt)", file: flake-excerpt.nix, lang: nix }
```

### data/home/quickstart.yaml

```yaml
id: start
title: "Quick start"
lead: "All you need is Nix with flakes enabled. The first two steps touch no cloud account."
steps:
  - title: "Run it without cloning"
    snippet: { file: hero-run.console, lang: console }
  - title: "Take the guided tour"
    text: "`nivistutor` scaffolds a sandboxed tutorial project, so you can watch a plan and an apply before any credentials are involved."
    snippet: { file: quickstart-tour.console, lang: console }
  - title: "Write a flake"
    text: "One provider, one resource. This is a complete `flake.nix`."
    snippet: { file: flake.nix, lang: nix }
  - title: "Plan, apply, inspect, destroy"
    text: "From here on you are creating real resources in your own AWS account."
    snippet: { file: quickstart-apply.console, lang: console }
    link: { label: "Read the full getting-started guide", doc: GETTING-STARTED.md }
```

### data/home/roundtrip.yaml

```yaml
id: roundtrip
title: "The round trip"
lead: >-
  A provider creates a resource and returns values nobody could know
  beforehand: an IP, an ID, a generated name. Nivis hands those back to Nix
  and evaluates again, until nothing is left unknown.
phases:
  - label: evaluate
    text: "Nix evaluates your flake to a JSON plan. Values that only exist after apply become typed placeholders."
  - label: apply
    text: "The executor applies everything that is fully known, speaking the plugin protocol to the provider binaries."
  - label: ledger
    text: "Whatever the providers computed is collected in the ledger."
  - label: re-evaluate
    text: "Nix runs again with the ledger as input. Placeholders resolve, the next phase unlocks, and the loop repeats to a fixpoint."
example:
  snippet: { file: roundtrip-note.nix, lang: nix }
  title: "A file whose content depends on a name AWS has yet to invent"
  text: "The bucket id does not exist until phase one has run. In phase two Nix builds the string around it, and the result becomes the body of a real S3 object."
  link: { label: "Follow the AWS S3 tutorial", doc: TUTORIAL-AWS-S3.md }
```

The phase numbers (`01` to `04`) are generated by the template, not stored.

### data/home/compare.yaml

Each cell has a `value` and an optional `tone: weak` (rendered in the muted text color for "no", "partly", "in progress"). The first column is Nivis and is visually highlighted by the template because it is flagged `highlight: true`.

```yaml
id: compare
title: "Where Nivis sits"
lead: >-
  Terranix generates HCL from Nix and hands it to Terraform. Pulumi compiles
  providers through a bridge. Nivis keeps resources as Nix values and spawns
  the providers untouched.
tools:
  - { key: nivis,    name: "Nivis", highlight: true }
  - { key: tf,       name: "OpenTofu / Terraform" }
  - { key: terranix, name: "Terranix" }
  - { key: nixops,   name: "NixOps 4" }
  - { key: pulumi,   name: "Pulumi" }
rows:
  - label: "Config language"
    nivis: { value: "Nix" }
    tf: { value: "HCL" }
    terranix: { value: "Nix → HCL" }
    nixops: { value: "Nix" }
    pulumi: { value: "TS, Python, Go, …" }
  - label: "Reuses Terraform / OpenTofu providers"
    nivis: { value: "Yes, spawned unmodified" }
    tf: { value: "Yes, native" }
    terranix: { value: "Yes, via Terraform" }
    nixops: { value: "In progress", tone: weak }
    pulumi: { value: "Yes, via bridge" }
  - label: "Outputs feed back into config"
    nivis: { value: "Yes, phased re-evaluation" }
    tf: { value: "Partly: HCL references only", tone: weak }
    terranix: { value: "No", tone: weak }
    nixops: { value: "Yes" }
    pulumi: { value: "Yes, Output<T>" }
  - label: "Plan before apply"
    nivis: { value: "Yes" }
    tf: { value: "Yes" }
    terranix: { value: "Yes, via Terraform" }
    nixops: { value: "Partly", tone: weak }
    pulumi: { value: "Yes" }
  - label: "OS build and cloud in one expression"
    nivis: { value: "Yes, NixOS image → AMI" }
    tf: { value: "No", tone: weak }
    terranix: { value: "No", tone: weak }
    nixops: { value: "Yes" }
    pulumi: { value: "No", tone: weak }
  - label: "License"
    nivis: { value: "Apache-2.0" }
    tf: { value: "MPL-2.0 / BUSL-1.1" }
    terranix: { value: "MIT" }
    nixops: { value: "LGPL-2.1" }
    pulumi: { value: "Apache-2.0 core" }
link: { label: "Read the full comparison, including CDK and CloudFormation", doc: COMPARISON.md }
```

### data/home/projects.yaml

`mark` refers to an entry in `data/marks.yaml`. The card links to `<github_org>/<name>`.

```yaml
id: projects
title: "The Nivis projects"
lead: "Every mark is the same curve, `h(θ) = a + b · cos kθ`, with different parameters."
items:
  - name: nivis
    status: "early but real"
    mark: nivis
    text: "The library and executor. Provider resources as Nix values, applied to a fixpoint."
  - name: registry
    status: "alpha"
    mark: registry
    text: "A browsable catalog of OpenTofu-compatible providers with Nix-native documentation."
  - name: nivis-tunnel
    status: "proof of concept"
    mark: tunnel
    text: "Deploy NixOS closures to machines with no inbound ports, over a Noise-encrypted relay."
  - name: nivis-demos
    status: "examples"
    mark: demos
    text: "Small reproducible stacks: state bootstrap, one NixOS workload on two clouds, tunnel deploys."
  - name: terraform-provider-nivis-tunnel
    status: "provider"
    mark: tunnel-provider
    text: "Terraform provider for the Nivis deployment tunnel."
  - name: terraform-provider-hcloudimage
    status: "provider"
    mark: hcloudimage
    text: "Upload raw disk images to Hetzner Cloud from Terraform or OpenTofu."
```

### data/home/docs.yaml

```yaml
title: "Go deeper"
text: "Nivis is early. The round trip works across providers, and AWS applies, updates, replaces and destroys today. Issues and experiments are welcome."
cta: { label: "Try it in five minutes", href: "#start" }
links:
  - { label: Installation, doc: INSTALL.md }
  - { label: Overview,     doc: OVERVIEW.md }
  - { label: Design,       doc: DESIGN.md }
  - { label: Data sources, doc: DATASOURCES.md }
  - { label: IR contract,  doc: IR-CONTRACT.md }
  - { label: Demos,        href: https://github.com/nivis-project/nivis-demos }
```

A link with `doc:` resolves to `<docs_base>/<doc>`; a link with `href:` is used as-is.

### Footer

Built from `data/site.yaml`: small mark, then "`<name>` · `<license>` · `<domain>`", then `footer_links`.

### Snippet files

`snippets/hero-run.console`
```console
$ nix run github:nivis-project/nivis#nivis -- --version
```

`snippets/main.tf`
```hcl
provider "aws" {
  region = "eu-central-1"
}

resource "aws_s3_bucket" "demo" {
  force_destroy = true
}
```

`snippets/flake-excerpt.nix`
```nix
providers.aws = lib.mkProvider {
  source = "registry.opentofu.org/hashicorp/aws";
  config.region = "eu-central-1";
};
resources = [
  (lib.mkResource {
    provider = "aws"; type = "aws_s3_bucket"; name = "demo";
    config.force_destroy = true;
  })
];
```

`snippets/quickstart-tour.console`
```console
$ nix shell github:nivis-project/nivis#nivis github:nivis-project/nivis#tutor
$ nivistutor
```

`snippets/flake.nix`
```nix
{
  inputs.nivis.url = "github:nivis-project/nivis";
  outputs = { self, nivis }:
    let lib = nivis.lib; in {
      nivis.plan = ledger: lib.toIR {
        providers.aws = lib.mkProvider {
          source = "registry.opentofu.org/hashicorp/aws";
          config.region = "eu-central-1";
        };
        resources = [
          (lib.mkResource {
            provider = "aws"; type = "aws_s3_bucket"; name = "demo";
            config.force_destroy = true;
          })
        ];
        inherit ledger;
      };
    };
}
```

`snippets/quickstart-apply.console`
```console
$ nivis plan                              # preview changes
$ nivis apply                             # apply to fixpoint
$ nivis state show aws.aws_s3_bucket.demo
$ nivis destroy
```

`snippets/roundtrip-note.nix`
```nix
note = lib.mkResource {
  provider = "aws";
  type = "aws_s3_object";
  name = "note";
  config = {
    bucket = bucket.refAttr "id";
    key = "hello-from-nix.txt";
    content = lib.str [
      "This file's content was generated by Nix.\n"
      "It is stored in the bucket named: "
      (bucket.refAttr "id")
      "\n"
    ];
    content_type = "text/plain";
  };
};
```

## 5. Design tokens

Put these in `assets/css/tokens.css`. Light values go on `:root`. Dark values apply under `:root[data-theme="dark"]` **and** under `@media (prefers-color-scheme: dark)` for `:root:not([data-theme="light"])`. Keep the dark values in one place (for example, generate both rule sets from a single list in a Hugo-templated CSS file) so the two never drift.

The palette is one indigo hue (275), halfway between Nix blue and Terraform purple, plus one warm amber accent.

| Token | Role | Light | Dark |
|---|---|---|---|
| `--ground` | page background, cards on surface | `oklch(0.975 0.008 275)` | `oklch(0.17 0.03 275)` |
| `--surface` | alternating section background, table | `oklch(0.995 0.003 275)` | `oklch(0.21 0.035 275)` |
| `--ink` | text | `oklch(0.24 0.04 275)` | `oklch(0.94 0.012 275)` |
| `--muted` | secondary text | `oklch(0.45 0.035 275)` | `oklch(0.76 0.035 275)` |
| `--line` | borders, dividers | `oklch(0.88 0.02 275)` | `oklch(0.34 0.04 275)` |
| `--accent` | links, outline button border | `oklch(0.42 0.19 275)` | `oklch(0.78 0.12 275)` |
| `--accent-soft` | highlighted table column | `oklch(0.93 0.04 275)` | `oklch(0.3 0.07 275)` |
| `--warm` | primary buttons, step numbers | `oklch(0.8 0.14 78)` | same |
| `--on-warm` | text on `--warm` | `oklch(0.17 0.03 275)` | same |
| `--code-bg` | code block background | `oklch(0.23 0.045 275)` | `oklch(0.13 0.025 275)` |
| `--code-ink` | code text | `oklch(0.93 0.015 275)` | same |
| `--code-dim` | comments, shell prompt | `oklch(0.74 0.05 275)` | same |
| `--band-bg` | round-trip section background | `oklch(0.235 0.09 275)` | `oklch(0.23 0.08 275)` |
| `--band-ink` | text on band | `oklch(0.96 0.01 275)` | same |
| `--band-muted` | secondary text on band | `oklch(0.84 0.04 275)` | same |
| `--band-line` | card borders on band | `oklch(0.46 0.08 275)` | same |
| `--band-code` | code block on band | `oklch(0.19 0.05 275)` | `oklch(0.15 0.04 275)` |
| `--mark-a` | mark outer layers (blue) | `oklch(0.6 0.16 250)` | `oklch(0.72 0.13 250)` |
| `--mark-b` | mark outer layers (purple) | `oklch(0.55 0.2 305)` | `oklch(0.7 0.16 305)` |
| `--mark-core` | mark core (indigo) | `oklch(0.37 0.19 275)` | `oklch(0.82 0.1 275)` |
| `--tok-keyword` | syntax: keywords | `oklch(0.8 0.13 320)` | same |
| `--tok-string` | syntax: strings | `oklch(0.85 0.11 160)` | same |
| `--tok-func` | syntax: functions, commands | `oklch(0.83 0.1 240)` | same |
| `--tok-literal` | syntax: booleans, numbers | `oklch(0.85 0.12 78)` | same |

Code blocks are dark in both modes. `--warm` is never used as a text color on `--ground` or `--surface` (insufficient contrast); it is a fill only.

**Type**

- Sans: **Hind** (300, 400, 500, 600), fallback `'Segoe UI', system-ui, sans-serif`. Hind is the logo typeface.
- Mono: **IBM Plex Mono** (400, 500), fallback `ui-monospace, monospace`.
- Body 18px / 1.55. Lead paragraph 21px / 1.5 (20px on the band).
- `h1`: `clamp(40px, 5.6vw, 68px)`, weight 600, line-height 1.04, letter-spacing -0.02em, `text-wrap: balance`.
- `h2`: 38px, weight 600, line-height 1.15, letter-spacing -0.015em.
- `h3`: 24px, weight 600.
- Code blocks 14.5px / 1.65 (hero command 15px / 1.6). Inline code 0.86em. Mono labels and badges 14px.
- Wordmark "Nivis": Hind 400, 34px, letter-spacing -0.01em.

**Shape and space**

- Content width 1120px, side padding 24px.
- Section vertical padding 88px (80px for the audiences section; hero 56px top, 88px bottom).
- Radii: cards 14px, code blocks 10px, buttons and badges fully rounded.
- Card padding 32px (project cards 28px, phase cards 24px).
- Gaps: 16 / 24 / 32 / 40 / 48px. Express these as spacing tokens too.

## 6. Page anatomy

All multi-column layouts use `repeat(auto-fit, minmax(min(<N>px, 100%), 1fr))` so they collapse to one column on a phone without media queries.

1. **Header.** Mark (40px) and wordmark on the left, linking to top. Nav on the right: four muted text links, a "GitHub" outline pill (1.5px `--accent` border), and a 44px round theme-switch button. The row wraps on narrow screens.
2. **Hero.** Two columns (min 420px), gap 48px, vertically centred. Left: mono badge pill, `h1`, lead (max 34em), primary button (`--warm`) plus a text link, then the one-line command as a code block. Right: the mark, up to 440px wide.
3. **Audiences** (on `--surface`, top and bottom border). `h2`, then two cards (`--ground`) side by side with title, muted lead and three bullet points. Below them two code blocks side by side, each with a small mono filename label above.
4. **Quick start** (`id="start"`). `h2` and lead, then four steps. Each step is a two-column grid (52px, rest): a 40px round number in `--warm`, then title, optional text (max 40em), code block and optional link.
5. **Round trip** (`id="roundtrip"`, full-width `--band-bg`). `h2` and lead, then an ordered list of four phase cards (min 230px, 1px `--band-line` border) each with a mono label "01 evaluate" and text. Below: the Nix example on the left and title, text and link on the right (min 420px).
6. **Compare** (`id="compare"`). `h2` and lead, then the table inside a horizontally scrollable, bordered, rounded box (table min-width 860px). The Nivis column has `--accent-soft` background and weight 600. Row headers weight 500. Use real `<th scope>` elements. Link below.
7. **Projects** (`id="projects"`, on `--surface`). `h2` and lead, then a grid of six cards (min 320px, `--ground`). Each whole card is one link: 64px mark variant, mono repo name with a small outlined status pill, and a muted description.
8. **Go deeper.** Two columns: `h2`, text and primary button on the left; on the right a two-column list of six doc links, each with a top divider.
9. **Footer.** Top border. Small mark (26px) with name, license and domain on the left; text links on the right.

Buttons and links must have visible `:hover` and `:focus-visible` states (the mockup only defines link hover: color changes to `--ink`).

## 7. The mark

The Nivis mark is drawn from the polar curve the project uses as the basis for all its marks:

```
r(θ) = a + b · cos(kθ),   with   b = a · amp / (k² + 1)
```

`amp = 1` gives nearly flat sides; larger values make the lobes more pronounced. A layer is that curve sampled at 120 points, rotated by `rot` degrees, drawn as a closed SVG path in a `-100 -100 200 200` viewBox.

Generate the paths **at build time** in `partials/mark.html` from parameters in `data/marks.yaml`. Do not ship JavaScript for this and do not hand-paste path data.

The main mark has five layers, back to front:

| Layer | a | rot | fill | opacity |
|---|---|---|---|---|
| 1 | 84 | -24° | `--mark-a` | 0.3 |
| 2 | 80 | -11° | `--mark-b` | 0.3 |
| 3 | 78 | 12° | `--mark-a` | 0.3 |
| 4 | 74 | 25° | `--mark-b` | 0.3 |
| core | 64 | 0° | `--mark-core` | 1 |

Main mark: `k = 3`, `amp = 1`. The header uses the same five layers at 40px; the footer uses layers 2, 3 and core at 26px.

Project marks have three layers: `a = 84` at `rot - 16°` (`--mark-a`, 0.35), `a = 80` at `rot + 16°` (`--mark-b`, 0.35), and core `a = 64` at `rot`.

```yaml
# data/marks.yaml
nivis:            { k: 3, amp: 1.0, rot: 0 }
registry:         { k: 4, amp: 1.2, rot: 45 }
tunnel:           { k: 2, amp: 1.6, rot: 0 }
demos:            { k: 5, amp: 1.4, rot: -18 }
tunnel-provider:  { k: 2, amp: 1.6, rot: 90 }
hcloudimage:      { k: 3, amp: 1.8, rot: 180 }
```

The per-project parameters are provisional; the maintainer may replace them. The mark colors are a proposal too: the original logo is a single grey (`#4d4d4d`) with translucent layers. Keep fills as CSS custom properties so this can change in one place.

Also generate a favicon (SVG) from the main mark.

## 8. Light and dark mode

- Default follows the system (`prefers-color-scheme`).
- The header button toggles between light and dark, sets `data-theme` on `<html>`, and stores the choice in `localStorage`.
- A tiny inline script in `<head>` applies the stored choice before first paint, to avoid a flash.
- Without JavaScript the site still follows the system setting; hide the button in that case.
- The button is a real `<button>` with an `aria-label` from `i18n/en.yaml`.

## 9. Syntax highlighting

- Use Hugo's built-in Chroma highlighter with **CSS classes** (`noClasses: false`), not inline styles.
- Write `assets/css/syntax.css` by hand, mapping Chroma's token classes onto the five `--tok-*` / `--code-*` tokens: keywords, strings, functions and builtins, literals (booleans and numbers), comments. Everything else stays `--code-ink`.
- Languages used: `nix`, `hcl`, `console`.
- In console snippets the `$ ` prompt and trailing `#` comments are dimmed (`--code-dim`), and the prompt should not be selectable when copying.
- The mockup colors `lib.mkResource`, `lib.mkProvider`, `lib.toIR`, `lib.str` and `bucket.refAttr` as functions. Chroma's Nix lexer may not classify them that way. Accept what the lexer gives; do not add markup to snippets to force it.
- Code blocks scroll horizontally on overflow and never wrap.
- Optional, if cheap: a copy button on each code block (progressive enhancement, label from `i18n`).

## 10. Quality bar

- Semantic HTML: one `h1`, sections labelled by their headings, `nav` with a label, lists as lists, the table as a real table.
- A skip link to main content.
- Text contrast at least 4.5:1 in both modes (3:1 for text 24px and larger). Touch targets at least 44px.
- Works from 360px wide upward with no horizontal page scroll. Only code blocks and the table scroll, inside their own boxes.
- Respect `prefers-reduced-motion` (smooth scrolling off).
- `<head>`: title, description, canonical URL, Open Graph and Twitter card tags, and a generated social image if feasible.
- Fonts: woff2, `font-display: swap`, preload the two most used weights.
- CSS bundled, minified and fingerprinted through Hugo Pipes. No unused framework code.
- Target Lighthouse scores of 95+ for performance, accessibility and best practices.

## 11. Acceptance checklist

- [ ] `nix develop -c hugo server` serves the site; `hugo --minify` builds into `public/` with no warnings.
- [ ] No copy in `layouts/`. Search for any literal English word in templates: none except in comments.
- [ ] No `style=""` attributes anywhere in the generated HTML.
- [ ] No color, font or size value in `content/`, `data/` or `snippets/`.
- [ ] No color value in CSS outside `tokens.css`.
- [ ] Changing the order of `sections` in `content/_index.md` reorders the page.
- [ ] Adding a project to `data/home/projects.yaml` and `data/marks.yaml` adds a card with a generated mark, with no template change.
- [ ] Light, dark and system modes all work; the choice persists across reloads without a flash.
- [ ] All seven snippets render highlighted and match the files in `snippets/` byte for byte.
- [ ] The page is usable with keyboard only and at 360px width.
- [ ] `amplify.yml` builds with the pinned Hugo version and publishes `public/`.
- [ ] README explains: how to run locally, where content lives, where tokens live, how to add a section or a project.

## 12. Open points for the maintainer

Do not decide these yourself; list them in the PR description.

1. Verify code samples and comparison table against the repositories.
2. Confirm hosting (Amplify assumed).
3. Confirm the colored mark versus the original grey logo.
4. Confirm or replace the per-project mark parameters.
5. Whether the site should grow beyond one page (docs, blog). The structure above allows it but does not build it.
