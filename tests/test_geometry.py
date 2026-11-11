# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction

import pytest

from annotation_qa_workbench.geometry import iou

TOL = 1e-12

CASES = [
    ("identical_10", (0, 0, 10, 10), (0, 0, 10, 10), Fraction(1)),
    ("half_shift_x", (0, 0, 10, 10), (5, 0, 10, 10), Fraction(1, 3)),
    ("touching_edge", (0, 0, 10, 10), (10, 0, 10, 10), Fraction(0)),
    ("shift_2_1", (0, 0, 10, 10), (2, 1, 10, 10), Fraction(9, 16)),
    ("robot_40_shift", (20, 60, 40, 40), (22, 61, 40, 40), Fraction(741, 859)),
    ("pallet_50x30_shift", (140, 100, 50, 30), (142, 101, 50, 30), Fraction(58, 67)),
    ("cone_20_shift", (250, 40, 20, 20), (252, 41, 20, 20), Fraction(171, 229)),
    ("zero_width", (0, 0, 0, 10), (0, 0, 10, 10), Fraction(0)),
    ("containment", (0, 0, 10, 10), (2, 2, 4, 4), Fraction(4, 25)),
]


def _box(xywh: tuple[float, float, float, float]) -> dict[str, float]:
    x, y, w, h = xywh
    return {"x": x, "y": y, "w": w, "h": h}


@pytest.mark.parametrize("name,a,b,expected", CASES, ids=[c[0] for c in CASES])
def test_iou_cases(name: str, a: tuple, b: tuple, expected: Fraction) -> None:
    got = iou(_box(a), _box(b))
    assert abs(got - float(expected)) <= TOL
