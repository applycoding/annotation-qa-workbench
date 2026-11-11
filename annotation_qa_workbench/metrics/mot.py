# SPDX-License-Identifier: Apache-2.0

"""CLEAR-style teaching MOTA, overlap MOTP, and standard IDF1."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

from annotation_qa_workbench.constants import IOU_THRESH, MAX_BOXES_PER_FRAME, MAX_IDENTITIES
from annotation_qa_workbench.geometry import iou
from annotation_qa_workbench.match import match_boxes, min_cost_assignment
from annotation_qa_workbench.metrics.detection import precision_recall_f1
from annotation_qa_workbench.metrics.kappa import cohen_kappa
from annotation_qa_workbench.types import track_id

IoUFn = Callable[..., float]


@dataclass
class MotScore:
    fn: int
    fp: int
    idsw: int
    gt_count: int
    pred_count: int
    matches: int
    mota: float | None
    motp_mean_iou: float | None
    idtp: int
    idfn: int
    idfp: int
    idf1: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    label_kappa: float | None
    n_matched: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _count_identity_pairs(
    gt_frames: Sequence[Sequence[dict[str, object]]],
    pred_frames: Sequence[Sequence[dict[str, object]]],
    thresh: float,
    iou_fn: IoUFn,
    match_only: bool,
) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = {}
    for gt_boxes, pred_boxes in zip(gt_frames, pred_frames, strict=True):
        if len(gt_boxes) > MAX_BOXES_PER_FRAME or len(pred_boxes) > MAX_BOXES_PER_FRAME:
            raise ValueError("invalid")
        if match_only:
            pairs = match_boxes(gt_boxes, pred_boxes, thresh=thresh, iou_fn=iou_fn)
            for gi, pj, _ in pairs:
                g_id = track_id(gt_boxes[gi])
                p_id = track_id(pred_boxes[pj])
                key = (g_id, p_id)
                counts[key] = counts.get(key, 0) + 1
        else:
            for gi, g in enumerate(gt_boxes):
                for pj, p in enumerate(pred_boxes):
                    if iou_fn(g, p) >= thresh:
                        g_id = track_id(g)
                        p_id = track_id(p)
                        key = (g_id, p_id)
                        counts[key] = counts.get(key, 0) + 1
    return counts


def score_sequence(
    gt_frames: list[list[dict[str, object]]],
    pred_frames: list[list[dict[str, object]]],
    thresh: float = IOU_THRESH,
    iou_fn: IoUFn | None = None,
    idf1_match_only: bool = False,
    skip_idsw: bool = False,
) -> MotScore | str:
    if iou_fn is None:
        iou_fn = iou

    gt_count = sum(len(f) for f in gt_frames)
    pred_count = sum(len(f) for f in pred_frames)

    for gt_boxes, pred_boxes in zip(gt_frames, pred_frames, strict=True):
        if len(gt_boxes) > MAX_BOXES_PER_FRAME or len(pred_boxes) > MAX_BOXES_PER_FRAME:
            return "invalid"

    if gt_count == 0 and pred_count == 0:
        return MotScore(
            fn=0,
            fp=0,
            idsw=0,
            gt_count=0,
            pred_count=0,
            matches=0,
            mota=1.0,
            motp_mean_iou=None,
            idtp=0,
            idfn=0,
            idfp=0,
            idf1=1.0,
            precision=None,
            recall=None,
            f1=None,
            label_kappa=None,
            n_matched=0,
        )

    if gt_count == 0 and pred_count > 0:
        precision, recall, f1, _tp, _fn, fp = precision_recall_f1(
            gt_frames, pred_frames, iou_fn=iou_fn
        )
        return MotScore(
            fn=0,
            fp=fp,
            idsw=0,
            gt_count=0,
            pred_count=pred_count,
            matches=0,
            mota=None,
            motp_mean_iou=None,
            idtp=0,
            idfn=0,
            idfp=pred_count,
            idf1=None,
            precision=precision,
            recall=recall,
            f1=f1,
            label_kappa=None,
            n_matched=0,
        )

    fn = 0
    fp = 0
    matches = 0
    idsw = 0
    iou_sum = 0.0
    matched_label_a: list[str] = []
    matched_label_b: list[str] = []
    last_pred_for_gt: dict[int, int] = {}

    for gt_boxes, pred_boxes in zip(gt_frames, pred_frames, strict=True):
        pairs = match_boxes(gt_boxes, pred_boxes, thresh=thresh, iou_fn=iou_fn)
        matched_gt = {i for i, _j, _ in pairs}
        matched_pr = {j for _i, j, _ in pairs}
        fn += len(gt_boxes) - len(matched_gt)
        fp += len(pred_boxes) - len(matched_pr)
        matches += len(pairs)
        for gi, pj, ov in pairs:
            iou_sum += ov
            g = gt_boxes[gi]
            p = pred_boxes[pj]
            matched_label_a.append(str(g["class"]))
            matched_label_b.append(str(p["class"]))
            gid = track_id(g)
            pid = track_id(p)
            if not skip_idsw and gid in last_pred_for_gt and last_pred_for_gt[gid] != pid:
                idsw += 1
            last_pred_for_gt[gid] = pid

    motp_mean_iou = iou_sum / matches if matches else None

    if not skip_idsw:
        mota_val = 1.0 - (fn + fp + idsw) / gt_count
    else:
        mota_val = 1.0 - (fn + fp) / gt_count

    try:
        counts = _count_identity_pairs(
            gt_frames, pred_frames, thresh, iou_fn, match_only=idf1_match_only
        )
    except ValueError:
        return "invalid"

    gt_ids = {track_id(b) for frame in gt_frames for b in frame}
    pred_ids = {track_id(b) for frame in pred_frames for b in frame}
    if len(gt_ids) > MAX_IDENTITIES or len(pred_ids) > MAX_IDENTITIES:
        return "invalid"

    gt_list = sorted(gt_ids)
    pr_list = sorted(pred_ids)
    cost: list[list[float]] = []
    for gt_id in gt_list:
        cost.append([-float(counts.get((gt_id, pred_id), 0)) for pred_id in pr_list])
    assigned = min_cost_assignment(cost)
    idtp = 0
    for i, j, _ in assigned:
        idtp += counts.get((gt_list[i], pr_list[j]), 0)
    idfn = gt_count - idtp
    idfp = pred_count - idtp
    denom = 2 * idtp + idfp + idfn
    idf1 = (2 * idtp / denom) if denom else None

    mota_out: float | None
    idf1_out: float | None
    kappa: float | None
    motp_out: float | None
    if pred_count == 0 and gt_count > 0:
        precision = None
        recall = 0.0
        f1 = None
        mota_out = 0.0
        idf1_out = 0.0
        kappa = None
        motp_out = None
    else:
        precision, recall, f1, _tp, _fn2, _fp2 = precision_recall_f1(
            gt_frames, pred_frames, iou_fn=iou_fn
        )
        mota_out = mota_val
        idf1_out = idf1
        kappa = cohen_kappa(matched_label_a, matched_label_b)
        motp_out = motp_mean_iou

    return MotScore(
        fn=fn,
        fp=fp,
        idsw=idsw,
        gt_count=gt_count,
        pred_count=pred_count,
        matches=matches,
        mota=mota_out,
        motp_mean_iou=motp_out,
        idtp=idtp,
        idfn=idfn,
        idfp=idfp,
        idf1=idf1_out,
        precision=precision,
        recall=recall,
        f1=f1,
        label_kappa=kappa,
        n_matched=matches,
    )


def mota_skip_idsw(gt_frames: list[list[dict[str, object]]], pred_frames: list[list[dict[str, object]]]) -> MotScore | str:
    """Mutant entry: MOTA without identity-switch penalty."""
    return score_sequence(gt_frames, pred_frames, skip_idsw=True)
