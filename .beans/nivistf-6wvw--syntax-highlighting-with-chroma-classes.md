---
# nivistf-6wvw
title: Syntax highlighting with Chroma classes
status: todo
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T13:02:41Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-gxj4
---

Chroma with CSS classes, mapped by hand onto the five token colors. No inline
styles, no markup added to the snippet files.

## Scope

- `assets/css/syntax.css`, written by hand, mapping Chroma's token classes onto
  keywords, strings, functions and builtins, literals, and comments. Everything
  else stays `--code-ink`.
- Languages: `nix`, `hcl`, `console`.
- In console snippets the `$ ` prompt and trailing `#` comments render in
  `--code-dim`, and the prompt is not selectable when copying.
- Code blocks are dark in both themes, scroll horizontally on overflow, and
  never wrap.
- Optional if cheap: a copy button per code block as progressive enhancement,
  label from i18n.

## Done when

- [ ] All seven snippets render highlighted
- [ ] Selecting and copying a console block yields the command without the
      prompt
- [ ] No inline style attribute appears in any highlighted block
- [ ] A test asserts the five token classes are all exercised by at least one
      snippet

## Note

The mockup colors `lib.mkResource`, `lib.mkProvider`, `lib.toIR`, `lib.str` and
`bucket.refAttr` as functions. Chroma's Nix lexer may not agree. Accept what the
lexer gives. Do not add markup to the snippets to force it.

## Briefing

Section 9.
