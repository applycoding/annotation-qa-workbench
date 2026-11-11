# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from annotation_qa_workbench.metrics.alpha import krippendorff_alpha_nominal
from annotation_qa_workbench.report import compute_warehouse_alphas
from annotation_qa_workbench.scenes import load_scene

from .fixtures_loader import load_expected, rational_float

TOL = 1e-12
_EXP = load_expected("alpha.json")


def test_ben_gerry() -> None:
    ben = list("aabbdcccedda")
    gerry = list("babbbccceddd")
    mat = [[b, g] for b, g in zip(ben, gerry, strict=True)]
    got = krippendorff_alpha_nominal(mat)
    assert got is not None
    assert abs(got - rational_float(_EXP["ben_gerry"])) <= TOL


def test_warehouse_alphas() -> None:
    scene = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    alphas = compute_warehouse_alphas(scene)
    wh = _EXP["warehouse"]
    for key in ("AC", "AB", "BC", "ABC", "GTABC"):
        assert abs(float(alphas[key]) - rational_float(wh[key])) <= TOL
