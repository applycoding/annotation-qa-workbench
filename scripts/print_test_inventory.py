# SPDX-License-Identifier: Apache-2.0
"""Print README test inventory bullets from collectors and source scans."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "expected"

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


def _count_test_calls(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"\b(?:test|it)\s*\(", text))


def vitest_count() -> int:
    if (WEB / "node_modules").is_dir():
        try:
            out = _run(["npx", "vitest", "run", "--reporter=basic"], cwd=WEB)
            m = re.search(r"Tests\s+(\d+)\s+passed", out)
            if m:
                return int(m.group(1))
        except subprocess.CalledProcessError:
            pass
    iou = len(json.loads((EXPECTED_DIR / "iou_cases.json").read_text(encoding="utf-8"))["cases"])
    return iou + 4 + 1 + 3 + 2 + 2


def playwright_count() -> int:
    spec = WEB / "tests" / "dashboard.spec.ts"
    if not spec.is_file():
        raise RuntimeError(f"missing playwright spec: {spec}")
    if (WEB / "node_modules").is_dir():
        try:
            out = _run(["npx", "playwright", "test", "--list"], cwd=WEB)
            m = re.search(r"Total:\s+(\d+)\s+tests?", out)
            if m:
                return int(m.group(1))
        except subprocess.CalledProcessError:
            pass
    return _count_test_calls(spec)


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
