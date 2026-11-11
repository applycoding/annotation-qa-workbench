# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction
from pathlib import Path

from annotation_qa_workbench.annotators import apply_annotator
from annotation_qa_workbench.geometry import iou
from annotation_qa_workbench.match import match_boxes
from annotation_qa_workbench.metrics.mot import score_sequence
from annotation_qa_workbench.scenes import load_scene, scene_frames

TOL = 1e-12


def _score(name: str):
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    pred = gf if name == "gt" else scene_frames(apply_annotator(gt, name))  # type: ignore[arg-type]
    return score_sequence(gf, pred)


def test_annotator_a() -> None:
    s = _score("A")
    assert s.mota == 1 and s.idf1 == 1 and s.label_kappa == 1
    assert abs(float(s.motp_mean_iou) - float(Fraction(32619964, 39538911))) <= TOL
    gt = scene_frames(load_scene(Path("fixtures/scenes/warehouse_v1.json")))
    af = scene_frames(apply_annotator(load_scene(Path("fixtures/scenes/warehouse_v1.json")), "A"))
    for fr_gt, fr_a in zip(gt, af, strict=True):
        for gi, pj, _ in match_boxes(fr_gt, fr_a):
            cls = fr_gt[gi]["class"]
            ov = iou(fr_gt[gi], fr_a[pj])
            if cls == "robot":
                assert abs(ov - float(Fraction(741, 859))) <= TOL
            elif cls == "pallet":
                assert abs(ov - float(Fraction(58, 67))) <= TOL
            else:
                assert abs(ov - float(Fraction(171, 229))) <= TOL


def test_annotator_b() -> None:
    s = _score("B")
    assert abs(float(s.mota) - float(Fraction(2, 3))) <= TOL
    assert abs(float(s.idf1) - float(Fraction(4, 5))) <= TOL
    assert abs(float(s.label_kappa) - float(Fraction(1, 2))) <= TOL
    assert s.fn == 20 and s.fp == 0
    assert s.precision == 1
    assert abs(float(s.recall) - float(Fraction(2, 3))) <= TOL
    assert abs(float(s.f1) - float(Fraction(4, 5))) <= TOL


def test_annotator_c() -> None:
    s = _score("C")
    assert abs(float(s.mota) - float(Fraction(29, 30))) <= TOL
    assert abs(float(s.idf1) - float(Fraction(2, 3))) <= TOL
    assert s.label_kappa == 1 and s.idsw == 2
    assert s.idtp == 40 and s.idfn == 20 and s.idfp == 20


def test_gt_self() -> None:
    s = _score("gt")
    assert s.mota == 1 and s.idf1 == 1 and s.label_kappa == 1
    assert float(s.motp_mean_iou) == 1.0 and s.matches == 60
