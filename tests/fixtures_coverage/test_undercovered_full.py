# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path


def test_execute_all_undercover_functions() -> None:
    path = Path(__file__).with_name("undercover.py")
    spec = importlib.util.spec_from_file_location("undercover_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.never_called()
    assert mod.branch_a() == "a"
    assert mod.branch_b() == "b"
    assert mod.branch_c() == "c"
