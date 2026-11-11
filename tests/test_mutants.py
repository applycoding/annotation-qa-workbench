# SPDX-License-Identifier: Apache-2.0

import math
from fractions import Fraction
from pathlib import Path

import pytest

from annotation_qa_workbench.annotators import apply_annotator
from annotation_qa_workbench.geometry import iou, iou_over_gt
from annotation_qa_workbench.match import match_boxes
from annotation_qa_workbench.metrics.kappa import cohen_kappa, kappa_is_po
from annotation_qa_workbench.metrics.mot import mota_skip_idsw, score_sequence
from annotation_qa_workbench.scenes import idf1_potential_pairs_scene, load_scene, scene_frames

TOL = 1e-12


def test_iou_over_gt() -> None:
    a = {"x": 20, "y": 60, "w": 40, "h": 40, "class": "robot", "track_id": 1}
    b = {"x": 22, "y": 61, "w": 40, "h": 40, "class": "robot", "track_id": 1}
    bad = iou_over_gt(a, b)
    good = iou(a, b)
    assert abs(bad - float(Fraction(741, 800))) <= TOL
    assert abs(good - float(Fraction(741, 859))) <= TOL
    with pytest.raises(AssertionError):
        assert abs(bad - float(Fraction(741, 859))) <= TOL


def test_kappa_is_po() -> None:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    bf = scene_frames(apply_annotator(gt, "B"))
    labels_a: list[str] = []
    labels_b: list[str] = []
    for gtb, prb in zip(gf, bf, strict=True):
        for gi, pj, _ in match_boxes(gtb, prb):
            labels_a.append(str(gtb[gi]["class"]))
            labels_b.append(str(prb[pj]["class"]))
    bad = kappa_is_po(labels_a, labels_b)
    good = cohen_kappa(labels_a, labels_b)
    assert bad is not None and abs(bad - 0.75) <= TOL
    assert good is not None and abs(float(good) - float(Fraction(1, 2))) <= TOL


def test_mota_skip_idsw() -> None:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    cf = scene_frames(apply_annotator(gt, "C"))
    healthy = score_sequence(gf, cf)
    mutant = mota_skip_idsw(gf, cf)
    assert healthy.mota is not None and abs(float(healthy.mota) - float(Fraction(29, 30))) <= TOL
    assert mutant.mota is not None and math.isfinite(float(mutant.mota))
    assert float(mutant.mota) == 1.0
    with pytest.raises(AssertionError):
        assert abs(float(mutant.mota) - float(Fraction(29, 30))) <= TOL


def test_idf1_match_only() -> None:
    sc = idf1_potential_pairs_scene()
    gf = scene_frames(sc)
    pf = [[dict(b) for b in fr["boxes"]] for fr in sc["predictions"]]
    healthy = score_sequence(gf, pf, idf1_match_only=False)
    mutant = score_sequence(gf, pf, idf1_match_only=True)
    assert abs(float(healthy.idf1) - 1.0) <= TOL
    assert mutant.idf1 is not None and abs(float(mutant.idf1) - float(Fraction(1, 2))) <= TOL
    with pytest.raises(AssertionError):
        assert abs(float(mutant.idf1) - 1.0) <= TOL
