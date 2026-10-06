#!/usr/bin/env python3
"""Emit the --ground token values the end-to-end suite compares against.

These were once written out in flake.nix with a comment claiming they came from
data/tokens.yaml "so there is one source". They did not: they were a copy, and
they drifted the first time the palette changed. The e2e suite then refused to
classify either palette, which is the right failure but the wrong cause.

Reading them here means the claim is true.
"""
import json
import pathlib
import sys

import yaml

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
data = yaml.safe_load((root / "data" / "tokens.yaml").read_text())
ground = next(c for c in data["colors"] if c["name"] == "ground")
print(json.dumps({"ground": {"light": ground["light"], "dark": ground["dark"]}}))
