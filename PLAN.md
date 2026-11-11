# annotation-qa-workbench - v1 plan

Revised 2026-11-11 after independent review, independent version, URL, license, and math checks, and a recorded prototype of the locked metrics. Outbound license is Apache-2.0. Planning only; this document does not create a public repo or implementation.

`gh repo list applycoding --limit 200` on 2026-11-11 shows no `applycoding/annotation-qa-workbench`.

## Goal

Public portfolio demo for Arpan Bom (idea #11): a browser workbench to annotate and QA synthetic robot-vision boxes and tracks, with agreement scores.

A static GitHub Pages app at base `/annotation-qa-workbench/` lets a visitor draw and edit axis-aligned boxes, assign classes and track ids, and see live scores against a locked ground-truth sequence and against other annotators. A Python package, `annotation_qa_workbench`, with console script `aqw`, is the scoring engine used in CI to write a schema-v1 report. TypeScript reimplements the same formulas for live scoring. Both must match committed golden fixtures within `1e-12`. The page is a real working annotator, and it also displays the recorded CI report. It does not train a model and does not download external datasets.

This is an original implementation of well-known methods (intersection-over-union, Cohen's kappa, Krippendorff's alpha, CLEAR MOT-style MOTA, and IDF1), inspired by the cited papers and by the idea of annotation QA workbenches such as CVAT and Label Studio. It is not those products, not a production labelling platform, and not a study of real annotators. Data are synthetic only: colored rectangles on a drawn floor grid, with known ground truth. No real robot images, no customer data, and no COCO, ImageNet, or Open Images downloads.

Git author and committer: **Arpan Bom <applycoding@gmail.com>**. No co-author trailers. No credit to any assistant or tool in the README, NOTICE, or commits.

## Scope

In v1:

- One locked 20-frame warehouse scene, three classes (`robot`, `pallet`, `cone`), three locked annotator traces (A, B, C).
- Metrics: IoU, precision / recall / F1 at IoU 0.5, Cohen's kappa on matched class labels, nominal Krippendorff's alpha with missing values, MOTA, `motp_mean_iou`, IDF1.
- Python CLI (`generate`, `score`, `report`), Vitest parity, React + Canvas workbench, Playwright as a real gate, one CI workflow that deploys tested Pages output from `main`.

Do not depend on, submodule, vendor, or copy these:

- applycoding/ros2-vision-tracking-demo: ROS 2 Humble YOLO plus a ByteTrack-style tracker. Not an annotation QA workbench, no multi-annotator agreement metrics, no static Pages annotator.
- applycoding/edge-vision-detector, applycoding/flutter-on-device-vision, applycoding/edge-yolo-tensorrt: detectors, not QA workbenches.
- applycoding/rosbag-eval-bench: offline bag metric regression, not box annotation.
- applycoding/lidar-shape-classifier-ros2: LiDAR clusters, not image-box QA.
- applycoding/rag-llm-eval-demo and applycoding/llm-eval-observability: language evals, not vision annotation.

CVAT and Label Studio are idea-only citations. Do not vendor or translate their sources.

## Architecture

### Decision A - two implementations, one golden

Installable package `annotation_qa_workbench`, console script `aqw`, build backend **hatchling 1.33.0**. Core CI uses the Python standard library plus the pinned test and lint tools only. No NumPy, no SciPy, no OpenCV, no Pillow, no ROS, and no model inference in v1.

TypeScript metrics live under `web/src/metrics`. Committed files in `fixtures/expected/` are the authority. `pytest` and `vitest` both read them. A stored `pass` flag in a report is not authority: validators recompute scores from the scene and the locked annotator functions.

### Decision B - geometry

Image coordinates: origin at the top left, x right, y down, units in pixels, float64. A box is `xywh`, half-open `[x, x+w) x [y, y+h)`. Area is `max(0, w) * max(0, h)`.

```
inter_w = max(0, min(ax+aw, bx+bw) - max(ax, bx))
inter_h = max(0, min(ay+ah, by+bh) - max(ay, by))
inter   = inter_w * inter_h
union   = area_a + area_b - inter
IoU     = 0 if union <= 0 or any side <= 0, else inter / union
```

Boxes that only touch on an edge have IoU 0. Do not clip boxes to the canvas in v1; every locked fixture, including a +2, +1 shift, stays inside 640 x 360. Non-finite coordinates (NaN, Inf) yield IoU 0 and are rejected by the scene validator.

Locked IoU unit cases (exact rationals; float64 must match within `1e-12`):

| Name | A | B | IoU |
| --- | --- | --- | --- |
| identical_10 | (0, 0, 10, 10) | (0, 0, 10, 10) | 1 |
| half_shift_x | (0, 0, 10, 10) | (5, 0, 10, 10) | 1/3 |
| touching_edge | (0, 0, 10, 10) | (10, 0, 10, 10) | 0 |
| shift_2_1 | (0, 0, 10, 10) | (2, 1, 10, 10) | 9/16 = 0.5625 |
| robot_40_shift | (20, 60, 40, 40) | (22, 61, 40, 40) | 741/859 |
| pallet_50x30_shift | (140, 100, 50, 30) | (142, 101, 50, 30) | 58/67 |
| cone_20_shift | (250, 40, 20, 20) | (252, 41, 20, 20) | 171/229 |
| zero_width | (0, 0, 0, 10) | (0, 0, 10, 10) | 0 |
| containment | (0, 0, 10, 10) | (2, 2, 4, 4) | 4/25 = 0.16 |

### Decision C - assignment

At most 8 objects per frame (the warehouse scene has 3). Frame-level matching minimizes the sum of costs, where cost is `(1 - IoU)` if `IoU >= 0.5` and forbidden (`1e9`) otherwise. After assignment, drop remaining forbidden pairs; they become false negatives or false positives. When the two sides have different lengths, pad to a square with dummy slots of cost 0 and ignore those dummies in the result. If two assignments have the same cost, pick the one whose sorted tuple of `(gt_index, pred_index)` pairs is lexicographically smallest.

Implementation: a rectangular Kuhn-Munkres (Hungarian) teaching implementation, not a library and not SciPy. For every locked matrix with both sides at most 6, a unit test requires that this function match an exhaustive permutation oracle exactly, including the counterexample below. Frame cap: if either side has more than 8 boxes, the scorer returns `invalid` and CI fails. The UI must refuse a ninth box rather than freeze.

Detection matching is class-agnostic: a robot box can match a pallet box. Precision and recall at IoU 0.5 are therefore localization scores, not class-correct detection scores. Annotator B's precision of 1 is consistent with that choice; do not silently switch to class-aware matching.

Locked counterexample (exhaustive must beat greedy-by-descending-IoU). IoU matrix:

```
0.55  0.54
0.54  0.10
```

`0.10` is below 0.5 and is forbidden. Greedy-by-descending-IoU would take `(0, 0)` and then fail to match row 1. Exhaustive must take `(0, 1)` and `(1, 0)`.

### Decision D - Cohen's kappa

Computed on class labels of matched box pairs only. Unmatched boxes are not kappa items; they appear in FN/FP and as missing values in alpha.

```
k = (p_o - p_e) / (1 - p_e)
```

`p_e` uses each rater's own marginals. Return `null` if `n == 0` or `p_e == 1`.

Locked cases:

- labels `A,A,A,B` vs `A,A,B,B`: `k = 1/2`
- labels `A,A,B,B` vs `A,B,A,B`: `k = 0`
- perfect pair: `k = 1`
- all the same category: `null` (undefined)
- 50-item table `[[20, 5], [10, 15]]`: `p_o = 7/10`, `p_e = 1/2`, `k = 2/5`

Cite Cohen, Educational and Psychological Measurement, 1960. The Sage full text returned HTTP 403 in the planning check; the formula is the standard definition. Do not claim a journal PDF was retrieved.

### Decision E - Krippendorff's alpha, nominal, missing allowed

Implementation follows Krippendorff, "Computing Krippendorff's Alpha-Reliability" (2011 revision). The PDF was retrieved with HTTP 200, 443314 bytes, magic `%PDF-1.3`, from https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff%27s%20Alpha-Reliability.pdf

Units with fewer than 2 ratings are skipped. For a unit with `m` ratings:

```
o_cc += n_c * (n_c - 1) / (m - 1)
o_ck += n_c * n_k / (m - 1)   # c != k
```

`n` is the number of values in units with `m >= 2`. Nominal alpha:

```
alpha = [(n - 1) * sum_c o_cc - sum_c n_c(n_c - 1)] / [n(n - 1) - sum_c n_c(n_c - 1)]
```

This is equivalent to `1 - D_o / D_e` for the nominal metric (delta is 0 if equal, else 1). Return `null` if the denominator is 0.

Locked official example (Ben and Gerry, 12 items, two observers, no missing), letters as in the paper:

```
Ben:   a a b b d c c c e d d a
Gerry: b a b b b c c c e d d d
```

alpha = `155/224` = `0.6919642857142857` in rational arithmetic (the paper prints 0.692).

Items for the warehouse multi-rater score: one item per `(frame, gt_track_id)` in order frame `0..19`, ids `1, 2, 3`. A rater's value is the class of the unique matched box (`IoU >= 0.5`), or missing if unmatched. This alpha measures class agreement after matching; it does not measure box-shift error (annotator A has the same class coding as ground truth). Spatial error is reported by mean IoU / `motp_mean_iou`. Do not claim otherwise.

Locked warehouse alphas (exact):

| Raters | alpha |
| --- | --- |
| A, C | 1 |
| A, B | 71/150 |
| B, C | 71/150 |
| A, B, C | 671/830 |
| GT, A, B, C | 457/530 |

### Decision F - CLEAR MOT-style MOTA and IDF1

Inspired by Bernardin and Stiefelhagen, EURASIP Journal on Image and Video Processing 2008, DOI 10.1155/2008/246309, and Ristani et al., ECCV Workshops 2016, arXiv 1609.01775 (abs and pdf HTTP 200). The Springer article landing page was HTTP 200; a full PDF was not independently retrieved here, so cite the DOI and arXiv, and do not claim the Springer PDF was hashed.

Protocol:

- Each frame: min-cost assignment as in Decision C.
- An identity switch is counted when a GT track that was matched in its most recent previously matched frame is now matched to a different predicted track id. A two-object swap in one frame counts as two switches.
- `MOTA = 1 - (FN + FP + IDSW) / GT_count`. May be negative. If `GT_count == 0` and `pred_count == 0`: `MOTA = 1`, `IDF1 = 1`, `motp_mean_iou = null`. If `GT_count == 0` and `pred_count > 0`: `MOTA = null` (invalid, not a ship fixture).
- `motp_mean_iou` is the mean IoU of matched pairs (the overlap form). This is not a world-coordinate or pixel-distance MOTP. If there are no matches: `null`.
- IDF1 follows the usual identity-score protocol (Ristani et al.; potential matches are all pairs with IoU >= 0.5, not only the pairs chosen by the per-frame matcher). In each frame, every threshold-valid `(gt_id, pred_id)` pair increments a count, independently of that frame's CLEAR-style assignment. Then assign identities by Kuhn-Munkres on `cost = -count`, maximizing IDTP. At most 32 distinct identities on each side of that assignment; if either side exceeds 32, the scorer returns `invalid` immediately (do not enumerate 32! permutations; Hungarian is cubic). `IDFN = GT_count - IDTP`, `IDFP = pred_count - IDTP`. `IDF1 = 2*IDTP / (2*IDTP + IDFP + IDFN)` when the denominator is nonzero, else `null`.
- MOTA in this demo uses an independent per-frame min-cost assignment. Classic CLEAR matching prefers a still-valid previous correspondence before optimizing overlap. Those can disagree on identity switches in ambiguous frames. Name the protocol in report metadata as `assignment_protocol: per_frame_min_cost_iou`. Do not call this "official CLEAR matching." Keep the simpler teaching MOTA; add the discriminating IDF1 fixture below so the two IDF1 accumulators cannot be confused.

Locked toy (2 frames, 2 objects, identical 10x10 boxes, perfect match then a complete ID swap): FN=0, FP=0, IDSW=2, GT=4, matches=4, MOTA=`1/2`, IDF1=`1/2`, `motp_mean_iou=1`, IDTP=2. On this fixture the two IDF1 accumulators agree.

Locked discriminating IDF1 fixture `idf1_potential_pairs` (standard IDF1 and match-only IDF1 disagree; warehouse goldens are unchanged). Integer boxes, IoU 0.5 threshold:

- Frame 0: GT 1 `(0,0,100,100)`, GT 2 `(40,0,100,100)`, pred 10 `(0,0,100,100)`, pred 20 `(40,0,100,100)`. Cross IoU is `3/7` (below threshold). Only the diagonal pairs are valid.
- Frame 1: same GT boxes and the same identities; pred 10 `(33,0,100,100)`, pred 20 `(7,0,100,100)`. IoU matrix (rows GT 1,2; columns pred 10,20): `67/133`, `93/107` on the first row and `93/107`, `67/133` on the second (`67/133 ≈ 0.5037593984962406`, `93/107 ≈ 0.8691588785046729`). All four pairs are valid. Per-frame min-cost selects the two `93/107` (cross) matches.

Standard IDF1 counts: `(1,10)=2`, `(2,20)=2`, `(1,20)=1`, `(2,10)=1`. Identity assignment takes the diagonal, IDTP=4, IDFN=0, IDFP=0, IDF1=1, GT_count=4, pred_count=4. A mutant that increments counts only on per-frame matches has all counts equal to 1, IDTP=2, and IDF1=`1/2`; that mutant must fail the standard-IDF1 gate. MOTA on this fixture is `1 - (0+0+2)/4 = 1/2` because the teaching per-frame matcher switches IDs in frame 1.

Empty-result contracts (display `n/a` for `null`, never a fake 0 when the value is undefined):

- `pred_count == 0` and `GT_count > 0`: precision=`null`, recall=0, f1=`null`, MOTA=0, IDF1=0, `motp_mean_iou=null`, `label_kappa=null`. This is the You-tab start state versus warehouse GT.
- `GT_count == 0` and `pred_count == 0`: as above, MOTA=1, IDF1=1, `motp_mean_iou=null`.
- `GT_count == 0` and `pred_count > 0`: MOTA=`null`, recall=`null`.
- Kappa remains `null` when `n==0` or `p_e==1`, including a single-class matched subset that makes `p_e==1`.

Detection quality at IoU 0.5 is precision, recall, and F1 only. Do not claim COCO mAP or VOC all-point AP.

### Decision G - locked warehouse_v1 scene and annotators

Canvas 640 x 360. 20 frames, indices `0..19`. `t = frame / 19`. Classes: `robot`, `pallet`, `cone`. Ground truth (constant sizes, linear motion):

- track 1, `robot`: `Box(x=20+(200-20)*t, y=60, w=40, h=40)`
- track 2, `pallet`: `Box(x=140, y=100, w=50, h=30)` (static)
- track 3, `cone`: `Box(x=250, y=40+(120-40)*t, w=20, h=20)`

No RNG. CI regenerates the scene JSON from this formula and diffs it to the committed fixture (small JSON, no PNG frames in the repo).

Annotator A: every box shifted `+2` x, `+1` y; same ids and classes.

Annotator B: drop every cone; on frames `10..19` flip pallet class to `robot`; otherwise exact geometry and ids.

Annotator C: exact boxes and classes; on frames `10..19` swap track ids of robot and pallet (`1 <-> 2`). Cone unchanged.

Locked scores versus ground truth (rational arithmetic; float64 within `1e-12`):

**A** (spatial noise, perfect labels and ids):

- matches=60, FN=0, FP=0, IDSW=0, GT=60, pred=60
- MOTA=1, IDF1=1, `label_kappa=1`, `n_matched=60`
- per-class IoU: robot `741/859`, pallet `58/67`, cone `171/229` (constant across frames)
- `mean_iou = motp_mean_iou = 32619964/39538911 = 0.825009166286851`
- precision=1, recall=1, f1=1

**B** (misses plus label errors):

- matches=40, FN=20, FP=0, IDSW=0, pred=40
- MOTA=`2/3`, IDF1=`4/5`, `label_kappa=1/2`, `n_matched=40`
- `motp_mean_iou=1`
- precision=1, recall=`2/3`, f1=`4/5`
- confusion on 40 matched pairs: 20 robot-robot, 10 pallet-pallet, 10 pallet-robot

**C** (identity switch only):

- matches=60, FN=0, FP=0, IDSW=2, pred=60
- MOTA=`29/30`, IDF1=`2/3`, `label_kappa=1`, `n_matched=60`
- `motp_mean_iou=1`
- precision=1, recall=1, f1=1
- IDTP=40, IDFN=20, IDFP=20

GT versus GT: MOTA=1, IDF1=1, kappa=1, `motp_mean_iou=1`, matches=60.

A recorded prototype on 2026-11-11 produced these exact rationals (Ben/Gerry alpha matched `155/224` with absolute error 0).

### Decision H - mutants that must fail

A crash or NaN is a CI failure, not a mutant pass. Each mutant is a separate function, not a random perturbation.

1. `iou_over_gt` (intersection / area of the first box) reports the robot shift as `741/800`, not `741/859`. The true-IoU test must fail this mutant.
2. `kappa_is_po` (reports `p_o`) reports `3/4` on annotator B, not `1/2`. The kappa test must fail this mutant.
3. `mota_skip_idsw` reports `1` on annotator C, not `29/30`. The MOTA test must fail this mutant.
4. `idf1_match_only` increments identity counts only on per-frame matches and reports IDF1 `1/2` on `idf1_potential_pairs`, not 1. The standard-IDF1 test must fail this mutant.

Each mutant is injected into the production scorer (a parameter or a monkeypatch of the function the gates call), not a standalone helper that the gate never uses. The healthy control must pass the same assertion; the mutant must return finite values; then the named numeric assertion must reject it.

### Decision I - React workbench on Pages

Vite + React + TypeScript. Base path `/annotation-qa-workbench/`. A Canvas 2D renderer draws a floor grid and colored class rectangles from scene JSON (no photo assets, no large binaries). Required UI:

- frame slider and previous/next
- draw, select, resize, and delete axis-aligned boxes
- set class and track id
- annotator tabs: You, A, B, C, Ground truth (GT is read-only)
- You starts empty and can be edited; A, B, C, and GT are loadable locked traces (only You is editable)
- live score panel versus GT and pairwise among loaded raters, using the TypeScript metrics
- a CI report panel that fetches `report.json` via `import.meta.env.BASE_URL`

The HTML document title contains `synthetic data`. Exact visible strings:

- `Synthetic data only`
- `Simulation only`
- `Recorded CI scores sit beside a live annotator; this page does not train a model and does not use real robot images.`

`web/public/sample_report.json` has `"sample": true`. CI copies `artifacts/report.json` to `web/public/report.json` with `"sample": false` before `vite build`. If the CI report is missing on a production build, show an error state; do not silently fall back to the sample.

`docs/demo.png` is produced once by a local Playwright run and committed. CI uploads a fresh screenshot artifact and does not commit it.

Locked box contract for the You tab (shared by Python and TypeScript): track ids are integers in `1..9999` and must be unique within a frame; classes are only `robot`, `pallet`, or `cone`; a track may change class across frames (annotator B does this); reverse-direction drags are normalized to positive `w,h`; a zero-area box is discarded, not kept; coordinates must satisfy `x,y` in `[-1000, 2000]` and `w,h` in `(0, 2000]`, otherwise that annotation is rejected (finite inputs can still overflow if unbounded); the ninth box is refused in the UI and is `invalid` in the scorer. Edits persist in memory across tab switches and frame changes, and are lost on reload; the README must say so. A keyboard-operable form edits the selected box's `x,y,w,h`, class, and track id. Locked traces (A, B, C, GT) are not editable. Suggested fill colors (not a score gate): robot `#2F6FED`, pallet `#C47A12`, cone `#C22A2A`; floor `#1B1F24`, grid `#2A313A`. Display at least 6 decimal places, and also expose a raw numeric `data-testid` (for example `data-score="motp_mean_iou"`) that Playwright reads.

Playwright, Chromium only, `npx playwright install --with-deps chromium`, `webServer` serving the built site on 127.0.0.1, tests at `/annotation-qa-workbench/`. Tests must interact with the canvas (not tautological):

- draw the exact GT robot box on frame 0 in the You tab and assert the displayed IoU versus GT is 1 within `1e-9`
- load A and assert `motp_mean_iou` (or mean IoU) matches `32619964/39538911` within `1e-9`
- assert B MOTA and C IDF1 match the golden values
- assert the title and the three honesty strings
- compact edit sequence: draw, select, resize or edit via the form, change class and track id, delete; then assert the live scores update
- frame isolation: a box drawn on frame 0 is not present as a drawable object on frame 1
- an attempted edit of a locked trace (GT or A) does not change that trace
- You starts empty: live MOTA versus GT is 0, and precision / kappa / `motp_mean_iou` show `n/a`
- CI report panel numbers come from the fetched JSON, not from the live You scorer
- missing-report, non-OK, malformed JSON, and `sample: true` in a production build each show the error state; inject these per test (do not delete a shared build artifact)
- `no console errors` is scoped so an intentional failed fetch in the error-state test is not a failure
- assert the title and the three honesty strings

Vitest unit tests and Playwright tests must use explicit `include` / `testDir` so `dashboard.spec.ts` is not collected by Vitest ([Vitest default include](https://vitest.dev/config/include) matches `*.spec.ts`).

### Decision J - one workflow, pinned SHAs, non-vacuous CI

`runs-on: ubuntu-24.04`. Never `ubuntu-latest`. Jobs: `core`, `web` (`needs: [core]`), `pages` (`needs: [core, web]`). Timeouts: 15 minutes each. Coverage line floor **80%** on authored Python modules `geometry`, `match`, `metrics` (kappa, alpha, mot, detection), `scenes`, `annotators`, and `report` only (omit `cli.py` and `web/`). Configure coverage so unexecuted authored files in that set still count in the denominator, and assert a nonzero measured statement count. `--cov-fail-under=80` must be able to fail. The negative coverage check uses the same 80% threshold on a deliberately undercovered, isolated fixture, writes to a separate coverage data file so it cannot replace the real report, asserts that tests actually ran (pytest exit code 1, not 2 or 3), and inspects the coverage failure reason. Do not implement the negative check by raising the floor to 100 on the real suite.

`author-check` inspects `github.event.pull_request.head.sha` on `pull_request` events and `github.sha` on `push`. On pull requests, `github.sha` is the merge commit and is not an authorship oracle ([GitHub pull_request SHA behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)). Fetch the head commit if it is not already in the clone. Report `git_sha` records the checked-out tree (the merge commit on `pull_request` if that is what the job tests, or the push SHA on `push`); do not use the authorship check as a substitute for report provenance. Names and emails are a policy check, not a proof of identity.

`license-bytes`: `LICENSE` sha256 equals `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` (official 11358-byte Apache-2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt).

The typographic-dash and assistant-word gate MUST use `grep -P` (do not use ripgrep; do not write a step that becomes green if a search binary is missing). Probe `grep -P` on a temporary known-match file; if `grep` is missing or exits 2, the job fails. Exit status 1 from a clean scan means "no matches" and is success. Scan the nonempty set of tracked authored text files (not the whole worktree). Exclude `LICENSE` from the assistant-word half of the scan only: the official Apache-2.0 text includes a stock clause about displays of Derivative Works, and `LICENSE` is already protected by the byte-hash gate. Still scan `LICENSE` for typographic dashes. Do not edit `LICENSE` to silence a scan; the byte-hash test is the authority. Fail if any such file contains U+2014, U+2013, or U+2212, or matches a regex that CI builds at runtime from `tests/hygiene_codepoints.txt`. That file contains one token per line as space-separated hex bytes (no assistant names in plaintext). The implementation brief lists the plaintext tokens so a reviewer can check the hex file; the committed tree must pass the assembled gate, including this plan. Do not flag the ordinary word "box" in "bounding box". Add fixtures: a clean file, a prohibited file in a temp dir, and a scanner-error case (for example `grep -P` invoked in a way that exits 2). A SHA-pin check must fail on floating tags (`@v4`, `@v7`), short SHAs, malformed SHAs, and un-pinned `uses:` forms, and must pass a valid `name@<40-hex>` with a tag comment; merely searching for the substring `@v4` is not enough. Every Action is `name@<40-hex>` with a comment of the tag.

GitHub Actions, full commit SHAs (verified 2026-11-11 via the GitHub git refs API; type=commit), never floating tags:

| Action | Tag | SHA |
| --- | --- | --- |
| actions/checkout | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-python | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| actions/setup-node | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| actions/upload-artifact | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| actions/download-artifact | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |
| actions/configure-pages | v6.0.0 | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
| actions/deploy-pages | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |
| actions/upload-pages-artifact | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |

The `pages` job runs only when `github.ref == 'refs/heads/main' && github.event_name == 'push'`, downloads the tested `web-dist`, and deploys only that tree. No `pages.yml`. No `pull_request_target`. No secrets in fork PRs.

`core` writes `artifacts/report.json` via `aqw score` and `aqw report --check --require-ci --expect-sha $GITHUB_SHA`. Gates are recomputed from records. `sample: true` must be rejected for CI. Do not commit generated frame images. Keep the repo small; render at run time.

### Decision K - honesty and license

Outbound Apache-2.0. NOTICE starts with `annotation-qa-workbench, Copyright 2026 Arpan Bom` and lists every direct runtime and dev dependency actually installed, with version and license, including `@types/node`, `@types/react`, `@types/react-dom`, hatchling, pip-tools, Playwright, Vite, TypeScript, Vitest, and `@vitejs/plugin-react`. Distinguish tools that are only installed (pytest, ruff, Playwright, and the rest of the dev set) from code redistributed in the Pages bundle (React, react-dom, and any transitive modules Vite actually emits). A `THIRD_PARTY_NOTICES.md` file at the repo root, copied into `web/public/` so it ships with Pages, contains the copyright and permission notice of every package in that production bundle, as required by those licenses and by Apache-2.0 section 4. Preserve any applicable upstream NOTICE text. The outbound Apache-2.0 license does not replace dependency licenses. No over-credits. Idea references belong in REFERENCES.md, pointed from NOTICE, and need no copied source notices. SPDX-License-Identifier: Apache-2.0 on every authored Python and TypeScript/TSX file.

## Pinned stack

Verified 2026-11-11 against PyPI, npm, nodejs.org, and the GitHub API. Python runtime on the runner: **3.12** (latest 3.12.x that `setup-python` resolves; do not float to 3.13).

Direct Python packages, equality pins, linux x86_64 or py3-none-any wheels:

| Package | Version | Wheel | sha256 | License |
| --- | --- | --- | --- | --- |
| pytest | 9.2.0 | `pytest-9.2.0-py3-none-any.whl` | `07acdcf88ec174f907dc01af70bf52d49b014bbab03faeeade31c96b18c2e588` | MIT |
| pytest-cov | 7.1.0 | `pytest_cov-7.1.0-py3-none-any.whl` | `a0461110b7865f9a271aa1b51e516c9a95de9d696734a2f71e3e78f46e1d4678` | MIT |
| coverage | 7.17.2 | `coverage-7.17.2-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl` | `36314997533266bde3d07765289674304d61bfe49165bb1b4fa9be12cb4ba0d1` | Apache-2.0 |
| ruff | 0.17.4 | `ruff-0.17.4-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `2cd025509b2e15721b426fc70fd946d71f43b3db3b08e946dfec2d696d911690` | MIT |
| mypy | 2.4.1 | `mypy-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `a20ff6cd2af7a670c64f089bfa5fbcebe8ff3bf896c5e6ac7c9862c7960e4494` | MIT |
| hatchling | 1.33.0 | `hatchling-1.33.0-py3-none-any.whl` | `415290b84f464d2884303fca8974d38e7b85579069fab02a15db0828fbb1446d` | MIT |
| pip-tools | 7.6.2 | `pip_tools-7.6.2-py3-none-any.whl` | `f37eb4b736859c2c30230e50977312c61918b7ef931071ff7811fd067715c25f` | BSD-3-Clause |

`requirements.in` lists pytest, pytest-cov, coverage, ruff, mypy, and hatchling 1.33.0 (so the build backend is in the hashed lock). Do not pass `pip-compile --python-version`. Run pinned `pip-tools==7.6.2` under Python 3.12: `pip-compile --generate-hashes -o requirements.lock requirements.in`. The lock's transitive set is whatever that resolver writes, including hatchling's own dependencies; do not hand-edit transitive versions into this plan. Record the pip version used to generate the lock in a comment at the top of the lock or in NOTICE. CI installs with `pip install --require-hashes -r requirements.lock`, then installs the local package with `--no-build-isolation --no-deps` so the isolated build path cannot fetch unhashed build dependencies ([pip build isolation](https://pip.pypa.io/en/stable/reference/build-system/)).

Node Active LTS: **26.13.0** Lithium, 2026-10-28, bundled npm **11.20.0** (https://nodejs.org/dist/index.json). npm packages, current latest on 2026-11-11, licenses from the registry:

| Package | Version | License |
| --- | --- | --- |
| vite | 8.3.8 | MIT |
| typescript | 7.0.2 | Apache-2.0 |
| vitest | 5.1.0 | MIT |
| @playwright/test | 1.65.0 | Apache-2.0 |
| @types/node | 26.6.6 | MIT |
| react | 19.3.1 | MIT |
| react-dom | 19.3.1 | MIT |
| @types/react | 19.3.0 | MIT |
| @types/react-dom | 19.3.0 | MIT |
| @vitejs/plugin-react | 6.3.0 | MIT |

Commit `package-lock.json` generated with npm 11.20.0. Playwright browsers: Chromium only, the build bundled with `@playwright/test@1.65.0`.

Sources: `https://pypi.org/pypi/<name>/<ver>/json`, `https://registry.npmjs.org/<name>/<ver>`, `https://nodejs.org/dist/index.json`, `https://api.github.com/repos/actions/<name>/git/refs/tags/<tag>`.

## File layout

```
annotation_qa_workbench/
  constants.py
  geometry.py
  match.py
  metrics/kappa.py
  metrics/alpha.py
  metrics/mot.py
  metrics/detection.py
  scenes.py
  annotators.py
  report.py
  cli.py
tests/                  # mirrors the package, plus:
  test_gates.py
  test_mutants.py
  test_report_schema.py
  test_docs_honesty.py
  test_assignment.py
web/
  index.html
  src/main.tsx
  src/App.tsx
  src/canvas/
  src/metrics/
  src/scenes/
  src/report/
  tests/                # vitest + Playwright dashboard.spec.ts
  public/sample_report.json
fixtures/scenes/warehouse_v1.json
fixtures/expected/      # unit plus warehouse scores
tests/hygiene_codepoints.txt
THIRD_PARTY_NOTICES.md  # filled after the npm lock, copied to web/public/
docs/demo.png
.github/workflows/ci.yml
LICENSE
NOTICE
README.md
pyproject.toml
requirements.in
requirements.lock
web/package.json
web/package-lock.json
```

SPDX-License-Identifier: Apache-2.0 on every authored Python and TypeScript/TSX file.

## Interfaces

### Python

```
iou(a, b) -> float
match_boxes(gt_boxes, pred_boxes, thresh=0.5) -> list[(i, j, iou)]
cohen_kappa(labels_a, labels_b) -> float | None
krippendorff_alpha_nominal(reliability_matrix) -> float | None
score_sequence(gt_seq, pred_seq) -> MotScore
generate_warehouse_v1() -> Scene
apply_annotator(scene, name) -> Scene   # name in {A, B, C}
write_report(path, payload) -> None    # JSON, reject NaN
```

`min_cost_assignment(cost_matrix) -> list[(row, col, cost)]` is the shared Hungarian helper.

`MotScore` includes `fn`, `fp`, `idsw`, `gt_count`, `pred_count`, `matches`, `mota`, `motp_mean_iou`, `idtp`, `idfn`, `idfp`, `idf1`, `precision`, `recall`, `f1`, `label_kappa`, `n_matched`. Integer fields are JSON integers, not booleans. Nullable fields use JSON `null` (not 0) when Decision F says `null`. Python `True`/`False` must not pass a validator that expects numbers.

### CLI

```
aqw generate --out fixtures/scenes
aqw score --scene fixtures/scenes/warehouse_v1.json --out artifacts/report.json --sha $GITHUB_SHA
aqw report --check artifacts/report.json --require-ci --expect-sha $GITHUB_SHA
```

`aqw score` applies A, B, C, and the GT self-check, and writes schema v1. Exit code 1 when any ship gate fails. `aqw report --check --require-ci` recomputes every warehouse gate from the scene plus locked annotator functions, rejects `sample: true`, rejects a zero or missing SHA, rejects NaN, and exits 1 on a failed gate or a missing field.

### Report JSON (schema version 1)

Top-level: `schema_version` (1), `sample` (bool), `git_sha` (40 hex from `GITHUB_SHA` / `--sha`; never the literal `unknown`; 40 zeros only on the committed sample), `honesty` (exact: `Synthetic data only. Simulation only. This file is recorded output; it is not a live model-training run and it does not contain real robot images.`), `scene` (`warehouse_v1`), `constants` (`iou_thresh` 0.5, `width` 640, `height` 360, `n_frames` 20), `scores` for keys `gt`, `A`, `B`, `C` (each a MotScore plus per-class IoU where applicable), `alphas` (`AC`, `AB`, `BC`, `ABC`, `GTABC`).

A validator recomputes those scores from the committed warehouse scene and the locked annotator functions (the same generator checked by the regen diff), checks `constants`, `honesty`, and `git_sha`, and fails if a stored number disagrees beyond `1e-12`. Reject non-finite values on read as well as write (`NaN` and infinities must not compare as "close enough"). Required keys and types are exact. Add rejection tests for: a changed finite score, a missing key, an incorrect SHA, a wrong constant, a wrong `null`, a boolean used as a number, `NaN`, and infinity. Test `--expect-sha` as well as the `sample` flag.

### Pages

Route `/annotation-qa-workbench/` loads `report.json` next to the built assets and runs the live annotator as in Decision I. Displayed CI-report numbers must match the fetched JSON.

## Edge cases

- Touching boxes: IoU 0.
- Zero or negative width or height: IoU 0.
- Non-finite coordinates: IoU 0, scene rejected.
- Empty frame vs empty frame: MOTA=1, IDF1=1, `motp_mean_iou=null`.
- Empty GT vs one prediction: MOTA=`null`.
- Kappa with `n=0` or `p_e=1`: `null`.
- Alpha with fewer than two ratings in every unit, or a zero denominator: `null`.
- More than 8 boxes on one side of a frame: `invalid`.
- ID switch after a gap (GT missed then seen again): compare against the last previous match, not against "previous frame only if matched then."
- Boxes that stay inside the canvas after the +2, +1 shift; no clipping, but coordinates outside the accepted range are rejected.
- Duplicate track ids in one frame: rejected by the validator.
- Fresh identities each frame (8 frames, 3 boxes, 24 predicted ids): IDF1 is finite and the call finishes in under 2 seconds. A 33-identity fixture returns `invalid` without a factorial search.
- You-tab empty versus warehouse GT: MOTA 0, IDF1 0, precision / f1 / kappa / `motp_mean_iou` are `null`.

## Test plan

Unit tests: all IoU cases in Decision B; assignment counterexample in Decision C and an `n=9` invalid test; all kappa cases in Decision D; Ben/Gerry alpha `155/224` with absolute error 0 in rational terms (float64 within `1e-12`); warehouse alphas in Decision E; toy MOTA/IDF1 in Decision F; warehouse A, B, C, and GT self-score in Decision G; all three mutants in Decision H, each healthy and failing the named gate; scene regeneration diffs; report schema and `sample: true` rejection; README honesty phrases; typographic-dash and tool-word tests may live in CI rather than pytest.

`ruff check` and `mypy --strict` on `annotation_qa_workbench`. `pytest --cov` with `--cov-fail-under=80` on the locked module set, plus a negative uncovered-fixture check.

Vitest plus `tsc --noEmit`: TypeScript metrics match the same goldens within `1e-12`. Playwright as in Decision I. The screenshot is an artifact in CI and is committed once locally.

## Numbered success criteria

1. `pytest tests/test_geometry.py` - all nine IoU unit cases match the rationals in Decision B within `1e-12`.
2. `pytest tests/test_assignment.py::test_exhaustive_beats_greedy` - the 0.55 / 0.54 / 0.10 matrix assigns `(0, 1)` and `(1, 0)`. `test_hungarian_matches_exhaustive` agrees with the permutation oracle on every locked n<=6 matrix. `test_n9_invalid` returns `invalid`. `test_identity_cap_33` returns `invalid` quickly. `test_fresh_ids_24` finishes in under 2 seconds with a finite IDF1.
3. `pytest tests/test_kappa.py` - locked cases `1/2`, `0`, `1`, `null`, and `2/5`.
4. `pytest tests/test_alpha.py::test_ben_gerry` - alpha equals `155/224` within `1e-12`.
5. `pytest tests/test_alpha.py::test_warehouse_alphas` - A,C `1`; A,B and B,C `71/150`; A,B,C `671/830`; GT,A,B,C `457/530`.
6. `pytest tests/test_mot.py::test_id_swap_toy` - MOTA `1/2`, IDF1 `1/2`, `motp_mean_iou` 1, IDSW 2, FN 0, FP 0.
6b. `pytest tests/test_mot.py::test_idf1_potential_pairs` - standard IDF1 is 1, IDTP 4, IDFN 0, IDFP 0; MOTA is `1/2` under the teaching per-frame protocol.
6c. `pytest tests/test_mot.py::test_empty_you_vs_gt` - pred_count 0 against warehouse GT yields MOTA 0, IDF1 0, and `null` precision, f1, kappa, and `motp_mean_iou`.
7. `pytest tests/test_gates.py::test_annotator_a` - MOTA 1, IDF1 1, kappa 1, `motp_mean_iou` `32619964/39538911`, per-class IoU `741/859`, `58/67`, `171/229`.
8. `pytest tests/test_gates.py::test_annotator_b` - MOTA `2/3`, IDF1 `4/5`, kappa `1/2`, FN 20, FP 0, precision 1, recall `2/3`, f1 `4/5`.
9. `pytest tests/test_gates.py::test_annotator_c` - MOTA `29/30`, IDF1 `2/3`, kappa 1, IDSW 2, IDTP 40, IDFN 20, IDFP 20.
10. `pytest tests/test_gates.py::test_gt_self` - MOTA 1, IDF1 1, kappa 1, `motp_mean_iou` 1, matches 60.
11. `pytest tests/test_mutants.py::test_iou_over_gt` - mutant reports `741/800` for the robot shift and fails the true-IoU assertion of `741/859`.
12. `pytest tests/test_mutants.py::test_kappa_is_po` - mutant reports `3/4` on B and fails the `1/2` assertion.
13. `pytest tests/test_mutants.py::test_mota_skip_idsw` - mutant is injected into the production scorer, the healthy control still reports `29/30`, the mutant reports 1 on C as a finite value, and the same `29/30` assertion rejects it. A crash or NaN fails the test.
13b. `pytest tests/test_mutants.py::test_idf1_match_only` - the mutant reports IDF1 `1/2` on `idf1_potential_pairs` and fails the standard-IDF1 assertion of 1, with a passing healthy control.
14. `pytest tests/test_scenes.py::test_warehouse_regen` - `aqw generate` into a temp directory diffs equal to `fixtures/scenes/warehouse_v1.json`.
15. `pytest tests/test_report_schema.py` - CI report has `schema_version == 1`, `sample == false`, scores for `gt`, `A`, `B`, `C`, and every stored number equals a recomputation within `1e-12`.
16. `aqw report --check --require-ci` on a mutated report that sets `sample` true while claiming a real SHA exits 1.
17. `pytest --cov` on the locked module set with `--cov-fail-under=80` exits 0, with a nonzero measured statement count and unexecuted authored files included in the denominator. The isolated 80% negative fixture run uses a separate coverage data file, exits 1 (not 2 or 3), and the log shows a coverage-threshold failure.
18. `ruff check` and `mypy --strict` on `annotation_qa_workbench` exit 0.
19. `npx tsc --noEmit`, `npx vitest run`, and `npx playwright test` exit 0. Vitest matches the Python goldens within `1e-12` and does not collect Playwright specs. `dashboard.spec.ts` draws the GT robot box and sees IoU 1, loads A and sees mean IoU `32619964/39538911` within `1e-9` via a raw `data-testid`, checks B MOTA and C IDF1, runs the compact edit / delete / frame-isolation / locked-tab checks, checks the empty-You `n/a` state, checks the three honesty strings and a title containing `synthetic data`, and checks the injected missing-report, malformed-JSON, and production-`sample` error states.
20. `ci.yml`: `web` has `needs: [core]`; `pages` has `needs: [core, web]`, `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`, downloads `web-dist`, and deploys only that tested tree. Web steps run with working directory `web` and npm cache `web/package-lock.json`. Artifact uploads set `if-no-files-found: error`. The `grep -P` dash and assistant-word gate (assembled from hex bytes, with clean / prohibited / scanner-error cases), `author-check` as in Decision J, `license-bytes`, and the SHA-pin check (valid 40-hex pins and bad tags) are present and able to fail. Checkout uses `persist-credentials: false` on jobs that never push. Enabling GitHub Pages (`build_type=workflow`) is a repo setting done after the first green `main` run; this workflow does not toggle it.
21. README and NOTICE contain the honesty boundary and do not claim to be CVAT, Label Studio, a production platform, or the inventors of the named metrics. The README states that MOTA uses per-frame assignment, that IDF1 uses all threshold-valid identity pairs, that `motp_mean_iou` is the overlap form, that label-level alpha does not capture annotator A's shift, and that B's precision is localization precision. `tests/test_docs_honesty.py` requires the exact disclaimer strings (including the sentence that contains "does not use real robot images") and rejects a short list of unambiguously positive claims (for example "this uses real robot images", "certified", "production labelling platform"). A fixture with a compliant negative sentence must pass; a fixture with a prohibited positive sentence must fail. Do not fail a file only because a required disclaimer contains those words.
22. `LICENSE` sha256 equals `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. CI step `license-bytes` fails on mismatch. `author-check` uses the pull-request head SHA or the push SHA as in Decision J, and expects author and committer `Arpan Bom <applycoding@gmail.com>` and no co-author trailers. `THIRD_PARTY_NOTICES.md` is present in the built `web/dist` (or `web/public` copied into dist) and names the bundled runtime packages.

## Out of scope

Polygons, polylines, keypoints, masks, 3D cuboids, attributes other than class and track id, real datasets, model training or auto-label, a backend server, COCO or VOC mAP, SciPy or a Hungarian library, NumPy, OpenCV, Pillow, ROS, Gazebo, Nav2, video codecs, audio, multi-page routing, accounts, and any claim of production labelling throughput or inter-annotator studies on real people.

## Documentation and honesty

README: task, the three annotator traces, the gate table, `aqw` commands, and the Pages URL. It states that the data are synthetic, that the metrics are original implementations of well-known methods inspired by the cited papers, that `motp_mean_iou` is the overlap form, that MOTA uses independent per-frame assignment (not classic CLEAR priority matching), that IDF1 counts all threshold-valid identity pairs, that B's precision is localization precision, that label-level alpha does not capture annotator A's shift, that You-tab edits are in-memory only, and that the dashboard is recorded CI output beside a live annotator. NOTICE starts with `annotation-qa-workbench, Copyright 2026 Arpan Bom` and lists redistributed or installed direct and dev dependencies with version and license, not merely idea citations. No real logs, no customer images, no patent-pending material, no safety certification.

## License

Outbound **Apache-2.0**. `LICENSE` is the verbatim official text (hash above). SPDX header on every authored source file.

Idea-only references, licences checked 2026-11-11, are listed in REFERENCES.md. Do not copy those projects.

## Build and CI

Workflow `.github/workflows/ci.yml`. Triggers: `push` and `pull_request`. Permissions default to `contents: read`; the `pages` job adds `pages: write` and `id-token: write`. Concurrency: `pages` group without cancel-in-progress; PR jobs may cancel in progress. No `pull_request_target`. No secrets in fork PRs.

`core` (`ubuntu-24.04`, 15 minutes): checkout SHA pin with `persist-credentials: false`; setup-python 3.12 SHA pin; `pip install --require-hashes -r requirements.lock`; install the local package `--no-build-isolation --no-deps`; `aqw generate` to a temp dir and diff to `fixtures/scenes/`; `ruff`; `mypy --strict`; `pytest` including goldens, mutants, coverage fail-under 80, and the negative coverage fixture; `aqw score` writing `artifacts/report.json`; `aqw report --check --require-ci --expect-sha ${{ github.sha }}`; `author-check`; `license-bytes`; the `grep -P` typographic-dash and tool-word check; the SHA-pin check; upload artifact `report`. Artifact uploads set `if-no-files-found: error`. A missing upload fails the job.

`web` (`needs: [core]`, 15 minutes): checkout with `persist-credentials: false`; setup-node 26.13.0 with npm cache dependency path `web/package-lock.json`; working directory `web` for npm, tsc, vitest, vite, and Playwright; `npm ci`; `npx tsc --noEmit`; `npx vitest run`; download `report`; validate it (`sample: false`, schema, SHA) before copying to `web/public/report.json` (fail if missing or invalid); after `vite build`, confirm the copied report is in `dist`; `npx vite build --base /annotation-qa-workbench/`; `npx playwright install --with-deps chromium`; Playwright against the built site; upload screenshot artifact and `web-dist` (the tested `web/dist` that already contains `report.json`). Do not `git add` the screenshot.

`pages` (`needs: [core, web]`, 15 minutes): `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`; environment `github-pages`; download `web-dist` into a known directory; configure-pages; upload-pages-artifact on that directory; deploy-pages. A failed main run must not replace a previously successful Pages deployment with a sample or failed report.

## Risks

- **Dual Python / TypeScript drift.** Mitigate with committed golden JSON and a parity test. Do not leave one side as the untested "live" path.
- **Playwright canvas coordinates versus CSS scale.** Tests should use a locked canvas CSS size and interact in canvas/image space. Record the mapping in the test.
- **Assignment cost.** Frame matching is capped at 8 boxes. IDF1 identity assignment is capped at 32 identities per side and uses Hungarian, not 32! permutation search. A fresh-id or 33-identity test must prove that bound.
- **Label-level alpha does not capture annotator A's shift.** The README and the score panel must say so. Spatial error is mean IoU.
- **MOTA can be negative**, and is `null` when there is no GT but there are predictions. Do not silently treat that as 0 or 1 except for the empty-vs-empty case in Decision F. MOTA here is the teaching per-frame protocol, not classic CLEAR priority matching.
- **Sample-report fallback.** Production shows an error if `report.json` is absent.
- **`mypy --strict`** may need explicit annotations; do not weaken the CI step, annotate instead.
- **Pin rot.** Pins are dated 2026-11-11. React 19.3.1 and Vite 8.3.8 were current latest; do not silently downgrade without a recorded pin failure. A refresh updates this plan and the lockfile together.
- **Authorship on pull requests.** The merge SHA is not the author oracle; see Decision J.
- **Honesty grep.** Do not forbid substrings that appear in required disclaimers; test exact required sentences and unambiguously positive over-claims.
- **Third-party notices.** The Pages bundle redistributes runtime JavaScript; `THIRD_PARTY_NOTICES.md` must track the actual bundle, not only the direct `package.json` names.

## Verification-hints

Prototype date: 2026-11-11. Arithmetic is rational where a fraction is given; tests may compare float64 against `float(fraction)` within `1e-12`.

IoU of a 10x10 box shifted by (+5, 0) is `50/150 = 1/3`. Shifted by (+2, +1) is `72/128 = 9/16`. Robot 40x40 shifted by (+2, +1): intersection `38*39=1482`, union `3200-1482=1718`, IoU `1482/1718=741/859`. Pallet 50x30: intersection `48*29=1392`, union `3000-1392=1608`, IoU `1392/1608=58/67`. Cone 20x20: intersection `18*19=342`, union `800-342=458`, IoU `342/458=171/229`. A's mean IoU is the average of those three, `32619964/39538911`.

Cohen 2x2 `[[2,1],[0,1]]`: `p_o=3/4`, `p_e=1/2`, `k=1/2`. The 50-item `[[20,5],[10,15]]`: `p_o=7/10`, `p_e=1/2`, `k=2/5`.

Ben/Gerry: `n=24`, diagonal coincidences 18, `sum n_c(n_c-1)=104`, alpha `(23*18-104)/(24*23-104)=310/448=155/224`.

Warehouse B kappa uses 40 matched pairs, 30 agreements, marginals GT robot=20 pallet=20, B robot=30 pallet=10, `p_e=1/2`, `k=1/2`. Mutant `p_o` is `3/4`.

C MOTA: `1 - 2/60 = 29/30`. Mutant without IDSW is 1.

Discriminating IDF1 boxes are integer pixels as in Decision F. Frame-0 cross IoU is `6000/14000=3/7`. Frame-1 diagonal IoU is `6700/13300=67/133`. Frame-1 cross IoU is `9300/10700=93/107`. Standard IDF1=1; match-only IDF1=`1/2`; teaching MOTA=`1/2`.

Do not publish a gate change that lacks recorded prototype rationals and a statement that the locked warehouse scene was not edited to chase a number.
