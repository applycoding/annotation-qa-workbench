# SPDX-License-Identifier: Apache-2.0

"""Schema v1 report read, write, and validation."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from annotation_qa_workbench import constants
from annotation_qa_workbench.annotators import apply_annotator
from annotation_qa_workbench.metrics.alpha import krippendorff_alpha_nominal
from annotation_qa_workbench.metrics.mot import MotScore, score_sequence
from annotation_qa_workbench.scenes import load_scene, scene_frames

HONESTY = (
    "Synthetic data only. Simulation only. "
    "This file is recorded output; it is not a live model-training run "
    "and it does not contain real robot images."
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _mot_to_json(score: MotScore) -> dict[str, Any]:
    d = score.to_dict()
    for key, val in list(d.items()):
        if isinstance(val, float) and val is not None and math.isfinite(val):
            continue
        if val is None:
            continue
        if isinstance(val, bool):
            raise TypeError("boolean in score")
    return d


def per_class_iou_a(gt_frames: list[list[dict[str, Any]]], pred_frames: list[list[dict[str, Any]]]) -> dict[str, float]:
    from annotation_qa_workbench.match import match_boxes

    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for gt_boxes, pred_boxes in zip(gt_frames, pred_frames, strict=True):
        for gi, _pj, ov in match_boxes(gt_boxes, pred_boxes):
            cls = str(gt_boxes[gi]["class"])
            sums[cls] = sums.get(cls, 0.0) + ov
            counts[cls] = counts.get(cls, 0) + 1
    return {c: sums[c] / counts[c] for c in sums}


def compute_warehouse_scores(scene_path: Path) -> dict[str, Any]:
    gt_scene = load_scene(scene_path)
    gt_frames = scene_frames(gt_scene)
    scores: dict[str, Any] = {}
    for key in ("gt", "A", "B", "C"):
        pred_scene = gt_scene if key == "gt" else apply_annotator(gt_scene, key)  # type: ignore[arg-type]
        pred_frames = scene_frames(pred_scene)
        result = score_sequence(gt_frames, pred_frames)
        if isinstance(result, str):
            raise TypeError(result)
        entry = _mot_to_json(result)
        if key == "A":
            entry["per_class_iou"] = per_class_iou_a(gt_frames, pred_frames)
        scores[key] = entry

    alphas = compute_warehouse_alphas(gt_scene)
    return {
        "schema_version": 1,
        "sample": False,
        "git_sha": "0" * 40,
        "honesty": HONESTY,
        "scene": "warehouse_v1",
        "constants": {
            "iou_thresh": constants.IOU_THRESH,
            "width": constants.CANVAS_WIDTH,
            "height": constants.CANVAS_HEIGHT,
            "n_frames": constants.N_FRAMES,
            "assignment_protocol": constants.ASSIGNMENT_PROTOCOL,
        },
        "scores": scores,
        "alphas": alphas,
    }


def _class_after_match(
    gt_frames: list[list[dict[str, Any]]],
    pred_frames: list[list[dict[str, Any]]],
    frame_idx: int,
    track_id: int,
) -> str | None:
    from annotation_qa_workbench.match import match_boxes

    gt_boxes = gt_frames[frame_idx]
    pred_boxes = pred_frames[frame_idx]
    for gi, pj, _ in match_boxes(gt_boxes, pred_boxes):
        if int(gt_boxes[gi]["track_id"]) == track_id:
            return str(pred_boxes[pj]["class"])
    return None


def _gt_class(gt_frames: list[list[dict[str, Any]]], frame_idx: int, track_id: int) -> str | None:
    for g in gt_frames[frame_idx]:
        if int(g["track_id"]) == track_id:
            return str(g["class"])
    return None


def alpha_matrix(
    gt_frames: list[list[dict[str, Any]]],
    rater_frames: list[list[list[dict[str, Any]]]],
    *,
    include_gt: bool = False,
) -> list[list[str | None]]:
    units: list[list[str | None]] = []
    track_ids = [1, 2, 3]
    for frame_idx in range(len(gt_frames)):
        for tid in track_ids:
            row: list[str | None] = []
            if include_gt:
                row.append(_gt_class(gt_frames, frame_idx, tid))
            for pred_frames in rater_frames:
                row.append(_class_after_match(gt_frames, pred_frames, frame_idx, tid))
            units.append(row)
    return units


def compute_warehouse_alphas(gt_scene: dict[str, Any]) -> dict[str, float | None]:
    gt_frames = scene_frames(gt_scene)
    a = apply_annotator(gt_scene, "A")
    b = apply_annotator(gt_scene, "B")
    c = apply_annotator(gt_scene, "C")
    a_f, b_f, c_f = scene_frames(a), scene_frames(b), scene_frames(c)
    return {
        "AC": krippendorff_alpha_nominal(alpha_matrix(gt_frames, [a_f, c_f])),
        "AB": krippendorff_alpha_nominal(alpha_matrix(gt_frames, [a_f, b_f])),
        "BC": krippendorff_alpha_nominal(alpha_matrix(gt_frames, [b_f, c_f])),
        "ABC": krippendorff_alpha_nominal(alpha_matrix(gt_frames, [a_f, b_f, c_f])),
        "GTABC": krippendorff_alpha_nominal(
            alpha_matrix(gt_frames, [a_f, b_f, c_f], include_gt=True)
        ),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    def check_val(v: Any) -> Any:
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError("NaN in report")
        if isinstance(v, dict):
            return {k: check_val(x) for k, x in v.items()}
        if isinstance(v, list):
            return [check_val(x) for x in v]
        return v

    clean = check_val(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recompute_and_validate(
    report: dict[str, Any],
    scene_path: Path,
    *,
    require_ci: bool = False,
    expect_sha: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_version") != 1:
        errors.append("schema_version")
    if require_ci and report.get("sample") is not False:
        errors.append("sample")
    if require_ci:
        sha = str(report.get("git_sha", ""))
        if not SHA_RE.match(sha) or sha == "0" * 40:
            errors.append("git_sha")
        if expect_sha and sha != expect_sha:
            errors.append("git_sha_mismatch")
    if report.get("honesty") != HONESTY:
        errors.append("honesty")
    fresh = compute_warehouse_scores(scene_path)
    for key in ("gt", "A", "B", "C"):
        if key not in report.get("scores", {}):
            errors.append(f"missing {key}")
            continue
        for field, expected in fresh["scores"][key].items():
            if field not in report["scores"][key]:
                errors.append(f"missing field {key}.{field}")
                continue
            got = report["scores"][key][field]
            if expected is None:
                if got is not None:
                    errors.append(f"{key}.{field}")
            elif isinstance(got, bool):
                errors.append(f"{key}.{field}")
            elif isinstance(expected, (int, float)) and isinstance(got, (int, float)):
                if isinstance(expected, int):
                    if got != expected:
                        errors.append(f"{key}.{field}")
                elif abs(float(got) - float(expected)) > 1e-12:
                    errors.append(f"{key}.{field}")
    for key, expected in fresh["alphas"].items():
        got = report.get("alphas", {}).get(key)
        if expected is None:
            if got is not None:
                errors.append(f"alpha {key}")
        elif got is None or abs(float(got) - float(expected)) > 1e-12:
            errors.append(f"alpha {key}")
    return errors


def load_report(path: Path) -> dict[str, Any]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("invalid report")
    return data
