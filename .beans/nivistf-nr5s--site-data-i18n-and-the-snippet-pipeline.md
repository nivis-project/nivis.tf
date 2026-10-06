---
# nivistf-nr5s
title: Site data, i18n and the snippet pipeline
status: completed
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:58:05Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-0ro9
openspec-link: openspec/changes/archive/2026-10-06-site-data-and-snippets
---

The data and snippet files every later section epic reads from. Create them in
one pass so the sections can be built in any order.

## Scope

- `data/site.yaml`, exactly as the briefing gives it.
- `data/home/` with `hero.yaml`, `audiences.yaml`, `quickstart.yaml`,
  `roundtrip.yaml`, `compare.yaml`, `projects.yaml`, `docs.yaml`.
- `data/marks.yaml`.
- `i18n/en.yaml` with the skip link text, the theme switch aria-label, the
  copy button label and the nav label.
- `snippets/` with all seven files, byte for byte as the briefing gives them.
- A `doc:` link resolves to `<docs_base>/<doc>`; an `href:` link is used as is.
  Implement that resolution once, in a partial or a template function.

## Done when

- [ ] A test asserts every rendered code block matches its file in `snippets/`
      byte for byte
- [ ] A test covers both link forms
- [ ] No HTML and no style value appears in any of these files

## Briefing

Section 4.

## Summary of Changes

Shipped as OpenSpec change `site-data-and-snippets`, capability `site-content`.

The briefing's approved copy is now in the repository: `data/site.yaml`, seven
files under `data/home/`, `data/marks.yaml`, and all seven snippets. The five
section epics are now pure rendering work.

`partials/link.html` is the only reader of `docs_base`. Both link forms appear
in four sections, so resolving them per-section would hard-code the base four
times and moving the documentation would be a four-file edit with one forgotten.

A real defect found and fixed: `nix fmt` was rewriting the approved copy.
`snippets/` holds three `.nix` files; `flake.nix` is a complete flake whose
exact line breaks are what the page shows a reader, and `roundtrip-note.nix` is
a fragment that is not valid Nix at all. The formatter reflowed the first and
errored on the second. Both are invisible failures from a reader's point of
view. The formatter now skips `snippets/`, and `snippets-unformatted` proves the
exclusion works by running the formatter and comparing bytes, rather than
inspecting the formatter's source for a flag it might have and ignore.

The orphan check runs in both directions deliberately. That every reference
resolves is the obvious half; that every file is referenced is the half that
rots silently, because a snippet nobody references is either dead weight or a
sample somebody edited believing it was on the page.

Seven probes, all caught: a dangling reference, an orphan file, an HTML tag in
data, a color value in data, a project naming an undeclared mark, and both link
forms plus a moved docs base.

A mistake worth recording: the probe proving `snippets-unformatted` bites ran
the unexcluded formatter against the REAL tree and corrupted
`snippets/flake.nix`. The restore then failed silently, because `jj file
restore` is not a subcommand. It was caught by diffing against a backup.
Destructive probes belong on a copy.

Not covered, and recorded in README.md so it is visible: the code samples and
the comparison table are unverified against the real repositories. The gate
proves they render faithfully, not that they are true. The briefing names this
as a maintainer task and no test here can stand in for it.
