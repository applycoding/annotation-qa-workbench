# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
from pathlib import Path


def test_undercover_fixture_tracked() -> None:
    path = Path("tests/fixtures_coverage/undercover.py")
    assert path.is_file()
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        check=True,
        capture_output=True,
    )


def test_negative_coverage_threshold() -> None:
    """Deliberately under-covered module must fail --cov-fail-under=80."""
    data_file = Path("tests/fixtures_coverage/.coverage.negative")
    env = dict(os.environ)
    env["COVERAGE_FILE"] = str(data_file.resolve())
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=undercover_mod",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-q",
            "tests/fixtures_coverage/test_undercovered.py",
        ],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        env=env,
        check=False,
    )
    assert proc.returncode == 1
    assert proc.returncode not in (2, 3)
    combined = proc.stdout + proc.stderr
    lowered = combined.lower()
    assert "filenotfounderror" not in lowered
    assert "importerror" not in lowered
    assert "modulenotfounderror" not in lowered
    assert "fail-under" in lowered or "below" in lowered
