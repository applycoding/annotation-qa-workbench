# SPDX-License-Identifier: Apache-2.0

from annotation_qa_workbench.metrics.kappa import cohen_kappa
from .fixtures_loader import load_expected, rational_float

TOL = 1e-12
_EXP = load_expected("kappa_cases.json")


def test_kappa_half() -> None:
    a = ["A", "A", "A", "B"]
    b = ["A", "A", "B", "B"]
    assert abs(float(cohen_kappa(a, b)) - rational_float(_EXP["half"])) <= TOL


def test_kappa_zero() -> None:
    a = ["A", "A", "B", "B"]
    b = ["A", "B", "A", "B"]
    assert abs(float(cohen_kappa(a, b))) <= TOL


def test_kappa_one() -> None:
    a = ["A", "B", "C"]
    b = ["A", "B", "C"]
    assert float(cohen_kappa(a, b)) == rational_float(_EXP["one"])


def test_kappa_null_same_category() -> None:
    assert cohen_kappa(["A", "A"], ["A", "A"]) is None


def test_kappa_two_five() -> None:
    labels_a: list[str] = []
    labels_b: list[str] = []
    table = [[20, 5], [10, 15]]
    for i, row in enumerate(table):
        cat = "A" if i == 0 else "B"
        for j, count in enumerate(row):
            icat = "A" if j == 0 else "B"
            labels_a.extend([cat] * count)
            labels_b.extend([icat] * count)
    assert abs(float(cohen_kappa(labels_a, labels_b)) - rational_float(_EXP["two_five"])) <= TOL
