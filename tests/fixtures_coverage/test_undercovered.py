# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path


def test_import_undercover_module() -> None:
    path = Path(__file__).with_name("undercover.py")
    spec = importlib.util.spec_from_file_location("undercover_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "never_called")
