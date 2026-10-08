"""Linear reservoirs. Outflow of one step is k times storage at the start of the step."""

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


def cascade(inflow: list[float], k1: float, k2: float) -> tuple[list[float], list[float]]:
    """Two reservoirs in series. Outflow of the first is inflow of the second."""
    _, outflow_1 = simulate(inflow, k1)
    _, outflow_2 = simulate(outflow_1, k2)
    return outflow_1, outflow_2


def max_discharge_grid(
    inflow: list[float], k_values: list[float]
) -> list[tuple[float, float, float]]:
    rows = []
    for k1 in k_values:
        for k2 in k_values:
            _, outflow_2 = cascade(inflow, k1, k2)
            rows.append((k1, k2, max(outflow_2)))
    return rows
