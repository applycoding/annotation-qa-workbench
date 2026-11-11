# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

EXPECTED_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "expected"


def load_expected(name: str) -> Any:
    return json.loads((EXPECTED_DIR / name).read_text(encoding="utf-8"))


def rational_float(entry: dict[str, Any]) -> float:
    if "rational" in entry:
        num, den = entry["rational"]
        return float(Fraction(int(num), int(den)))
    return float(entry["float64"])


def assert_close(actual: float | None, entry: dict[str, Any], tol: float = 1e-12) -> None:
    assert actual is not None
    assert abs(float(actual) - rational_float(entry)) <= tol
