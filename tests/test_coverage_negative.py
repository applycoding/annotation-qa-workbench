# SPDX-License-Identifier: Apache-2.0

import os
import re
import subprocess
import sys
from pathlib import Path

COVERAGE_RC = "tests/fixtures_coverage/coverage.rc"
UNDERCOVER_PATH = "tests/fixtures_coverage/undercover.py"


def _valid_undercoverage_failure(stdout: str, stderr: str) -> bool:
    combined = stdout + stderr
    lowered = combined.lower()
    if "no data to report" in lowered:
        return False
    if "filenotfounderror" in lowered or "importerror" in lowered or "modulenotfounderror" in lowered:
        return False
    if UNDERCOVER_PATH not in combined and "undercover.py" not in combined:
        return False
    stmt_match = re.search(r"undercover\.py\s+(\d+)\s+\d+\s+\d+%", combined)
    if not stmt_match or int(stmt_match.group(1)) <= 0:
        return False
    pct_match = re.search(r"total coverage:\s*([\d.]+)%", lowered)
    if not pct_match:
        return False
    if float(pct_match.group(1)) >= 80.0:
        return False
    return "fail-under" in lowered or "below" in lowered


def _coverage_subprocess(test_file: str, *, use_rc: bool) -> subprocess.CompletedProcess[str]:
    data_file = Path("tests/fixtures_coverage/.coverage.negative")
    env = dict(os.environ)
    env["COVERAGE_FILE"] = str(data_file.resolve())
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=undercover_mod",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-q",
        test_file,
    ]
    if use_rc:
        cmd[3:3] = [f"--cov-config={COVERAGE_RC}"]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        env=env,
        check=False,
    )


def test_undercover_fixture_tracked() -> None:
    path = Path(UNDERCOVER_PATH)
    assert path.is_file()
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        check=True,
        capture_output=True,
    )


def test_negative_coverage_rejects_no_data() -> None:
    """Without the isolated rcfile, coverage must not satisfy the gate (no data path)."""
    proc = _coverage_subprocess("tests/fixtures_coverage/test_undercovered.py", use_rc=False)
    assert proc.returncode == 1
    assert "no data to report" in (proc.stdout + proc.stderr).lower()
    assert not _valid_undercoverage_failure(proc.stdout, proc.stderr)


def test_negative_coverage_threshold() -> None:
    """Import-only run must fail fail-under with real statements measured on undercover.py."""
    proc = _coverage_subprocess("tests/fixtures_coverage/test_undercovered.py", use_rc=True)
    assert proc.returncode == 1
    assert proc.returncode not in (2, 3)
    assert _valid_undercoverage_failure(proc.stdout, proc.stderr)


def test_negative_coverage_full_passes() -> None:
    """Executing every function must meet the same fail-under threshold."""
    proc = _coverage_subprocess("tests/fixtures_coverage/test_undercovered_full.py", use_rc=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr
    assert "undercover.py" in combined
    assert re.search(r"total coverage:\s*100", combined.lower())
