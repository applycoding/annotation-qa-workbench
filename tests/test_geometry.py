# SPDX-License-Identifier: Apache-2.0

import pytest

from annotation_qa_workbench.geometry import iou
from tests.fixtures_loader import load_expected, rational_float

TOL = 1e-12

_CASES = load_expected("iou_cases.json")["cases"]


def _box(xywh: list[float]) -> dict[str, float]:
    x, y, w, h = xywh
    return {"x": x, "y": y, "w": w, "h": h}


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_iou_cases(case: dict) -> None:
    got = iou(_box(case["a"]), _box(case["b"]))
    assert abs(got - rational_float(case)) <= TOL
