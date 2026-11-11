#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

wf=.github/workflows/ci.yml
good='uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1'
if ! grep -qF "$good" "$wf"; then
  echo "missing valid pin" >&2
  exit 1
fi
if grep -E 'uses:[[:space:]]*[^@[:space:]]+@[vV][0-9]' "$wf" >/dev/null; then
  echo "floating tag found" >&2
  exit 1
fi
if grep -E 'uses:[[:space:]]*[^@[:space:]]+@[0-9a-f]{1,39}[[:space:]]*$' "$wf" >/dev/null; then
  echo "short sha found" >&2
  exit 1
fi
if grep -E 'uses:[[:space:]]*[^@[:space:]]+$' "$wf" >/dev/null; then
  echo "unpinned uses" >&2
  exit 1
fi

# fixtures
tmpdir=$(mktemp -d)
cat >"$tmpdir/bad.yml" <<'YML'
uses: actions/checkout@v4
YML
if ! grep -E 'uses:[[:space:]]*[^@[:space:]]+@[vV][0-9]' "$tmpdir/bad.yml" >/dev/null; then
  echo "scanner cannot catch bad pin" >&2
  exit 1
fi

exit 0
