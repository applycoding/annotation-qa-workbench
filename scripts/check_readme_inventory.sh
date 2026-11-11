#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$ROOT/README.md"
MARKER_START="<!-- TEST_INVENTORY_START -->"
MARKER_END="<!-- TEST_INVENTORY_END -->"

expected="$(python3 "$ROOT/scripts/print_test_inventory.py")"
actual="$(python3 - "$README" "$MARKER_START" "$MARKER_END" <<'PY'
import pathlib
import sys

path, start, end = sys.argv[1:4]
text = pathlib.Path(path).read_text(encoding="utf-8")
if start not in text or end not in text:
    raise SystemExit("README missing inventory markers")
_, rest = text.split(start, 1)
body, _ = rest.split(end, 1)
print(body.strip())
PY
)"

if [ "$actual" != "$expected" ]; then
  echo "README test inventory is stale; run scripts/sync_readme_inventory.sh" >&2
  echo "--- expected ---" >&2
  printf '%s\n' "$expected" >&2
  echo "--- actual ---" >&2
  printf '%s\n' "$actual" >&2
  exit 1
fi
