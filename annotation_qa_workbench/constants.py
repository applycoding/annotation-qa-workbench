# SPDX-License-Identifier: Apache-2.0

"""Shared constants for the warehouse demo and scorer."""

IOU_THRESH: float = 0.5
MAX_BOXES_PER_FRAME: int = 8
MAX_IDENTITIES: int = 32
CANVAS_WIDTH: int = 640
CANVAS_HEIGHT: int = 360
N_FRAMES: int = 20
CLASSES: frozenset[str] = frozenset({"robot", "pallet", "cone"})
FORBIDDEN_COST: float = 1e9
ASSIGNMENT_PROTOCOL: str = "per_frame_min_cost_iou"
