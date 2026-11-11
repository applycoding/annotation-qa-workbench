# SPDX-License-Identifier: Apache-2.0

"""Min-cost assignment (Kuhn-Munkres) and IoU-threshold box matching."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence

from annotation_qa_workbench.constants import FORBIDDEN_COST, IOU_THRESH, MAX_BOXES_PER_FRAME
from annotation_qa_workbench.geometry import iou

IoUFn = Callable[..., float]


def _pad_cost_matrix(cost: list[list[float]]) -> list[list[float]]:
    n_rows = len(cost)
    n_cols = len(cost[0]) if cost else 0
    size = max(n_rows, n_cols)
    if size == 0:
        return []
    padded = [[0.0] * size for _ in range(size)]
    for i in range(n_rows):
        for j in range(n_cols):
            padded[i][j] = cost[i][j]
    return padded


def min_cost_assignment(cost_matrix: Sequence[Sequence[float]]) -> list[tuple[int, int, float]]:
    """Kuhn-Munkres on a rectangular cost matrix; dummies pad to a square."""
    if not cost_matrix:
        return []
    n_rows = len(cost_matrix)
    n_cols = len(cost_matrix[0])
    padded = _pad_cost_matrix([list(row) for row in cost_matrix])
    n = len(padded)
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = padded[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    result: list[tuple[int, int, float]] = []
    for j in range(1, n + 1):
        i = p[j]
        if i == 0:
            continue
        row = i - 1
        col = j - 1
        if row < n_rows and col < n_cols:
            result.append((row, col, padded[row][col]))
    result.sort(key=lambda t: (t[0], t[1]))
    return result


def exhaustive_min_cost(cost_matrix: Sequence[Sequence[float]]) -> list[tuple[int, int, float]]:
    """Brute-force oracle for small square problems (n <= 6)."""
    n_rows = len(cost_matrix)
    n_cols = len(cost_matrix[0]) if cost_matrix else 0
    if n_rows == 0 or n_cols == 0:
        return []
    size = max(n_rows, n_cols)
    best_cost = float("inf")
    best_pairs: tuple[tuple[int, int], ...] = ()

    cols = list(range(n_cols))
    extra = list(range(n_cols, size))
    for perm in itertools.permutations(cols + extra, size):
        pairs: list[tuple[int, int]] = []
        total = 0.0
        for r in range(n_rows):
            c = perm[r]
            if c >= n_cols:
                pairs.append((r, -1))
                continue
            total += float(cost_matrix[r][c])
            pairs.append((r, c))
        real = [(r, c) for r, c in pairs if c >= 0]
        real.sort()
        key = tuple(real)
        if total < best_cost or (total == best_cost and key < best_pairs):
            best_cost = total
            best_pairs = key
    return [(r, c, float(cost_matrix[r][c])) for r, c in best_pairs]


def match_boxes(
    gt_boxes: Sequence[dict[str, object]],
    pred_boxes: Sequence[dict[str, object]],
    thresh: float = IOU_THRESH,
    iou_fn: IoUFn = iou,
) -> list[tuple[int, int, float]]:
    """Match predictions to ground truth by min-cost IoU assignment."""
    if len(gt_boxes) > MAX_BOXES_PER_FRAME or len(pred_boxes) > MAX_BOXES_PER_FRAME:
        raise ValueError("invalid")
    if not gt_boxes and not pred_boxes:
        return []
    n_gt = len(gt_boxes)
    n_pr = len(pred_boxes)
    if n_gt == 0 or n_pr == 0:
        return []
    cost: list[list[float]] = []
    for g in gt_boxes:
        row: list[float] = []
        for p in pred_boxes:
            overlap = iou_fn(g, p)
            if overlap >= thresh:
                row.append(1.0 - overlap)
            else:
                row.append(FORBIDDEN_COST)
        cost.append(row)
    assigned = min_cost_assignment(cost)
    return [(i, j, overlap_iou(gt_boxes[i], pred_boxes[j], iou_fn))
            for i, j, c in assigned if c < FORBIDDEN_COST]


def overlap_iou(
    a: dict[str, object],
    b: dict[str, object],
    iou_fn: IoUFn = iou,
) -> float:
    return float(iou_fn(a, b))
