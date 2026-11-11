# SPDX-License-Identifier: Apache-2.0

"""Nominal Krippendorff's alpha with missing values."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence


def krippendorff_alpha_nominal(reliability_matrix: Sequence[Sequence[str | None]]) -> float | None:
    """
    Rows are units; columns are raters. None means missing.
    """
    if not reliability_matrix:
        return None
    n_c_total: Counter[str] = Counter()
    sum_o_cc = 0.0
    n_values = 0

    for unit in reliability_matrix:
        present = [v for v in unit if v is not None]
        m = len(present)
        if m < 2:
            continue
        n_values += m
        counts = Counter(present)
        for c, n_c in counts.items():
            n_c_total[c] += n_c
            sum_o_cc += n_c * (n_c - 1) / (m - 1)

    if n_values < 2:
        return None
    denom_stat = sum(n_c * (n_c - 1) for n_c in n_c_total.values())
    numerator = (n_values - 1) * sum_o_cc - denom_stat
    denominator = n_values * (n_values - 1) - denom_stat
    if denominator == 0:
        return None
    return numerator / denominator
