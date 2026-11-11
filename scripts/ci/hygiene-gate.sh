#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

probe=$(mktemp)
probe_phrase=$(python3 -c "
from pathlib import Path
line = Path('tests/hygiene_codepoints.txt').read_text().splitlines()[9].strip()
print(bytes(int(x,16) for x in line.split()).decode())
")
printf '%s\n' "$probe_phrase" >"$probe"
if ! grep -P "$probe_phrase" "$probe" >/dev/null; then
  echo "grep -P probe failed" >&2
  exit 2
fi
rm -f "$probe"

python3 - <<'PY' >/tmp/hygiene-pattern.txt
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

assistant_pat=$(cat /tmp/hygiene-pattern.txt)

scan_assistant() {
  local f=$1
  local body pointer_prop
  pointer_prop=$(python3 -c "import binascii; print(binascii.unhexlify('637572736f72').decode())")
  body=$(printf '%s\n' "$(cat "$f")" | grep -vE "^[[:space:]]*${pointer_prop}[[:space:]]*:")
  if printf '%s' "$body" | grep -P -i "$assistant_pat" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

scan_dashes() {
  local f=$1
  local st=0
  if grep -P '[\x{2014}\x{2013}\x{2212}]' "$f" >/dev/null 2>&1; then
    return 0
  fi
  st=$?
  if [[ $st -eq 2 ]]; then
    echo "dash scanner error on $f" >&2
    exit 2
  fi
  return 1
}

run_self_tests() {
  local clean allow bad
  clean=$(mktemp)
  allow=$(mktemp)
  bad=$(mktemp)
  printf 'synthetic warehouse\n' >"$clean"
  pointer_prop=$(python3 -c "import binascii; print(binascii.unhexlify('637572736f72').decode())")
  printf '%s\n' "  ${pointer_prop}: default" >"$allow"
  printf '%s\n' 'vendor token list item' >"$bad"
  bad_token=$(python3 -c "
from pathlib import Path
line = Path('tests/hygiene_codepoints.txt').read_text().splitlines()[8].strip()
print(bytes(int(x,16) for x in line.split()).decode())
")
  printf '%s\n' "${bad_token} sample mention" >"$bad"
  scan_assistant "$clean" || { echo "clean fixture failed" >&2; exit 1; }
  scan_assistant "$allow" || { echo "css allow failed" >&2; exit 1; }
  if scan_assistant "$bad"; then
    echo "prohibited fixture not detected" >&2
    exit 1
  fi
  rm -f "$clean" "$allow" "$bad"
}

run_self_tests

mapfile -t files < <(git ls-files)
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  file -b "$f" | grep -qi text || continue
  case "$f" in
    LICENSE) ;;
    *)
      if scan_dashes "$f"; then
        echo "typographic dash in $f" >&2
        exit 1
      fi
      ;;
  esac
  case "$f" in
    LICENSE | requirements.lock | requirements.in | tests/hygiene_codepoints.txt)
      continue
      ;;
  esac
  scan_assistant "$f" || {
    echo "assistant token in $f" >&2
    exit 1
  }
done

exit 0
