"""Forcing and discharge for the flowerpot. Callers pass paths."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def find_data_root(start: Path) -> Path:
    """Nearest data/camels_ch at or above start."""
    for candidate in (start, *start.parents):
        root = candidate / "data" / "camels_ch"
        if root.is_dir():
            return root
    raise FileNotFoundError(f"No CAMELS-CH data above {start}")


def load_camels(obs_path: Path, sim_path: Path) -> pd.DataFrame:
    """Catchment-average P, T, Q and PET. Columns: date, P, T, Q, PET."""
    obs = pd.read_csv(obs_path, parse_dates=["date"])
    sim = pd.read_csv(sim_path, parse_dates=["date"])
    merged = obs.merge(sim[["date", "pet_sim(mm/d)"]], on="date", how="inner")
    out = merged.rename(
        columns={
            "precipitation(mm/d)": "P",
            "temperature_mean(degC)": "T",
            "discharge_spec(mm/d)": "Q",
            "pet_sim(mm/d)": "PET",
        }
    )
    return out[["date", "P", "T", "Q", "PET"]]


def load_station(path: Path) -> pd.DataFrame:
    """MeteoSwiss daily P and T. Columns: date, P, T."""
    raw = pd.read_csv(path, sep=";")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(raw["reference_timestamp"], format="%d.%m.%Y %H:%M"),
            "P": pd.to_numeric(raw["rre150d0"], errors="coerce"),
            "T": pd.to_numeric(raw["tre200d0"], errors="coerce"),
        }
    )
    return out.dropna(subset=["P", "T"]).reset_index(drop=True)


def load_gauge(attrs_path: Path, gauge_id: int) -> tuple[str, str]:
    """River and gauge name for one id."""
    attrs = pd.read_csv(attrs_path, comment="#", encoding="latin-1")
    row = attrs.loc[attrs["gauge_id"] == gauge_id]
    if row.empty:
        raise ValueError(f"Unknown gauge_id {gauge_id}")
    record = row.iloc[0]
    return str(record["water_body_name"]), str(record["gauge_name"])


def with_station_forcing(camels: pd.DataFrame, station: pd.DataFrame) -> pd.DataFrame:
    """Replace P and T with the station series. Keep CAMELS Q and PET."""
    merged = camels[["date", "Q", "PET"]].merge(station, on="date", how="inner")
    return merged[["date", "P", "T", "Q", "PET"]]
