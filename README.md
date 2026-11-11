# annotation-qa-workbench

A browser workbench to annotate and QA synthetic robot-vision boxes and tracks, with agreement scores. Portfolio demo by Arpan Bom.

**Synthetic data only. Simulation only.** This repository does not use real robot images, customer photos, or public datasets such as COCO or ImageNet. The Pages demo does not train a model.

This is an original implementation of well-known methods (intersection-over-union, Cohen's kappa, Krippendorff's alpha, MOTA, and IDF1), inspired by the cited papers and by the idea of annotation QA workbenches. It is not CVAT, not Label Studio, and not a production labelling platform.

A later implementation will add the Python scorer (`aqw`), the React workbench, and the GitHub Pages demo at `/annotation-qa-workbench/`. See PLAN.md, TASKS.md, and REFERENCES.md.

License: Apache-2.0. Author: Arpan Bom.
