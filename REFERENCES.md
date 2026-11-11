# References

Permissively licensed GitHub projects used as **references only**. Do not copy sources, tests, fixtures, UI, or documentation prose. Credit any conceptually derived idea in the README. Licenses were checked on 2026-11-11 with `gh api repos/OWNER/REPO --jq .license.spdx_id` and with the raw LICENSE file.

**Outbound license for this demo repo is Apache-2.0**. A LICENSE file with the official Apache-2.0 text, a NOTICE file crediting Arpan Bom, and SPDX-License-Identifier: Apache-2.0 headers are required at build time.

This demo must not duplicate existing applycoding repos. The closest is [applycoding/ros2-vision-tracking-demo](https://github.com/applycoding/ros2-vision-tracking-demo): ROS 2 Humble YOLO detection with a ByteTrack-style tracker. This repo is a static annotation QA workbench with multi-annotator agreement scores and no ROS, no learned detector, and no tracker training. Do not copy that tree.

## Selected references (2)

### 1. cvat-ai/cvat

- URL: https://github.com/cvat-ai/cvat
- License: **MIT** (`gh api` SPDX: MIT). Raw LICENSE at commit `f9cb186211c27619604fd6d0bd6c78e8bb5e415d` (develop tip on 2026-11-11, HTTP 200): https://raw.githubusercontent.com/cvat-ai/cvat/f9cb186211c27619604fd6d0bd6c78e8bb5e415d/LICENSE. The LICENSE file begins "MIT License" and names Intel Corporation and CVAT.ai Corporation.
- Borrow: the *idea* of a workbench for drawing boxes and tracks and reviewing them. v1 does not depend on, vendor, or translate CVAT.

### 2. HumanSignal/label-studio

- URL: https://github.com/HumanSignal/label-studio
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0). Raw LICENSE at commit `73262def09a2da4f95ef32c5203dc917c7511fea` (develop tip on 2026-11-10, HTTP 200 on 2026-11-11): https://raw.githubusercontent.com/HumanSignal/label-studio/73262def09a2da4f95ef32c5203dc917c7511fea/LICENSE.
- Borrow: the *idea* of multi-annotator quality checks. Do not vendor, wrap, or translate this project.

## Academic citations (not code)

- Cohen, J. "A Coefficient of Agreement for Nominal Scales," Educational and Psychological Measurement, 20(1), 37-46, 1960. Formula only. The Sage page https://journals.sagepub.com/doi/10.1177/001316446002000104 returned HTTP 403 in the 2026-11-11 planning check. Do not claim that a journal PDF was retrieved.
- Krippendorff, K. "Computing Krippendorff's Alpha-Reliability," 2011 revision. https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff%27s%20Alpha-Reliability.pdf (HTTP 200 on 2026-11-11, 443314 bytes, PDF magic `%PDF-1.3`). The locked Ben/Gerry example and the coincidence-matrix formula come from this document.
- Bernardin, K. and Stiefelhagen, R. "Evaluating Multiple Object Tracking Performance: The CLEAR MOT Metrics," EURASIP Journal on Image and Video Processing, 2008. DOI 10.1155/2008/246309. Article landing page https://link.springer.com/article/10.1155/2008/246309 returned HTTP 200 on 2026-11-11; a full PDF was not independently retrieved in that check. Cite the DOI. This demo implements a teaching MOTA and an overlap-form `motp_mean_iou`; it does not claim a world-coordinate MOTP.
- Ristani, E., Solera, F., Zou, R., Cucchiara, R., and Tomasi, C. "Performance Measures and a Data Set for Multi-Target, Multi-Camera Tracking," ECCV Workshops 2016. arXiv:1609.01775. https://arxiv.org/abs/1609.01775 and https://arxiv.org/pdf/1609.01775 both HTTP 200 on 2026-11-11. This demo implements the usual identity-score accumulator (all threshold-valid pairs, then a global identity assignment). It is not official MOTChallenge code.

Intersection-over-union (the Jaccard index on two axis-aligned boxes) is a classical formula. The Kuhn-Munkres assignment step is a classical algorithm. Neither is an invention of this repo.

## Idea-only or exclude

- applycoding/ros2-vision-tracking-demo, edge-vision-detector, flutter-on-device-vision, edge-yolo-tensorrt, rosbag-eval-bench, lidar-shape-classifier-ros2, rag-llm-eval-demo, llm-eval-observability: different problems. Do not copy.
- COCO API, VOC evaluation kits, MOTChallenge official toolkits: idea-only. Do not vendor them, and do not claim COCO mAP.
- SciPy, NumPy, OpenCV, Pillow, ROS, Gazebo, Nav2: not used in v1.
- GPL or LGPL annotation or tracking libraries: not dependencies.

Direct runtime and dev dependencies (pytest, ruff, mypy, coverage, hatchling, pip-tools, Vite, TypeScript, React, Playwright, and the rest of the lockfiles) belong in NOTICE with version and license once installed. They are dependencies, not idea references.
