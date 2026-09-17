"""Finite, minimisation-only Pareto algebra; units belong to the caller.

For a fixed completed task, maximising tasks/J is equivalent to minimising
joules/task. No MAC-based normalisation or scalar EDP preference is imposed.
"""

from __future__ import annotations

import math


def valid_vector(values) -> bool:
    return bool(values) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool)
        and math.isfinite(v) and v > 0 for v in values
    )


def dominates_vector(a, b) -> bool:
    return (len(a) == len(b) and valid_vector(a) and valid_vector(b)
            and all(x <= y for x, y in zip(a, b))
            and any(x < y for x, y in zip(a, b)))


def frontier_vectors(points):
    unique = sorted({tuple(p) for p in points if valid_vector(p)})
    return tuple(p for p in unique if not any(dominates_vector(q, p) for q in unique))


def extends_frontier(points, candidate, tolerance=0.0):
    """Count a new trade-off as progress, even if its latency is worse.

    Tolerance only affects stopping, never the exact reported frontier. A point
    covered by an existing point's relative tolerance box is not progress.
    """
    if not 0 <= tolerance < 1:
        raise ValueError("tolerance must be in [0, 1)")
    if not valid_vector(candidate):
        return False
    return not any(
        len(p) == len(candidate) and valid_vector(p)
        and all(x <= y * (1 + tolerance) for x, y in zip(p, candidate))
        for p in points
    )


def hypervolume_2d(points, reference):
    """Area dominated by a minimisation front and bounded by a FIXED reference.

    Never infer a separate reference for each method/seed. Callers should fix
    and record it before evaluation, or report the exact front without HV.
    """
    if len(reference) != 2 or not valid_vector(reference):
        raise ValueError("reference must contain two finite positive values")
    front = frontier_vectors(
        p for p in points if len(p) == 2 and valid_vector(p)
        and p[0] < reference[0] and p[1] < reference[1]
    )
    area, previous_y = 0.0, reference[1]
    for x, y in front:
        area += (reference[0] - x) * (previous_y - y)
        previous_y = y
    return area
