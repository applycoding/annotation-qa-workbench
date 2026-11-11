#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

wf=.github/workflows/ci.yml

validate_file() {
  local file=$1
  local line
  while IFS= read -r line; do
    [[ "$line" =~ uses: ]] || continue
    if [[ ! "$line" =~ uses:[[:space:]]+[^@[:space:]]+@[0-9a-f]{40}[[:space:]]+# ]]; then
      echo "invalid pin line: $line" >&2
      return 1
    fi
  done < <(grep -E 'uses:' "$file" || true)
}

validate_file "$wf"

tmpdir=$(mktemp -d)
write() {
  printf '%s\n' "$1" >"$tmpdir/$2"
}

write 'uses: actions/checkout@v4' bad-tag.yml
write 'uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1' bad-nocomment.yml
write 'uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1' good.yml
write 'uses: actions/checkout@abc # v7' short.yml
write 'uses: actions/checkout' unpinned.yml

expect_fail() {
  if validate_file "$tmpdir/$1" 2>/dev/null; then
    echo "expected failure for $1" >&2
    exit 1
  fi
}

expect_fail bad-tag.yml
expect_fail bad-nocomment.yml
expect_fail short.yml
expect_fail unpinned.yml
validate_file "$tmpdir/good.yml"

exit 0
