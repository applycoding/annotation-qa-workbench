# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

REQUIRED = (
    "Synthetic data only",
    "Simulation only",
    "does not use real robot images",
)

FORBIDDEN_POSITIVE = (
    "this uses real robot images",
    "certified",
    "production labelling platform",
)


def _scan_text(text: str) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    for phrase in REQUIRED:
        if phrase.lower() not in lower:
            errors.append(f"missing {phrase}")
    for phrase in FORBIDDEN_POSITIVE:
        idx = 0
        while True:
            pos = lower.find(phrase, idx)
            if pos < 0:
                break
            window = lower[max(0, pos - 12) : pos]
            if "not " not in window and "not a " not in window:
                errors.append(f"forbidden {phrase}")
                break
            idx = pos + len(phrase)
    return errors


def test_readme_honesty() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert not _scan_text(text)


def test_notice_honesty() -> None:
    text = Path("NOTICE").read_text(encoding="utf-8")
    assert "Arpan Bom" in text
    assert not any(p in text.lower() for p in FORBIDDEN_POSITIVE)


def test_compliant_fixture_passes() -> None:
    ok = "Synthetic data only. Simulation only. This demo does not use real robot images."
    assert not _scan_text(ok)


def test_prohibited_fixture_fails() -> None:
    bad = "This uses real robot images from our fleet."
    assert _scan_text(bad)
