---
# nivistf-6wvw
title: Syntax highlighting with Chroma classes
status: completed
type: epic
priority: normal
created_at: 2026-10-06T13:02:12Z
updated_at: 2026-10-06T14:29:48Z
parent: nivistf-zsjy
blocked_by:
    - nivistf-nr5s
    - nivistf-gxj4
openspec-link: openspec/changes/archive/2026-10-06-syntax-highlighting
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

## Summary of Changes

Shipped as OpenSpec change `syntax-highlighting`, capability `code-presentation`.

`assets/css/syntax.css` maps Chroma's token classes onto the `--tok-*` and
`--code-*` tokens, written by hand because Chroma's generated stylesheet would
put colour values outside tokens.css. The mapping was built from what the seven
samples actually emit, measured rather than transcribed, with neighbouring
classes included so a future sample containing a number or a single-quoted
string does not suddenly render as plain text.

The finding worth keeping: `--tok-func` has a rule and nothing triggers it.
Across all seven samples Chroma emits no function or builtin token at all. The
briefing predicted exactly this and said to accept what the lexer gives rather
than adding markup to force it.

The bean's original acceptance item said "a test asserts the five token classes
are all exercised by at least one snippet". That test cannot honestly pass. The
options were to delete the token, add markup to the samples, or keep the rule
and report the gap. Deleting discards a value the briefing's palette defines;
adding markup breaks the guarantee that a sample renders byte for byte from its
file. So the check prints on every run:

    syntax: note, --tok-func is mapped but no sample currently produces it

A visible gap is worth more than a green check that means less than it looks
like it means.

The check also asserts SPECIFIC Chroma classes appear in SPECIFIC languages, so
a Hugo bump that reclassifies a token fails the gate rather than silently
restyling the page.

The shell prompt is excluded from a copied selection with `user-select: none`
scoped to the prompt token, so dragging across a sample and pasting gives a
runnable command. The check verifies the scoping too: applying it to the whole
block would make the entire sample uncopyable, which is the obvious wrong fix.
Whether a real selection excludes it is browser behaviour and belongs to
nivistf-c6h5.

Six probes caught: a reclassified token, an inline style, an unmapped class, a
selectable prompt, an unselectable block, a wrapping rule.

No copy button. The briefing lists it as optional, and excluding the prompt from
a selection gives most of the benefit without shipping more JavaScript than the
theme switch.
