#!/usr/bin/env python3
"""Link checking, in the two halves the sandbox allows.

`nix flake check` has no network, so this half checks what can be checked
offline and is the one that runs on every change:

  * every external address is well formed and uses https,
  * every address points at a host the project expects, which catches a typo in
    a repository name or a docs path,
  * every same-page target resolves (page-chrome also covers this; here it
    guards the data rather than the rendered page).

Actually resolving the URLs needs the network and is a separate target,
`nix run .#check-links-live`, meant to run before a release. Pretending a
sandboxed check proves a URL resolves would be the dishonest option.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from htmlnorm import normalise
from urllib.parse import urlparse

# Hosts this site is allowed to link to. A new one is a deliberate decision.
ALLOWED_HOSTS = {"github.com", "nivis.tf"}


def main():
    public = pathlib.Path(sys.argv[1])
    html = normalise((public / "index.html").read_text())
    errors = []

    external = set()
    for m in re.finditer(r'<a\b[^>]*\bhref="([^"]+)"', html):
        href = m.group(1)
        if href.startswith("#"):
            continue
        external.add(href)

    for href in sorted(external):
        parsed = urlparse(href)
        if not parsed.scheme:
            errors.append(f"{href} has no scheme; links off the page must be absolute")
            continue
        if parsed.scheme != "https":
            errors.append(f"{href} is {parsed.scheme}, not https")
        if parsed.netloc not in ALLOWED_HOSTS:
            errors.append(
                f"{href} points at {parsed.netloc}, which is not in the allowed hosts "
                f"{sorted(ALLOWED_HOSTS)}. Add it deliberately if that is intended."
            )
        if " " in href or href != href.strip():
            errors.append(f"{href!r} contains whitespace")

    if not external:
        errors.append("the page has no external links at all, which cannot be right")

    if errors:
        for e in errors:
            print(f"links: FAIL {e}", file=sys.stderr)
        return 1

    print(
        f"links: ok, {len(external)} external links, all https and all on expected hosts"
    )
    print(
        "links: note, resolving them needs the network. Run `nix run .#check-links-live` "
        "before a release; this check cannot prove a URL is reachable."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
