# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
from pathlib import Path


def test_negative_coverage_threshold() -> None:
    """Deliberately under-covered module must fail --cov-fail-under=80."""
    tiny = Path("tests/fixtures_coverage/undercover.py")
    tiny.parent.mkdir(parents=True, exist_ok=True)
    tiny.write_text(
        "# SPDX-License-Identifier: Apache-2.0\n"
        "def never_called() -> int:\n"
        "    return 1\n",
        encoding="utf-8",
    )
    data_file = Path("tests/fixtures_coverage/.coverage.negative")
    env = dict(os.environ)
    env["COVERAGE_FILE"] = str(data_file.resolve())
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=tests.fixtures_coverage.undercover",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-q",
            "tests/fixtures_coverage/test_empty.py",
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
    assert "fail" in combined.lower() or "coverage" in combined.lower()
