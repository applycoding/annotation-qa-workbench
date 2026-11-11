#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
expected=cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
actual=$(sha256sum LICENSE | awk '{print $1}')
test "$actual" = "$expected"
test "$(wc -c < LICENSE)" = "11358"
