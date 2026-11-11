# SPDX-License-Identifier: Apache-2.0

"""Half-open axis-aligned box IoU."""

from __future__ import annotations

import math
from collections.abc import Mapping


def _finite(v: float) -> bool:
    return math.isfinite(v)


def box_area(w: float, h: float) -> float:
    if w <= 0 or h <= 0:
        return 0.0
    return w * h


def iou(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Intersection-over-union for xywh boxes in half-open pixel coordinates."""
    ax, ay, aw, ah = float(a["x"]), float(a["y"]), float(a["w"]), float(a["h"])
    bx, by, bw, bh = float(b["x"]), float(b["y"]), float(b["w"]), float(b["h"])
    for v in (ax, ay, aw, ah, bx, by, bw, bh):
        if not _finite(v):
            return 0.0
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0.0
    inter_w = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    inter_h = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = inter_w * inter_h
    union = box_area(aw, ah) + box_area(bw, bh) - inter
    if union <= 0:
        return 0.0
    return inter / union


def iou_over_gt(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Mutant: intersection divided by area of the first box only."""
    ax, ay, aw, ah = float(a["x"]), float(a["y"]), float(a["w"]), float(a["h"])
    bx, by, bw, bh = float(b["x"]), float(b["y"]), float(b["w"]), float(b["h"])
    for v in (ax, ay, aw, ah, bx, by, bw, bh):
        if not _finite(v):
            return 0.0
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0.0
    inter_w = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    inter_h = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = inter_w * inter_h
    denom = box_area(aw, ah)
    if denom <= 0:
        return 0.0
    return inter / denom
