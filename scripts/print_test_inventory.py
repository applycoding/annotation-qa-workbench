# SPDX-License-Identifier: Apache-2.0
"""Print README test inventory bullets from live collection commands."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def _run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout + proc.stderr


def pytest_count() -> int:
    out = _run([sys.executable, "-m", "pytest", "--collect-only"])
    m = re.search(r"(\d+)\s+tests?\s+collected", out)
    if not m:
        raise RuntimeError(f"could not parse pytest collection:\n{out}")
    return int(m.group(1))


def vitest_count() -> int:
    out = _run(["npx", "vitest", "run"], cwd=WEB)
    m = re.search(r"Tests\s+(\d+)\s+passed", out)
    if not m:
        raise RuntimeError(f"could not parse vitest output:\n{out}")
    return int(m.group(1))


def playwright_count() -> int:
    out = _run(["npx", "playwright", "test", "--list"], cwd=WEB)
    m = re.search(r"Total:\s+(\d+)\s+tests?", out)
    if not m:
        raise RuntimeError(f"could not parse playwright list:\n{out}")
    return int(m.group(1))


def main() -> None:
    mutant_tests = sum(
        1
        for line in (ROOT / "tests" / "test_mutants.py").read_text(encoding="utf-8").splitlines()
        if line.startswith("def test_")
    )

    bullets = [
        f"- Pytest: **{pytest_count()}** tests collected (`python -m pytest --collect-only -q`).",
        f"- Vitest: **{vitest_count()}** test (`cd web && npx vitest run`).",
        f"- Playwright: **{playwright_count()}** specs (`cd web && npx playwright test --list`).",
        f"- Injected scorer mutants: {mutant_tests} (`iou_over_gt`, `kappa_is_po`, `mota_skip_idsw`, `idf1_match_only`).",
    ]
    print("\n".join(bullets))


if __name__ == "__main__":
    main()
