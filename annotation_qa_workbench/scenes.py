# SPDX-License-Identifier: Apache-2.0

"""Synthetic scene generation and validation."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from annotation_qa_workbench.constants import CANVAS_HEIGHT, CANVAS_WIDTH, CLASSES, N_FRAMES


def _box(x: float, y: float, w: float, h: float, cls: str, track_id: int) -> dict[str, Any]:
    return {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "class": cls,
        "track_id": track_id,
    }


def generate_warehouse_v1() -> dict[str, Any]:
    frames: list[dict[str, Any]] = []
    for frame in range(N_FRAMES):
        t = frame / 19.0
        robot_x = 20.0 + (200.0 - 20.0) * t
        cone_y = 40.0 + (120.0 - 40.0) * t
        boxes = [
            _box(robot_x, 60.0, 40.0, 40.0, "robot", 1),
            _box(140.0, 100.0, 50.0, 30.0, "pallet", 2),
            _box(250.0, cone_y, 20.0, 20.0, "cone", 3),
        ]
        frames.append({"index": frame, "boxes": boxes})
    return {
        "name": "warehouse_v1",
        "width": CANVAS_WIDTH,
        "height": CANVAS_HEIGHT,
        "frames": frames,
    }


def scene_frames(scene: dict[str, Any]) -> list[list[dict[str, Any]]]:
    out: list[list[dict[str, Any]]] = []
    for fr in scene["frames"]:
        out.append([dict(b) for b in fr["boxes"]])
    return out


def validate_scene(scene: dict[str, Any]) -> None:
    if scene.get("width") != CANVAS_WIDTH or scene.get("height") != CANVAS_HEIGHT:
        raise ValueError("invalid scene dimensions")
    if len(scene.get("frames", [])) != N_FRAMES:
        raise ValueError("invalid frame count")
    for fr in scene["frames"]:
        seen: set[int] = set()
        if len(fr["boxes"]) > 8:
            raise ValueError("invalid")
        for b in fr["boxes"]:
            for key in ("x", "y", "w", "h"):
                v = float(b[key])
                if not math.isfinite(v):
                    raise ValueError("non-finite coordinate")
            if b["class"] not in CLASSES:
                raise ValueError("invalid class")
            tid = int(b["track_id"])
            if tid in seen:
                raise ValueError("duplicate track id")
            seen.add(tid)


def write_scene(path: Path, scene: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scene, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_scene(path: Path) -> dict[str, Any]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("invalid scene json")
    return data


def idf1_potential_pairs_scene() -> dict[str, Any]:
    """Locked discriminating IDF1 fixture (2 frames)."""
    f0_gt = [
        _box(0, 0, 100, 100, "robot", 1),
        _box(40, 0, 100, 100, "pallet", 2),
    ]
    f0_pr = [
        _box(0, 0, 100, 100, "robot", 10),
        _box(40, 0, 100, 100, "pallet", 20),
    ]
    f1_gt = copy.deepcopy(f0_gt)
    f1_pr = [
        _box(33, 0, 100, 100, "robot", 10),
        _box(7, 0, 100, 100, "pallet", 20),
    ]
    return {
        "name": "idf1_potential_pairs",
        "width": 200,
        "height": 100,
        "frames": [
            {"index": 0, "boxes": f0_gt},
            {"index": 1, "boxes": f1_gt},
        ],
        "predictions": [
            {"index": 0, "boxes": f0_pr},
            {"index": 1, "boxes": f1_pr},
        ],
    }
