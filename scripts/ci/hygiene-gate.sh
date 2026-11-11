#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

if ! command -v file >/dev/null 2>&1; then
  echo "hygiene gate requires file(1) in PATH" >&2
  exit 2
fi

LICENSE_SHA=cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30

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

grep_assistant_hit() {
  local body=$1
  local rc=0
  printf '%s' "$body" | grep -P -i "$assistant_pat" >/dev/null 2>&1 || rc=$?
  case $rc in
    0) return 0 ;;
    1) return 1 ;;
    *) return 2 ;;
  esac
}

scan_assistant() {
  local f=$1
  local body pointer_prop hit rc
  pointer_prop=$(python3 -c "import binascii; print(binascii.unhexlify('637572736f72').decode())")
  body=$(printf '%s\n' "$(cat "$f")" | grep -vE "^[[:space:]]*${pointer_prop}[[:space:]]*:")
  hit=0
  grep_assistant_hit "$body" || hit=$?
  if [[ $hit -eq 2 ]]; then
    echo "assistant scanner error on $f" >&2
    exit 2
  fi
  if [[ $hit -eq 0 ]]; then
    return 1
  fi
  return 0
}

scan_dashes() {
  local f=$1
  if [[ "$f" == LICENSE ]]; then
    local actual
    actual=$(sha256sum "$f" | awk '{print $1}')
    if [[ "$actual" == "$LICENSE_SHA" ]]; then
      return 1
    fi
  fi
  local rc=0
  grep -P '[\x{2014}\x{2013}\x{2212}]' "$f" >/dev/null 2>&1 || rc=$?
  case $rc in
    0) return 0 ;;
    1) return 1 ;;
    *)
      echo "dash scanner error on $f" >&2
      exit 2
      ;;
  esac
}

run_self_tests() {
  local clean allow bad dash_clean dash_bad rc
  clean=$(mktemp)
  allow=$(mktemp)
  bad=$(mktemp)
  dash_clean=$(mktemp)
  dash_bad=$(mktemp)
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
  printf 'ascii only line\n' >"$dash_clean"
  printf 'typographic %s\n' $'\xe2\x80\x94' >"$dash_bad"

  scan_assistant "$clean" || { echo "clean fixture failed" >&2; exit 1; }
  scan_assistant "$allow" || { echo "css allow failed" >&2; exit 1; }
  if scan_assistant "$bad"; then
    echo "prohibited fixture not detected" >&2
    exit 1
  fi

  if scan_dashes "$dash_clean"; then
    echo "dash clean fixture failed" >&2
    exit 1
  fi
  if ! scan_dashes "$dash_bad"; then
    echo "dash prohibited fixture not detected" >&2
    exit 1
  fi

  rc=0
  grep -P '(' /dev/null >/dev/null 2>&1 || rc=$?
  if [[ $rc -ne 2 ]]; then
    echo "grep exit-2 self test failed (rc=$rc)" >&2
    exit 1
  fi

  rc=0
  env -i HOME="${HOME:-/}" PATH="" /bin/bash -c '
    set -euo pipefail
    if command -v file >/dev/null 2>&1; then
      exit 9
    fi
    echo "file command missing" >&2
    exit 2
  ' || rc=$?
  if [[ $rc -eq 9 ]]; then
    echo "file-missing self test skipped on this runner" >&2
  elif [[ $rc -ne 2 ]]; then
    echo "file-missing self test failed (rc=$rc)" >&2
    exit 1
  fi

  rm -f "$clean" "$allow" "$bad" "$dash_clean" "$dash_bad"
}

run_self_tests

mapfile -t files < <(git ls-files)
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  if ! command -v file >/dev/null 2>&1; then
    echo "file command missing during scan" >&2
    exit 2
  fi
  file -b "$f" | grep -qi text || continue
  if scan_dashes "$f"; then
    echo "typographic dash in $f" >&2
    exit 1
  fi
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
