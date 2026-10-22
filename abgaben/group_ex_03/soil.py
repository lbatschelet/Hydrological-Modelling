"""Soil flowerpot: linear outflow, ET from relative storage, overflow joins outflow."""

from __future__ import annotations


def et_from_storage(storage: float, smax: float, pet: float) -> float:
    """PET times the square root of relative storage. Empty storage evaporates nothing."""
    if storage <= 0 or smax <= 0 or pet <= 0:
        return 0.0
    return pet * (storage / smax) ** 0.5


def soil_step(
    storage: float, inflow: float, k: float, smax: float, pet: float
) -> tuple[float, float, float]:
    """Linear outflow, then ET, then a cap. Water above Smax is added to the outflow."""
    outflow = k * storage
    updated = storage + inflow - outflow
    et = min(et_from_storage(storage, smax, pet), max(updated, 0.0))
    updated -= et
    overflow = max(updated - smax, 0.0)
    updated = min(max(updated, 0.0), smax)
    return updated, outflow + overflow, et
