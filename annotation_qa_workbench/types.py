# SPDX-License-Identifier: Apache-2.0

from typing import Any, TypedDict


class BoxDict(TypedDict):
    x: float
    y: float
    w: float
    h: float
    track_id: int


def track_id(box: dict[str, Any]) -> int:
    return int(box["track_id"])
