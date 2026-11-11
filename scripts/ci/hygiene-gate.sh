#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

probe=$(mktemp)
printf 'the box\n' >"$probe"
if ! grep -P 'the box' "$probe" >/dev/null; then
  echo "grep -P probe failed" >&2
  exit 2
fi
rm -f "$probe"

python3.12 - <<'PY' >/tmp/hygiene-pattern.txt
from pathlib import Path
parts = []
for line in Path("tests/hygiene_codepoints.txt").read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    b = bytes(int(x, 16) for x in line.split())
    parts.append(b.decode("utf-8", errors="strict"))
print("|".join(parts))
PY

mapfile -t files < <(git ls-files)
text_files=()
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  if file -b "$f" | grep -qi text; then
    text_files+=("$f")
  fi
done

assistant_pat=$(cat /tmp/hygiene-pattern.txt)
for f in "${text_files[@]}"; do
  if grep -P '[\x{2014}\x{2013}\x{2212}]' "$f" >/dev/null 2>&1; then
    echo "typographic dash in $f" >&2
    exit 1
  fi
  case "$f" in
    LICENSE | requirements.lock | requirements.in | tests/hygiene_codepoints.txt)
      continue
      ;;
    scripts/ci/*)
      continue
      ;;
  esac
  if grep -P -i "$assistant_pat" "$f" >/dev/null 2>&1; then
    echo "assistant token in $f" >&2
    exit 1
  fi
done

exit 0
