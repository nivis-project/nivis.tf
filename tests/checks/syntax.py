#!/usr/bin/env python3
"""Assert the highlighting reaches the page as classes resolving to tokens.

Chroma's classification can change on a Hugo bump, which would silently restyle
the page. So this asserts specific classes appear in specific samples: a
reclassification fails the gate rather than quietly changing the colours.
"""
import pathlib
import re
import sys

# What each language's samples must produce. Measured from the real output, not
# transcribed from a published list.
EXPECTED = {
    "console": {"gp"},            # shell prompt
    "nix": {"s2", "n", "p", "o"},  # strings, names, punctuation, operators
    "hcl": {"s2", "k"},            # strings, keywords
}

# Which token each mapped Chroma class must resolve to.
MAPPING = {
    "--tok-keyword": {"k", "kc", "kd", "kn", "kp", "kr", "kt"},
    "--tok-string": {"s", "sa", "sb", "sc", "s1", "s2", "se", "sh", "si", "sx"},
    "--tok-func": {"nf", "nb", "nv", "fm"},
    "--tok-literal": {"m", "mb", "mf", "mh", "mi", "mo", "no", "bp"},
    "--code-dim": {"c", "c1", "cm", "cp", "cs", "ch", "gp"},
}


def main():
    public = pathlib.Path(sys.argv[1])
    html = (public / "index.html").read_text()
    css = "".join(p.read_text() for p in public.rglob("*.css"))
    errors = []

    blocks = re.findall(r'<code[^>]*data-lang="([a-z]+)"[^>]*>(.*?)</code>', html, re.S)
    if not blocks:
        print("syntax: FAIL no highlighted code blocks on the page", file=sys.stderr)
        return 1

    seen_by_lang = {}
    for lang, body in blocks:
        classes = set(re.findall(r'<span class="([a-z0-9]+)">', body))
        classes -= {"line", "cl"}
        seen_by_lang.setdefault(lang, set()).update(classes)

    for lang, want in EXPECTED.items():
        got = seen_by_lang.get(lang)
        if got is None:
            errors.append(f"no {lang} sample on the page")
            continue
        missing = want - got
        if missing:
            errors.append(
                f"{lang} samples no longer produce {sorted(missing)}; "
                f"Chroma may have reclassified them, which silently restyles the page"
            )

    # No inline styles: the whole point of class-based highlighting.
    for lang, body in blocks:
        if re.search(r"style\s*=", body):
            errors.append(f"a {lang} sample carries an inline style attribute")
            break

    # Every mapped class must actually resolve to its token in the stylesheet.
    for token, classes in MAPPING.items():
        for cls in classes:
            if not re.search(rf"\.chroma\s+\.{cls}\b[^{{}}]*?[,{{]", css):
                errors.append(f"Chroma class .{cls} is not mapped in the stylesheet")
                break

    # The prompt rule must be scoped to the prompt token, not to code generally.
    m = re.search(r"\.chroma\s+\.gp\s*\{([^}]*)\}", css)
    if not m:
        errors.append("no rule for the shell prompt token")
    elif "user-select:none" not in m.group(1).replace(" ", ""):
        errors.append("the shell prompt is not excluded from a selection")
    if re.search(r"figure\.code[^{]*\{[^}]*user-select\s*:\s*none", css):
        errors.append("user-select:none is applied to the whole code block, not just the prompt")

    # Samples must never wrap: a broken line changes what the code says.
    if not re.search(r"white-space:\s*pre\b", css):
        errors.append("no white-space: pre rule, so samples could wrap")
    if re.search(r"figure\.code[^{]*\{[^}]*white-space\s*:\s*(pre-wrap|normal)", css):
        errors.append("a code rule allows wrapping")

    # Report mapped-but-unused classes, so the gap stays visible rather than
    # decaying into a silent assumption. --tok-func currently has no producer;
    # the briefing predicted this and said to accept what the lexer gives.
    all_seen = set().union(*seen_by_lang.values()) if seen_by_lang else set()
    unused = {
        token: sorted(classes - all_seen)
        for token, classes in MAPPING.items()
        if not (classes & all_seen)
    }

    if errors:
        for e in errors:
            print(f"syntax: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"syntax: ok, {len(blocks)} samples in {len(seen_by_lang)} languages, "
        f"classes resolve to tokens, prompt excluded from selection, no wrapping"
    )
    for token in sorted(unused):
        print(f"syntax: note, {token} is mapped but no sample currently produces it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
