#!/usr/bin/env bash
set -euo pipefail
exec python3 "${1:-.}/tests/checks/snippets.py" "${1:-.}"
