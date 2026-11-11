# SPDX-License-Identifier: Apache-2.0

import math
from fractions import Fraction
from pathlib import Path

from annotation_qa_workbench.annotators import apply_annotator
from annotation_qa_workbench.geometry import iou_over_gt
from annotation_qa_workbench.metrics.kappa import kappa_is_po
from annotation_qa_workbench.metrics.mot import MotScore, score_sequence
from annotation_qa_workbench.scenes import idf1_potential_pairs_scene, load_scene, scene_frames

TOL = 1e-12


def test_iou_over_gt() -> None:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    af = scene_frames(apply_annotator(gt, "A"))
    golden = float(Fraction(32619964, 39538911))
    healthy = score_sequence(gf, af)
    assert isinstance(healthy, MotScore)
    assert healthy.motp_mean_iou is not None
    assert abs(float(healthy.motp_mean_iou) - golden) <= TOL
    mutant = score_sequence(gf, af, iou_fn=iou_over_gt)
    assert isinstance(mutant, MotScore)
    assert mutant.motp_mean_iou is not None and math.isfinite(float(mutant.motp_mean_iou))
    assert abs(float(mutant.motp_mean_iou) - golden) > TOL


def test_kappa_is_po() -> None:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    bf = scene_frames(apply_annotator(gt, "B"))
    gate = float(Fraction(1, 2))
    healthy = score_sequence(gf, bf)
    assert isinstance(healthy, MotScore)
    assert healthy.label_kappa is not None
    assert abs(float(healthy.label_kappa) - gate) <= TOL
    mutant = score_sequence(gf, bf, kappa_fn=kappa_is_po)
    assert isinstance(mutant, MotScore)
    assert mutant.label_kappa is not None and math.isfinite(float(mutant.label_kappa))
    assert abs(float(mutant.label_kappa) - gate) > TOL


def test_mota_skip_idsw() -> None:
    gt = load_scene(Path("fixtures/scenes/warehouse_v1.json"))
    gf = scene_frames(gt)
    cf = scene_frames(apply_annotator(gt, "C"))
    gate = float(Fraction(29, 30))
    healthy = score_sequence(gf, cf)
    assert isinstance(healthy, MotScore)
    assert healthy.mota is not None
    assert abs(float(healthy.mota) - gate) <= TOL
    mutant = score_sequence(gf, cf, skip_idsw=True)
    assert isinstance(mutant, MotScore)
    assert mutant.mota is not None and math.isfinite(float(mutant.mota))
    assert abs(float(mutant.mota) - gate) > TOL


def test_idf1_match_only() -> None:
    sc = idf1_potential_pairs_scene()
    gf = scene_frames(sc)
    pf = [[dict(b) for b in fr["boxes"]] for fr in sc["predictions"]]
    healthy = score_sequence(gf, pf, idf1_match_only=False)
    mutant = score_sequence(gf, pf, idf1_match_only=True)
    assert isinstance(healthy, MotScore) and isinstance(mutant, MotScore)
    assert abs(float(healthy.idf1) - 1.0) <= TOL
    assert mutant.idf1 is not None and math.isfinite(float(mutant.idf1))
    assert abs(float(mutant.idf1) - float(Fraction(1, 2))) <= TOL
    assert abs(float(mutant.idf1) - 1.0) > TOL
