"""Elevation bands from CAMELS topographic percentiles. Callers pass the CSV path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Standard atmospheric lapse [°C / m]. Negative: colder higher up.
DEFAULT_LAPSE = -0.0065


@dataclass(frozen=True)
class ElevBand:
    name: str
    z_m: float  # representative elevation
    weight: float  # area fraction


def load_topo_row(path: Path, gauge_id: int) -> pd.Series:
    frame = pd.read_csv(path, comment="#", encoding="latin-1")
    row = frame.loc[frame["gauge_id"] == gauge_id]
    if row.empty:
        raise ValueError(f"Unknown gauge_id {gauge_id} in {path}")
    return row.iloc[0]


def quartile_bands(row: pd.Series) -> list[ElevBand]:
    """
    Four equal-area bands from elev percentiles (25 % each).

    Representative z = mid-point of the band edges.
    """
    z_min = float(row["elev_min"])
    p25 = float(row["elev_percentile25"])
    p50 = float(row["elev_percentile50"])
    p75 = float(row["elev_percentile75"])
    z_max = float(row["elev_max"])
    edges = [
        ("low", z_min, p25),
        ("mid_low", p25, p50),
        ("mid_high", p50, p75),
        ("high", p75, z_max),
    ]
    return [
        ElevBand(name=name, z_m=0.5 * (lo + hi), weight=0.25)
        for name, lo, hi in edges
    ]


def lapse_temperature(
    t_mean: float,
    z_band: float,
    z_ref: float,
    lapse: float = DEFAULT_LAPSE,
) -> float:
    """T at band elevation from catchment-mean T (CAMELS) and a lapse rate."""
    return t_mean + lapse * (z_band - z_ref)


def load_bands(path: Path, gauge_id: int) -> tuple[list[ElevBand], float]:
    """Bands plus catchment elev_mean (lapse reference)."""
    row = load_topo_row(path, gauge_id)
    return quartile_bands(row), float(row["elev_mean"])
