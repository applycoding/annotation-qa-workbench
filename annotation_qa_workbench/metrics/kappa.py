# SPDX-License-Identifier: Apache-2.0

"""Cohen's kappa on paired nominal labels."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float | None:
    n = len(labels_a)
    if n != len(labels_b) or n == 0:
        return None
    agree = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b)
    p_o = agree / n
    ca = Counter(labels_a)
    cb = Counter(labels_b)
    cats = set(ca) | set(cb)
    p_e = sum((ca.get(c, 0) / n) * (cb.get(c, 0) / n) for c in cats)
    if p_e == 1.0:
        return None
    return (p_o - p_e) / (1.0 - p_e)


def kappa_is_po(labels_a: Sequence[str], labels_b: Sequence[str]) -> float | None:
    """Mutant: reports raw observed agreement p_o instead of kappa."""
    n = len(labels_a)
    if n != len(labels_b) or n == 0:
        return None
    agree = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b)
    return agree / n
