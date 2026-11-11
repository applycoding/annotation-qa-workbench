# SPDX-License-Identifier: Apache-2.0

from annotation_qa_workbench.metrics.mot import MotScore, score_sequence
from annotation_qa_workbench.scenes import (
    generate_warehouse_v1,
    idf1_potential_pairs_scene,
    scene_frames,
)
from .fixtures_loader import assert_close, load_expected

TOL = 1e-12
_TOYS = load_expected("mot_toys.json")


def test_id_swap_toy() -> None:
    gt = []
    pr = []
    box = {"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": 1}
    box2 = {"x": 20, "y": 0, "w": 10, "h": 10, "class": "pallet", "track_id": 2}
    gt.append([dict(box, track_id=1), dict(box2, track_id=2)])
    pr.append([dict(box, track_id=1), dict(box2, track_id=2)])
    gt.append([dict(box, track_id=1), dict(box2, track_id=2)])
    pr.append([dict(box, track_id=2), dict(box2, track_id=1)])
    exp = _TOYS["id_swap_toy"]
    s = score_sequence(gt, pr)
    assert isinstance(s, MotScore)
    assert s.fn == exp["fn"] and s.fp == exp["fp"] and s.idsw == exp["idsw"]
    assert_close(s.mota, exp["mota"], TOL)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert_close(s.motp_mean_iou, exp["motp_mean_iou"], TOL)


def test_idf1_potential_pairs() -> None:
    sc = idf1_potential_pairs_scene()
    gf = scene_frames(sc)
    pf = [[dict(b) for b in fr["boxes"]] for fr in sc["predictions"]]
    exp = _TOYS["idf1_potential_pairs"]
    s = score_sequence(gf, pf)
    assert isinstance(s, MotScore)
    assert_close(s.idf1, exp["idf1"], TOL)
    assert s.idtp == exp["idtp"] and s.idfn == exp["idfn"] and s.idfp == exp["idfp"]
    assert_close(s.mota, exp["mota"], TOL)


def test_empty_you_vs_gt() -> None:
    gt = scene_frames(generate_warehouse_v1())
    empty = [[] for _ in gt]
    s = score_sequence(gt, empty)
    assert isinstance(s, MotScore)
    assert_close(s.mota, _TOYS["empty_you_vs_gt"]["mota"], TOL)
    assert_close(s.idf1, _TOYS["empty_you_vs_gt"]["idf1"], TOL)
    assert s.precision is None and s.f1 is None and s.label_kappa is None
    assert s.motp_mean_iou is None


def test_gt_zero_pred_positive() -> None:
    pr = [[{"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": 1}]]
    gt = [[]]
    s = score_sequence(gt, pr)
    assert isinstance(s, MotScore)
    assert s.mota is None and s.recall is None and s.idf1 is None


def test_empty_both() -> None:
    s = score_sequence([[]], [[]])
    assert isinstance(s, MotScore)
    assert_close(s.mota, _TOYS["empty_both"]["mota"], TOL)
    assert_close(s.idf1, _TOYS["empty_both"]["idf1"], TOL)
    assert s.motp_mean_iou is None
