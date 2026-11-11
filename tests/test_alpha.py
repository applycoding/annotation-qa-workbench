# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction
from pathlib import Path

from annotation_qa_workbench.metrics.alpha import krippendorff_alpha_nominal
from annotation_qa_workbench.report import compute_warehouse_alphas
from annotation_qa_workbench.scenes import load_scene

TOL = 1e-12


def test_ben_gerry() -> None:
    ben = list("aabbdcccedda")
    gerry = list("babbbccceddd")
    mat = [[b, g] for b, g in zip(ben, gerry, strict=True)]
    got = krippendorff_alpha_nominal(mat)
    assert got is not None
    assert abs(got - float(Fraction(155, 224))) <= TOL


def test_warehouse_alphas() -> None:
    scene = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    alphas = compute_warehouse_alphas(scene)
    assert abs(float(alphas["AC"]) - 1.0) <= TOL
    assert abs(float(alphas["AB"]) - float(Fraction(71, 150))) <= TOL
    assert abs(float(alphas["BC"]) - float(Fraction(71, 150))) <= TOL
    assert abs(float(alphas["ABC"]) - float(Fraction(671, 830))) <= TOL
    assert abs(float(alphas["GTABC"]) - float(Fraction(457, 530))) <= TOL
