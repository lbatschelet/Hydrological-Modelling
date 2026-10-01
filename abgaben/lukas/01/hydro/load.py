"""Read CAMELS-CH files into frames with the agreed columns."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_FLUX_COLUMNS = {
    "discharge_spec(mm/d)": "Q",
    "precipitation(mm/d)": "P",
    "temperature_mean(degC)": "T",
    "pet_sim(mm/d)": "PET",
}


def load_fluxes(obs_path: Path, sim_path: Path) -> pd.DataFrame:
    """Daily Q, P, T from observations and PET from the simulation file."""
    obs = pd.read_csv(obs_path, parse_dates=["date"])
    sim = pd.read_csv(sim_path, parse_dates=["date"])
    merged = obs.merge(sim[["date", "pet_sim(mm/d)"]], on="date", how="inner")
    renamed = merged.rename(columns=_FLUX_COLUMNS)
    return renamed[["date", "Q", "P", "T", "PET"]]


def load_discharge(path: Path) -> pd.DataFrame:
    """Daily discharge volume as column Q."""
    raw = pd.read_csv(path, parse_dates=["date"])
    renamed = raw.rename(columns={"discharge_vol(m3/s)": "Q"})
    return renamed[["date", "Q"]].dropna(subset=["Q"]).reset_index(drop=True)


def load_gauge(attrs_path: Path, gauge_id: int) -> tuple[str, str]:
    """River and gauge name for one id."""
    attrs = pd.read_csv(attrs_path, comment="#", encoding="latin-1")
    row = attrs.loc[attrs["gauge_id"] == gauge_id]
    if row.empty:
        raise ValueError(f"Unknown gauge_id {gauge_id}")
    record = row.iloc[0]
    return str(record["water_body_name"]), str(record["gauge_name"])
