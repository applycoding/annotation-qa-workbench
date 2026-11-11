# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from annotation_qa_workbench.scenes import generate_warehouse_v1, validate_scene


def test_validate_rejects_non_finite() -> None:
    sc = generate_warehouse_v1()
    sc["frames"][0]["boxes"][0]["x"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        validate_scene(sc)


def test_validate_rejects_duplicate_track_id() -> None:
    sc = generate_warehouse_v1()
    sc["frames"][0]["boxes"][0]["track_id"] = sc["frames"][0]["boxes"][1]["track_id"]
    with pytest.raises(ValueError, match="duplicate track id"):
        validate_scene(sc)


def test_warehouse_regen() -> None:
    committed = Path("fixtures/scenes/warehouse_v1.json").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        subprocess.run(
            [sys.executable, "-m", "annotation_qa_workbench.cli", "generate", "--out", str(out)],
            check=True,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(Path.cwd())},
        )
        fresh = (out / "warehouse_v1.json").read_text(encoding="utf-8")
        assert json.loads(fresh) == json.loads(committed)
