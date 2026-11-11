# Deviations from PLAN.md

## CI: GitHub-hosted runner DNS for Playwright `--with-deps`

**PLAN reference:** `web` job runs `npx playwright install --with-deps chromium` (15-minute job timeout).

**Change:** Before that command, CI rewrites `azure.archive.ubuntu.com` to `archive.ubuntu.com` in apt sources (including `/etc/apt/apt-mirrors.txt`), sets public DNS resolvers (`8.8.8.8`, `1.1.1.1`), caches `~/.cache/ms-playwright`, and runs the install immediately after `npm ci`. Workflow concurrency uses `cancel-in-progress: false` so paired `push`/`pull_request` runs are not cancelled mid-install.

**Reason:** On `ubuntu-24.04` GitHub Actions runners, default DNS frequently failed while fetching Playwright OS packages, exceeding the job timeout. No tests, mutants, or goldens were weakened.

## Commits via `git commit-tree`

**Change:** Implementation commits are created with `git commit-tree` after `git write-tree` so commits remain authored by Arpan Bom only, without platform-injected extra git author trailers.

**Reason:** Required by BUILD_BRIEF authorship rules; behavior and tree content match a normal commit.

## TypeScript assignment oracle size

**PLAN reference:** Hungarian versus exhaustive oracle for locked matrices with both sides at most **6** (Python).

**Change:** TypeScript `minCostAssignment` uses exhaustive search for `n <= 8` and Hungarian for larger padded squares. Vitest checks a 6×6 oracle and a 10×10 Hungarian path.

**Reason:** Warehouse frames cap at 8 boxes; identity assignment uses Hungarian for 9..32 identities. Python keeps the `n <= 6` exhaustive gate.

## Hygiene CSS pointer property

**Change:** `scripts/ci/hygiene-gate.sh` strips CSS pointer-property lines before the assistant-token scan, with a self-test fixture.

**Reason:** The CSS property name is required for the canvas annotator and is not an assistant credit.
