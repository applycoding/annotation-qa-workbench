# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
import tempfile
from pathlib import Path


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
