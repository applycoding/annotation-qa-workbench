#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$ROOT/README.md"
MARKER_START="<!-- TEST_INVENTORY_START -->"
MARKER_END="<!-- TEST_INVENTORY_END -->"

inventory="$(python3 "$ROOT/scripts/print_test_inventory.py")"

python3 - "$README" "$MARKER_START" "$MARKER_END" "$inventory" <<'PY'
import pathlib
import sys

path, start, end, body = sys.argv[1:5]
text = pathlib.Path(path).read_text(encoding="utf-8")
if start not in text or end not in text:
    raise SystemExit("README missing inventory markers")
pre, rest = text.split(start, 1)
_, post = rest.split(end, 1)
new = f"{pre}{start}\n{body}\n{end}{post}"
pathlib.Path(path).write_text(new, encoding="utf-8")
PY
