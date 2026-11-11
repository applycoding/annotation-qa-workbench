# SPDX-License-Identifier: Apache-2.0

from tests.fixtures_coverage import undercover as uc


def test_import_only() -> None:
    assert hasattr(uc, "never_called")
