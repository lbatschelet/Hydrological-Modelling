"""One linear reservoir. Outflow of a step is k times storage at the start of that step."""

from __future__ import annotations


def linear_step(storage: float, inflow: float, k: float) -> tuple[float, float]:
    outflow = k * storage
    return storage + inflow - outflow, outflow


def simulate(inflow: list[float], k: float, storage: float = 0.0) -> tuple[list[float], list[float]]:
    storages: list[float] = []
    outflows: list[float] = []
    for volume in inflow:
        storage, outflow = linear_step(storage, volume, k)
        storages.append(storage)
        outflows.append(outflow)
    return storages, outflows
