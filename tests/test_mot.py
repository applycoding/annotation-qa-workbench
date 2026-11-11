# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction

from annotation_qa_workbench.metrics.mot import score_sequence
from annotation_qa_workbench.scenes import (
    generate_warehouse_v1,
    idf1_potential_pairs_scene,
    scene_frames,
)

TOL = 1e-12


def test_id_swap_toy() -> None:
    gt = []
    pr = []
    box = {"x": 0, "y": 0, "w": 10, "h": 10, "class": "robot", "track_id": 1}
    box2 = {"x": 20, "y": 0, "w": 10, "h": 10, "class": "pallet", "track_id": 2}
    gt.append([dict(box, track_id=1), dict(box2, track_id=2)])
    pr.append([dict(box, track_id=1), dict(box2, track_id=2)])
    gt.append([dict(box, track_id=1), dict(box2, track_id=2)])
    pr.append([dict(box, track_id=2), dict(box2, track_id=1)])
    s = score_sequence(gt, pr)
    assert s.fn == 0 and s.fp == 0 and s.idsw == 2 and s.gt_count == 4
    assert abs(float(s.mota) - float(Fraction(1, 2))) <= TOL
    assert abs(float(s.idf1) - float(Fraction(1, 2))) <= TOL
    assert float(s.motp_mean_iou) == 1.0


def test_idf1_potential_pairs() -> None:
    sc = idf1_potential_pairs_scene()
    gf = scene_frames(sc)
    pf = [[dict(b) for b in fr["boxes"]] for fr in sc["predictions"]]
    s = score_sequence(gf, pf)
    assert abs(float(s.idf1) - 1.0) <= TOL
    assert s.idtp == 4 and s.idfn == 0 and s.idfp == 0
    assert abs(float(s.mota) - float(Fraction(1, 2))) <= TOL


def test_empty_you_vs_gt() -> None:
    gt = scene_frames(generate_warehouse_v1())
    empty = [[] for _ in gt]
    s = score_sequence(gt, empty)
    assert s.mota == 0.0 and s.idf1 == 0.0
    assert s.precision is None and s.f1 is None and s.label_kappa is None
    assert s.motp_mean_iou is None
