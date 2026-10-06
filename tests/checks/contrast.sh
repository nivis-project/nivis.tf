#!/usr/bin/env bash
set -euo pipefail
exec python3 "${1:-.}/tests/checks/contrast.py" "${1:-.}"
