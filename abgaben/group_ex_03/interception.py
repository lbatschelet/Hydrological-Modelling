"""Thin canopy store. Overflow becomes throughfall; the rest can evaporate."""

from __future__ import annotations


def interception_step(
    storage: float, precip: float, pet: float, imax: float
) -> tuple[float, float, float]:
    """Return updated store, throughfall, and interception evaporation."""
    storage = storage + precip
    throughfall = max(storage - imax, 0.0)
    storage = min(storage, imax)
    evaporated = min(storage, max(pet, 0.0))
    storage -= evaporated
    return storage, throughfall, evaporated
