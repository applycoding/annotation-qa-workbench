# annotation-qa-workbench

A browser workbench to annotate and QA synthetic robot-vision boxes and tracks, with agreement scores. Portfolio demo by Arpan Bom.

**Synthetic data only. Simulation only.** This repository does not use real robot images, customer photos, or public datasets such as COCO or ImageNet. The Pages demo does not train a model.

This is an original implementation of well-known methods (intersection-over-union, Cohen's kappa, Krippendorff's alpha, MOTA, and IDF1), inspired by the cited papers and by the idea of annotation QA workbenches. It is not CVAT, not Label Studio, and not a production labelling platform.

## What ships in v1

- Python package `annotation_qa_workbench` with console script `aqw` (`generate`, `score`, `report`).
- Locked synthetic warehouse scene with annotator traces **A**, **B**, and **C** (see PLAN.md).
- GitHub Pages workbench at `/annotation-qa-workbench/` with a Canvas annotator, live scores, and a panel that loads the CI `report.json`.
- Class-agnostic localization precision at IoU 0.5 (annotator B's precision 1 is localization precision, not class-correct detection).
- Teaching **MOTA** via independent per-frame min-cost IoU assignment (`assignment_protocol: per_frame_min_cost_iou`), not classic CLEAR priority matching.
- Standard **IDF1** using all threshold-valid identity pairs (see `idf1_potential_pairs` in tests).
- Overlap-form **`motp_mean_iou`** (not distance MOTP). Label-level Krippendorff alpha does not capture annotator A's spatial shift; mean IoU does.
- **You** tab edits are in-memory only (lost on reload).

## Commands

```bash
pip install --require-hashes -r requirements.lock
pip install --no-build-isolation --no-deps .
aqw generate --out fixtures/scenes
aqw score --scene fixtures/scenes/warehouse_v1.json --out artifacts/report.json --sha "$GITHUB_SHA"
aqw report --check artifacts/report.json --require-ci --expect-sha "$GITHUB_SHA"
```

```bash
cd web && npm ci && npx vite build --base /annotation-qa-workbench/
```

## Gates (warehouse versus ground truth)

| Annotator | MOTA | IDF1 | Label kappa | MOTP mean IoU |
| --- | --- | --- | --- | --- |
| A | 1 | 1 | 1 | 32619964/39538911 |
| B | 2/3 | 4/5 | 1/2 | 1 |
| C | 29/30 | 2/3 | 1 | 1 |

## Test inventory (computed)

```bash
python -m pytest --collect-only -q
cd web && npx vitest run --reporter=basic
cd web && npx playwright test --list
```

<!-- TEST_INVENTORY_START -->
- Pytest: **53** tests collected (`python -m pytest --collect-only -q`).
- Vitest: **21** tests (`cd web && npx vitest run`).
- Playwright: **15** specs (`cd web && npx playwright test --list`).
- Injected scorer mutants: 4 (`iou_over_gt`, `kappa_is_po`, `mota_skip_idsw`, `idf1_match_only`).
<!-- TEST_INVENTORY_END -->

## License

Apache-2.0. Author: Arpan Bom.
