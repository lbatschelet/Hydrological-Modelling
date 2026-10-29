"""Linear stores that only route water. No ET, no capacity."""

from __future__ import annotations


def linear_route(storage: float, inflow: float, k: float) -> tuple[float, float]:
    """Add inflow, then release k times the store at the start of the release."""
    storage = storage + inflow
    outflow = k * storage
    return storage - outflow, outflow
