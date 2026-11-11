# Build tasks - annotation-qa-workbench

Execute in order. Follow PLAN.md. Deviate only if a pin or a test proves a step broken, or if a documented design correction from PLAN.md requires it, and record why in DEVIATIONS.md. License is **Apache-2.0**. Commit author and committer are always **Arpan Bom <applycoding@gmail.com>**. No co-author trailers. No credit to any assistant or tool in the repository.

Each task has acceptance checks. A task is done only when those checks pass. Do not loosen a gate or drop a mutant to make CI green.

## 1. Repository skeleton and license

- Create the tree in PLAN.md (empty dirs may hold `.gitkeep`).
- Fetch `https://www.apache.org/licenses/LICENSE-2.0.txt` into `LICENSE` and confirm sha256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` (11358 bytes).
- Write `NOTICE` starting with `annotation-qa-workbench, Copyright 2026 Arpan Bom`, then dependency notices (filled as pins land).
- README stub: portfolio demo, synthetic data only, simulation only, original implementations of IoU, Cohen's kappa, Krippendorff's alpha, MOTA, and IDF1, inspired by the cited papers and by the idea of annotation QA workbenches, not CVAT, not Label Studio, not a production platform, Apache-2.0, author Arpan Bom.
- `pyproject.toml` with hatchling 1.33.0, package `annotation_qa_workbench`, script `aqw`. SPDX on authored files.
- `.gitignore`: `__pycache__/`, `.venv/`, `node_modules/`, `dist/`, `artifacts/`, `.pytest_cache/`, coverage files, local Playwright output. Scene JSON fixtures are committed; rendered frames are not.

**Accept:** `sha256sum LICENSE` matches the official digest. NOTICE and README name Apache-2.0 and Arpan Bom. Criteria 21 and 22 (docs and license) have their stubs in place.

## 2. Lock Python and Node pins

- Write `requirements.in` with the direct pins in PLAN.md (pytest, pytest-cov, coverage, ruff, mypy, and hatchling 1.33.0). hatchling is also the build backend in `pyproject.toml`. pip-tools is used to generate the lock, not a runtime dependency of the package.
- Under Python 3.12, with `pip-tools==7.6.2`, run `pip-compile --generate-hashes -o requirements.lock requirements.in`. Do not pass a `--python-version` flag.
- Record hatchling and pip-tools wheel hashes in NOTICE once installed.
- `web/package.json` and `package-lock.json` with Node 26.13.0 / npm 11.20.0 and the npm pins in PLAN.md, including React 19.3.1 and `@vitejs/plugin-react` 6.3.0.

**Accept:** `pip install --require-hashes -r requirements.lock` succeeds on Python 3.12. The lock was produced by the pinned pip-tools and includes hatchling plus its resolved dependencies. The local package then installs with `--no-build-isolation --no-deps`. `npm ci` succeeds with the committed lockfile.

## 3. Geometry and assignment

- Implement `iou` and the half-open `xywh` contract exactly as in PLAN.md Decision B.
- Implement Kuhn-Munkres matching as in Decision C, with the 8-object frame cap, the 32-identity IDF1 cap, dummy padding, and the locked tie-break. Cross-check against the exhaustive oracle for n<=6.

**Accept:** Criteria 1 and 2.

## 4. Kappa, alpha, MOT, detection scores

- Implement Cohen's kappa (Decision D), nominal Krippendorff's alpha with missing values (Decision E), MOTA / `motp_mean_iou` / IDF1 (Decision F), and precision / recall / F1 at IoU 0.5.
- Do not call `motp_mean_iou` a distance MOTP. Do not claim COCO mAP.

**Accept:** Criteria 3, 4, 6, 6b, and 6c, plus the warehouse alpha cases once the scene exists (criterion 5 can land with task 5).

## 5. Scene, annotators, and goldens

- Implement `generate_warehouse_v1` and annotators A, B, C from the closed-form rules in Decision G. No RNG.
- Land a working `aqw generate` in this task (score and report may wait for task 6).
- Commit `fixtures/scenes/warehouse_v1.json` and `fixtures/expected/` scores (rationals as strings plus float64 values), including the `idf1_potential_pairs` boxes.
- CI must regenerate the scene and diff it. Do not commit rendered PNG frames.

**Accept:** Criteria 5, 7, 8, 9, 10, and 14.

## 6. Mutants, report writer, CLI

- Implement the four mutants in Decision H. Each is injected into the production scorer, the healthy control passes, the mutant returns finite values, and the named gate then fails.
- `write_report` rejects NaN. `aqw generate`, `aqw score`, and `aqw report --check --require-ci --expect-sha` behave as in PLAN.md.
- Validators recompute gates from the scene and locked annotator functions.

**Accept:** Criteria 11, 12, 13, 13b, 15, and 16.

## 7. Pages workbench and Playwright

- Vite + React + TypeScript app, `base: '/annotation-qa-workbench/'`, Canvas 2D, honesty labels, fetches via `import.meta.env.BASE_URL`.
- Working annotator UI as in Decision I (draw, edit, tabs, live scores, CI report panel).
- Copy CI `report.json` into `web/public/` before the production build. No silent sample fallback.
- TypeScript metrics match the committed goldens.
- Playwright as locked (Chromium with deps, `webServer` on the built site, 127.0.0.1, draw-the-box IoU 1, annotator A/B/C numbers, edit / delete / frame-isolation / locked-tab / empty-You checks, document title contains `synthetic data`, injected error states). Vitest must not collect Playwright specs.
- Check in `docs/demo.png` locally once. CI uploads the screenshot and does not commit it.

**Accept:** Criterion 19. `THIRD_PARTY_NOTICES.md` lists the packages actually bundled for Pages and is copied into `web/public/`.

## 8. Single workflow, honesty, authorship

- One `ci.yml` as in PLAN.md: `core`, `web` needs `core`, `pages` needs both and deploys only a main push of that SHA. SHA-pinned actions, Python 3.12, Node 26.13.0, `ubuntu-24.04`. Never `ubuntu-latest`.
- Local package installed with `--no-build-isolation --no-deps` after hashed requirements.
- `author-check` as in PLAN.md Decision J (pull-request head SHA, or push SHA). `license-bytes`. The `grep -P` typographic-dash and assistant-word check assembled from `tests/hygiene_codepoints.txt` (U+2014, U+2013, U+2212, and the hex tokens; do not flag the word "box" in "bounding box"; do not use ripgrep; fail on grep exit 2). Exclude `LICENSE` from the assistant-word half of the scan; still dash-scan it; do not edit the official Apache text. SHA-pin check that catches floating tags, short SHAs, and valid 40-hex pins. README honesty test as in criterion 21 (exact disclaimers, not a self-contradictory substring ban). Pass the checked-out SHA into the report so `git_sha` is never `unknown`.
- Coverage 80% on the locked module set, plus the negative uncovered-fixture check.
- Fill NOTICE with every direct runtime and dev dependency actually installed, including `@types/node`, `@types/react`, `@types/react-dom`, hatchling, and pip-tools. Ship `THIRD_PARTY_NOTICES.md` for redistributed bundle code. Artifact uploads use `if-no-files-found: error`. Web steps use working directory `web`.

**Accept:** Criteria 17, 18, 20, 21, and 22. CI is green and the final run on the pushed branch has **completed**.
