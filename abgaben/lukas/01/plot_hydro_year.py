"""Hydrological year of discharge, precipitation, temperature, and potential evapotranspiration."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from hydro.load import load_fluxes, load_gauge
from hydro.paths import find_data_root, observation_csv, simulation_csv, topography_csv
from hydro.plot_hydro_year import plot_hydro_year
from hydro.series import select_period
# Shared figure style, defined in plot_style.py at the repository root.
from hydro.style import apply_style

HERE = Path(__file__).resolve().parent
DATA_ROOT = find_data_root(HERE)
FIGURES = HERE / "figures"
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _hydro_year_subtitle(period: pd.DataFrame) -> str:
    by_month = period.groupby(period["date"].dt.month)["Q"].sum()
    wettest = _MONTHS[int(by_month.idxmax()) - 1]
    peak_day = period.loc[period["Q"].idxmax(), "date"]
    return (
        f"Most runoff comes in {wettest}. "
        f"The highest day is {peak_day.day} {_MONTHS[peak_day.month - 1]}."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", default="2019-10-01")
    parser.add_argument("--end", default="2020-09-30")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    fluxes = load_fluxes(
        observation_csv(args.data_root, args.gauge),
        simulation_csv(args.data_root, args.gauge),
    )
    period = select_period(fluxes, start, end)
    river, gauge_name = load_gauge(topography_csv(args.data_root), args.gauge)
    fig = plot_hydro_year(
        period,
        title=(
            f"Hydrological year {start.year}/{end.year} — "
            f"CAMELS-CH {args.gauge} ({river}, {gauge_name})"
        ),
        subtitle=_hydro_year_subtitle(period),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"hydro_year_{args.gauge}_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
