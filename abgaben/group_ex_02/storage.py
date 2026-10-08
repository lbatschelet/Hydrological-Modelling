"""One linear reservoir. Outflow of a step is k times storage at the start of that step."""

from __future__ import annotations

from evapotranspiration import evapotranspiration


def linear_step(storage: float, inflow: float, k: float) -> tuple[float, float]:
    outflow = k * storage
    return storage + inflow - outflow, outflow


def limited_step(
    storage: float, inflow: float, k: float, smax: float, et0: float
) -> tuple[float, float, float]:
    """Linear outflow, then ET, then a cap. Excess above Smax leaves as discharge."""
    outflow = k * storage
    updated = storage + inflow - outflow
    et = min(evapotranspiration(storage, smax, et0), max(updated, 0.0))
    updated -= et
    overflow = max(updated - smax, 0.0)
    updated = min(max(updated, 0.0), smax)
    return updated, outflow + overflow, et


def simulate(inflow: list[float], k: float, storage: float = 0.0) -> tuple[list[float], list[float]]:
    storages: list[float] = []
    outflows: list[float] = []
    for volume in inflow:
        storage, outflow = linear_step(storage, volume, k)
        storages.append(storage)
        outflows.append(outflow)
    return storages, outflows


def simulate_limited(
    inflow: list[float],
    k: float,
    smax: float,
    et0: float,
    storage: float = 0.0,
) -> tuple[list[float], list[float], list[float]]:
    storages: list[float] = []
    discharges: list[float] = []
    evapotranspirations: list[float] = []
    for volume in inflow:
        storage, discharge, et = limited_step(storage, volume, k, smax, et0)
        storages.append(storage)
        discharges.append(discharge)
        evapotranspirations.append(et)
    return storages, discharges, evapotranspirations
