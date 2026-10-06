#!/usr/bin/env python3
"""Re-quote attribute values in minified HTML, so checks can match either form.

Every check builds with --minify, because that is what amplify.yml deploys.
Hugo's minifier drops the quotes around an attribute value that contains no
space, so `class="project-card"` becomes `class=project-card` while
`class="card stack audience-card"` keeps them.

That means a pattern written against readable markup matches one and not the
other, which is how several checks ended up asserting against an artifact that
never ships. Normalising once here is safer than patching every pattern, where
missing one is silent.

Used as a filter (`htmlnorm.py < in > out`) or as `normalise(text)`.
"""
import re
import sys

# An attribute inside a tag whose value is unquoted: name=value, where value
# runs to the next space or the closing bracket. Deliberately anchored to tag
# context so text content is never touched.
TAG = re.compile(r"<[a-zA-Z/!][^>]*>")
UNQUOTED_ATTR = re.compile(r"""(\s[a-zA-Z_:][-a-zA-Z0-9_:.]*)=(?!["'])([^\s"'=<>`]+)""")


def normalise(html: str) -> str:
    def fix_tag(m):
        return UNQUOTED_ATTR.sub(lambda a: f'{a.group(1)}="{a.group(2)}"', m.group(0))

    return TAG.sub(fix_tag, html)


if __name__ == "__main__":
    sys.stdout.write(normalise(sys.stdin.read()))
