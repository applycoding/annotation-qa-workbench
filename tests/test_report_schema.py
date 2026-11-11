# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from annotation_qa_workbench.report import (
    compute_warehouse_scores,
    load_report,
    recompute_and_validate,
    write_report,
)

TOL = 1e-12


def test_ci_report_schema() -> None:
    scene = Path("fixtures/scenes/warehouse_v1.json")
    sha = "a" * 40
    payload = compute_warehouse_scores(scene)
    payload["git_sha"] = sha
    payload["sample"] = False
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.json"
        write_report(path, payload)
        report = load_report(path)
        assert report["schema_version"] == 1 and report["sample"] is False
        for key in ("gt", "A", "B", "C"):
            assert key in report["scores"]
        errors = recompute_and_validate(report, scene, require_ci=True, expect_sha=sha)
        assert not errors


def test_sample_true_rejected(tmp_path: Path) -> None:
    scene = Path("fixtures/scenes/warehouse_v1.json")
    report = compute_warehouse_scores(scene)
    report["sample"] = True
    report["git_sha"] = "b" * 40
    path = tmp_path / "report.json"
    write_report(path, report)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "annotation_qa_workbench.cli",
            "report",
            "--check",
            str(path),
            "--require-ci",
            "--expect-sha",
            "b" * 40,
        ],
        env={**dict(__import__("os").environ), "PYTHONPATH": str(Path.cwd())},
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 1


def test_reject_nan(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_report(tmp_path / "x.json", {"x": float("nan")})


def test_reject_boolean_score(tmp_path: Path) -> None:
    scene = Path("fixtures/scenes/warehouse_v1.json")
    report = compute_warehouse_scores(scene)
    report["scores"]["A"]["matches"] = True  # type: ignore[assignment]
    errors = recompute_and_validate(report, scene, require_ci=False)
    assert any("matches" in e for e in errors)
