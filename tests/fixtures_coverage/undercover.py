# SPDX-License-Identifier: Apache-2.0

"""Deliberately under-covered module for negative coverage gate."""


def never_called() -> int:
    total = 0
    for i in range(50):
        total += i * i
    return total


def branch_a() -> str:
    return "a"


def branch_b() -> str:
    return "b"


def branch_c() -> str:
    return "c"
