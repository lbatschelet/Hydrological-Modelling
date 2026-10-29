"""CAMELS CORINE fractions → HRU weights. All 12 columns used; params stay in 3 groups."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Every CAMELS land-cover column → one parameter family (not its own calibrated set).
COVER_TO_GROUP: dict[str, str] = {
    "dwood_perc": "forest",
    "mixed_wood_perc": "forest",
    "ewood_perc": "forest",
    "scrub_perc": "forest",
    "grass_perc": "grass",
    "crop_perc": "grass",
    "wetlands_perc": "grass",
    "urban_perc": "quick",
    "rock_perc": "quick",
    "loose_rock_perc": "quick",
    "ice_perc": "quick",
    "inwater_perc": "quick",
}

HRU_NAMES = ("forest", "grass", "quick")


def load_landcover_row(path: Path, gauge_id: int) -> pd.Series:
    """One gauge row from CAMELS_CH_landcover_attributes.csv."""
    frame = pd.read_csv(path, comment="#")
    row = frame.loc[frame["gauge_id"] == gauge_id]
    if row.empty:
        raise ValueError(f"Unknown gauge_id {gauge_id} in {path}")
    return row.iloc[0]


def cover_fractions(row: pd.Series) -> dict[str, float]:
    """Raw percent for each of the 12 CORINE columns (0 if missing)."""
    out: dict[str, float] = {}
    for col in COVER_TO_GROUP:
        out[col] = float(row[col]) if col in row.index else 0.0
    return out


def hru_weights(row: pd.Series) -> dict[str, float]:
    """
    Sum all 12 cover fractions into forest / grass / quick, then renormalise to 1.
    """
    raw = {name: 0.0 for name in HRU_NAMES}
    for col, group in COVER_TO_GROUP.items():
        if col in row.index:
            raw[group] += float(row[col])
    total = sum(raw.values())
    if total <= 0:
        raise ValueError("Land-cover fractions sum to zero")
    return {name: value / total for name, value in raw.items()}


def load_hru_weights(path: Path, gauge_id: int) -> dict[str, float]:
    """CSV path + gauge → normalised HRU weights."""
    return hru_weights(load_landcover_row(path, gauge_id))
