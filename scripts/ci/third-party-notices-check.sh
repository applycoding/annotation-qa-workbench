#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
canonical="$ROOT/THIRD_PARTY_NOTICES.md"
public="$ROOT/web/public/THIRD_PARTY_NOTICES.md"

test -f "$canonical"
test -f "$public"
cmp -s "$canonical" "$public"

if [[ -f "$ROOT/web/dist/THIRD_PARTY_NOTICES.md" ]]; then
  cmp -s "$canonical" "$ROOT/web/dist/THIRD_PARTY_NOTICES.md"
fi
