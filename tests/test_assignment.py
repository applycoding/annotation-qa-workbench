# SPDX-License-Identifier: Apache-2.0

import time

import pytest

from annotation_qa_workbench.constants import FORBIDDEN_COST
from annotation_qa_workbench.match import exhaustive_min_cost, match_boxes, min_cost_assignment
from annotation_qa_workbench.metrics.mot import score_sequence


def _boxes_from_iou_matrix(ious: list[list[float]]) -> tuple[list[dict], list[dict]]:
    gt, pr = [], []
    for i, row in enumerate(ious):
        gt.append({"x": i * 20, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": i + 1})
    for j in range(len(ious[0])):
        pr.append({"x": j * 20, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": j + 1})
    return gt, pr


def test_exhaustive_beats_greedy() -> None:
    cost = [[1 - 0.55, 1 - 0.54], [1 - 0.54, FORBIDDEN_COST]]
    got = min_cost_assignment(cost)
    pairs = {(i, j) for i, j, _ in got}
    assert pairs == {(0, 1), (1, 0)}


@pytest.mark.parametrize(
    "ious",
    [
        [[0.55, 0.54], [0.54, 0.10]],
        [[1.0, 0.0], [0.0, 1.0]],
        [[0.9, 0.1], [0.1, 0.9]],
        [[0.6], [0.7]],
    ],
)
def test_hungarian_matches_exhaustive(ious: list[list[float]]) -> None:
    n, m = len(ious), len(ious[0])
    if max(n, m) > 6:
        pytest.skip("oracle size")
    cost: list[list[float]] = []
    for row in ious:
        cost.append([FORBIDDEN_COST if v < 0.5 else 1 - v for v in row])
    h = {(i, j) for i, j, _ in min_cost_assignment(cost)}
    e = {(i, j) for i, j, _ in exhaustive_min_cost(cost)}
    assert h == e


def test_n9_invalid() -> None:
    gt = [
        {"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": i}
        for i in range(9)
    ]
    pr = [{"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": 1}]
    with pytest.raises(ValueError, match="invalid"):
        match_boxes(gt, pr)


def test_identity_cap_33() -> None:
    frames = [
        [
            {"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": i + 1}
            for i in range(33)
        ]
    ]
    empty: list[list[dict]] = [[]]
    out = score_sequence(empty, frames)
    assert out == "invalid"


def test_fresh_ids_24() -> None:
    frames_gt = [[{"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": 1}] * 3] * 8
    frames_gt = [[dict(b) for b in fr] for fr in frames_gt]
    frames_pr = []
    pid = 1
    for _ in range(8):
        frames_pr.append(
            [
                {"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": pid + k}
                for k in range(3)
            ]
        )
        pid += 3
    start = time.perf_counter()
    out = score_sequence(frames_gt, frames_pr)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    assert isinstance(out, object) and out != "invalid"
    assert getattr(out, "idf1", None) is not None
