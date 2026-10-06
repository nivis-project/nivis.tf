---
# nivistf-rs19
title: Separation invariants as executable checks
status: todo
type: epic
priority: high
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-a5q8
blocked_by:
    - nivistf-7mto
    - nivistf-0ro9
---

Make the one hard architectural rule a thing the build enforces, not a thing
reviewers remember.

## Scope

Each of these is a test that fails the build:

- No literal English copy in `layouts/`. Scan every template for word
  characters outside Go template actions, HTML tag names, attribute names and
  comments. Maintain an explicit allowlist and keep it short.
- No `style=""` attribute anywhere in the generated HTML.
- No color, font or size value in `content/`, `data/` or `snippets/`.
- No color value in any CSS file outside `tokens.css`.
- No `<script>` in the output except the theme switch and its inline
  no-flash preamble.
- Every snippet referenced from `data/` exists in `snippets/`, and every file
  in `snippets/` is referenced.

## Done when

- [ ] All six checks run under `nix flake check`
- [ ] Each check has a negative fixture proving it actually catches the
      violation
- [ ] The allowlist for the copy scan is documented in `docs/TESTING.md`

## Briefing

Sections 1 and 11.
