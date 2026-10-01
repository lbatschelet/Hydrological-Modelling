"""CAMELS-CH file locations. Callers pass the dataset root."""

from __future__ import annotations

from pathlib import Path


def observation_csv(data_root: Path, gauge_id: int) -> Path:
    return (
        data_root
        / "timeseries"
        / "observation_based"
        / f"CAMELS_CH_obs_based_{gauge_id}.csv"
    )


def simulation_csv(data_root: Path, gauge_id: int) -> Path:
    return (
        data_root
        / "timeseries"
        / "simulation_based"
        / f"CAMELS_CH_sim_based_{gauge_id}.csv"
    )


def topography_csv(data_root: Path) -> Path:
    return data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"


def find_data_root(start: Path) -> Path:
    """Nearest `data/camels_ch` at or above `start`."""
    for candidate in (start, *start.parents):
        data_root = candidate / "data" / "camels_ch"
        if data_root.is_dir():
            return data_root
    raise FileNotFoundError(f"No CAMELS-CH data above {start}")
