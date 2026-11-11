# SPDX-License-Identifier: Apache-2.0

"""Locked annotator traces A, B, and C."""

from __future__ import annotations

import copy
from typing import Any, Literal

AnnotatorName = Literal["A", "B", "C"]


def apply_annotator(scene: dict[str, Any], name: AnnotatorName) -> dict[str, Any]:
    out = copy.deepcopy(scene)
    if name == "A":
        for fr in out["frames"]:
            for b in fr["boxes"]:
                b["x"] = float(b["x"]) + 2.0
                b["y"] = float(b["y"]) + 1.0
        return out
    if name == "B":
        for fr in out["frames"]:
            kept = []
            for b in fr["boxes"]:
                if b["class"] == "cone":
                    continue
                nb = dict(b)
                if fr["index"] >= 10 and nb["class"] == "pallet":
                    nb["class"] = "robot"
                kept.append(nb)
            fr["boxes"] = kept
        return out
    if name == "C":
        for fr in out["frames"]:
            if fr["index"] >= 10:
                for b in fr["boxes"]:
                    tid = int(b["track_id"])
                    if tid == 1:
                        b["track_id"] = 2
                    elif tid == 2:
                        b["track_id"] = 1
        return out
    raise ValueError(f"unknown annotator {name}")
