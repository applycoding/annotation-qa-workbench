# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction
from pathlib import Path

from annotation_qa_workbench.annotators import apply_annotator
from annotation_qa_workbench.geometry import iou
from annotation_qa_workbench.match import match_boxes
from annotation_qa_workbench.metrics.mot import MotScore, score_sequence
from annotation_qa_workbench.scenes import load_scene, scene_frames
from tests.fixtures_loader import assert_close, load_expected

TOL = 1e-12
_GATES = load_expected("warehouse_gates.json")


def _score(name: str) -> MotScore:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    pred = gf if name == "gt" else scene_frames(apply_annotator(gt, name))  # type: ignore[arg-type]
    out = score_sequence(gf, pred)
    assert isinstance(out, MotScore)
    return out


def test_annotator_a() -> None:
    exp = _GATES["A"]
    s = _score("A")
    assert_close(s.mota, exp["mota"], TOL)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert_close(s.label_kappa, exp["label_kappa"], TOL)
    assert_close(s.motp_mean_iou, exp["motp_mean_iou"], TOL)
    gt = scene_frames(load_scene(Path("fixtures/scenes/warehouse_v1.json")))
    af = scene_frames(apply_annotator(load_scene(Path("fixtures/scenes/warehouse_v1.json")), "A"))
    for fr_gt, fr_a in zip(gt, af, strict=True):
        for gi, pj, _ in match_boxes(fr_gt, fr_a):
            cls = str(fr_gt[gi]["class"])
            ov = iou(fr_gt[gi], fr_a[pj])
            num, den = exp["per_class_iou"][cls]
            assert abs(ov - float(Fraction(num, den))) <= TOL


def test_annotator_b() -> None:
    exp = _GATES["B"]
    s = _score("B")
    assert_close(s.mota, exp["mota"], TOL)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert_close(s.label_kappa, exp["label_kappa"], TOL)
    assert s.fn == exp["fn"] and s.fp == exp["fp"]
    assert_close(s.precision, exp["precision"], TOL)
    assert_close(s.recall, exp["recall"], TOL)
    assert_close(s.f1, exp["f1"], TOL)


def test_annotator_c() -> None:
    exp = _GATES["C"]
    s = _score("C")
    assert_close(s.mota, exp["mota"], TOL)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert_close(s.label_kappa, exp["label_kappa"], TOL)
    assert s.idsw == exp["idsw"]
    assert s.idtp == exp["idtp"] and s.idfn == exp["idfn"] and s.idfp == exp["idfp"]


def test_gt_self() -> None:
    exp = _GATES["gt"]
    s = _score("gt")
    assert_close(s.mota, exp["mota"], TOL)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert_close(s.label_kappa, exp["label_kappa"], TOL)
    assert_close(s.motp_mean_iou, exp["motp_mean_iou"], TOL)
    assert s.matches == exp["matches"]
