# SPDX-License-Identifier: Apache-2.0

"""Localization precision, recall, and F1 at a fixed IoU threshold."""

from __future__ import annotations

from typing import Any

from annotation_qa_workbench.match import match_boxes


def precision_recall_f1(
    gt_frames: list[list[dict[str, object]]],
    pred_frames: list[list[dict[str, object]]],
    iou_fn: Any = None,
) -> tuple[float | None, float | None, float | None, int, int, int]:
    from annotation_qa_workbench.geometry import iou as default_iou

    if iou_fn is None:
        iou_fn = default_iou

    tp = 0
    fn = 0
    fp = 0
    for gt_boxes, pred_boxes in zip(gt_frames, pred_frames, strict=True):
        if len(gt_boxes) > 8 or len(pred_boxes) > 8:
            raise ValueError("invalid")
        matches = match_boxes(gt_boxes, pred_boxes, iou_fn=iou_fn)
        tp += len(matches)
        fn += len(gt_boxes) - len(matches)
        fp += len(pred_boxes) - len(matches)
    gt_count = sum(len(f) for f in gt_frames)
    pred_count = sum(len(f) for f in pred_frames)
    if pred_count == 0 and gt_count > 0:
        return None, 0.0, None, tp, fn, fp
    if gt_count == 0 and pred_count == 0:
        return None, None, None, tp, fn, fp
    if gt_count == 0 and pred_count > 0:
        prec: float | None = 1.0
        rec: float | None = None
        f1: float | None = None
        return prec, rec, f1, tp, fn, fp
    precision = tp / pred_count if pred_count else None
    recall = tp / gt_count if gt_count else None
    if precision is None or recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1, tp, fn, fp
