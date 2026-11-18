#!/usr/bin/env python3
import pathlib
import re
import sys

FORBIDDEN = "google-fonts"
DRV = re.compile(rb"/nix/store/[0-9a-z]{32}-[^\"/]+\.drv")


def walk(roots):
    seen, todo = set(), list(roots)
    while todo:
        drv = todo.pop()
        if drv in seen:
            continue
        seen.add(drv)
        todo.extend(m.decode() for m in DRV.findall(pathlib.Path(drv).read_bytes()))
    return seen


def main():
    roots = sys.argv[1:]
    if not roots:
        sys.exit("font-sources: no derivations given")
    seen = walk(roots)
    hits = sorted(d for d in seen if FORBIDDEN in pathlib.Path(d).name)
    if hits:
        print(f"font-sources: FAIL {FORBIDDEN} is a build input:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        return 1
    print(f"font-sources: ok, {len(seen)} derivations, none is {FORBIDDEN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
