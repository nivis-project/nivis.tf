#!/usr/bin/env python3
"""Write openspec-link into a bean's front matter.

beans rewrites the whole file on every update and drops front-matter keys it
does not know about, so this has to run AFTER the last beans write. That is the
only ordering in which the link survives; writing it before `beans update`
silently loses it.
"""
import pathlib
import re
import sys

if len(sys.argv) != 3:
    sys.exit("usage: link-bean.py <bean-file> <archive-path>")

path = pathlib.Path(sys.argv[1])
link = sys.argv[2]
text = path.read_text()

head, sep, body = text.partition("\n---\n")
if not sep:
    sys.exit(f"link-bean: {path} has no front matter")

if re.search(r"^openspec-link:", head, re.M):
    head = re.sub(r"^openspec-link:.*$", f"openspec-link: {link}", head, flags=re.M)
else:
    head = head.rstrip("\n") + f"\nopenspec-link: {link}"

path.write_text(head + sep + body)
