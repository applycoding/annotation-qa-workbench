#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]]; then
  sha="${GITHUB_EVENT_PULL_REQUEST_HEAD_SHA:-}"
  if [[ -z "$sha" ]]; then
    sha=$(jq -r .pull_request.head.sha "$GITHUB_EVENT_PATH")
  fi
  git fetch origin "$sha" --depth=1 2>/dev/null || true
else
  sha="${GITHUB_SHA}"
fi

author=$(git show -s --format='%an <%ae>' "$sha")
committer=$(git show -s --format='%cn <%ce>' "$sha")
body=$(git show -s --format='%B' "$sha")
test "$author" = "Arpan Bom <applycoding@gmail.com>"
test "$committer" = "Arpan Bom <applycoding@gmail.com>"
echo "$body" > /tmp/commit-meta.txt
trailer=$(python3 -c "print(bytes.fromhex('63 6f 2d 61 75 74 68 6f 72 65 64 2d 62 79').decode())")
if grep -qi "$trailer" /tmp/commit-meta.txt; then
  echo "commit trailer rejected" >&2
  exit 1
fi
