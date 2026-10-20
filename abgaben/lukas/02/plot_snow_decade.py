"""Ten-year mean snow store against the ten-year mean of the SLF SWE record."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# Shared figure style. The definitions live in plot_style.py at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from plot_style import (  # noqa: E402
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
    new_figure,
    set_title,
    style_axes,
)

from first_snow_model import find_data_root, load_gauge, load_snow_forcing, simulate_snow

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

# Wider than the lecture ranges, same grid as the long-record search outside this folder.
MF_VALUES = [round(0.2 + 0.2 * i, 1) for i in range(40)]
TT_VALUES = [round(-1.0 + 0.25 * i, 2) for i in range(21)]


def hydro_day(dates: pd.Series) -> pd.Series:
    """Day of the hydrological year. 1 October is day 0."""
    year = dates.dt.year.where(dates.dt.month >= 10, dates.dt.year - 1)
    start = pd.to_datetime(dict(year=year, month=10, day=1))
    return (dates - start).dt.days


def mean_by_hydro_day(frame: pd.DataFrame, column: str) -> pd.Series:
    """Mean of one column on each day of the hydrological year. Leap-day 29 Feb is dropped."""
    work = frame.loc[~((frame["date"].dt.month == 2) & (frame["date"].dt.day == 29))].copy()
    work["hydro_day"] = hydro_day(work["date"])
    return work.groupby("hydro_day")[column].mean()


def rmse(period: pd.DataFrame, mf: float, tt: float) -> float:
    """Root mean square error against SWE. The opening day sets the store, it is not scored."""
    opening = period["SWE"].iloc[0]
    swe0 = 0.0 if pd.isna(opening) else float(opening)
    stores, _melts = simulate_snow(
        period["P"].tolist(),
        period["T"].tolist(),
        mf,
        tt,
        swe0,
    )
    simulated = pd.Series(stores, index=period.index)
    paired = period["SWE"].notna().copy()
    paired.iloc[0] = False
    error = simulated[paired] - period.loc[paired, "SWE"]
    return float((error.pow(2).mean()) ** 0.5)


def optimise(period: pd.DataFrame) -> tuple[float, float, float]:
    """Return the (rmse, mf, tt) with the smallest error on this window."""
    scores = [(rmse(period, mf, tt), mf, tt) for tt in TT_VALUES for mf in MF_VALUES]
    return min(scores, key=lambda row: row[0])


def plot_snow_mean(
    simulated: pd.Series,
    observed: pd.Series,
    *,
    title: str,
    subtitle: str,
    note: str,
) -> plt.Figure:
    """Mean snow water equivalent through the hydrological year."""
    fig, ax = new_figure()
    # A non-leap year starting on 1 October gives readable month ticks for the hydro year.
    axis_dates = pd.date_range("2019-10-01", periods=len(simulated), freq="D")
    ax.plot(axis_dates, simulated.values, color=STORAGE_COLOR, lw=2.2, label="Simulated mean SWE")
    ax.plot(axis_dates, observed.values, color=OUTFLOW_COLOR, lw=1.8, label="Observed mean SWE")
    ax.set_xlabel("Hydrological year")
    ax.set_ylabel("Snow water equivalent [mm]")
    set_title(ax, title, subtitle=subtitle)
    style_axes(ax)
    ax.set_xlim(axis_dates[0], axis_dates[-1])
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    figure_note(fig, note)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    return fig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    # Ten full hydrological years ending with 2019/20.
    parser.add_argument("--start", default="2010-10-01")
    parser.add_argument("--end", default="2020-09-30")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    data_root = args.data_root or find_data_root(HERE)
    path = (
        data_root
        / "timeseries"
        / "observation_based"
        / f"CAMELS_CH_obs_based_{args.gauge}.csv"
    )
    attrs = data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"
    river, gauge_name = load_gauge(attrs, args.gauge)
    forcing = load_snow_forcing(path)
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    period = forcing.loc[(forcing["date"] >= start) & (forcing["date"] <= end)].copy()
    if period.empty:
        raise ValueError(f"No data between {start.date()} and {end.date()}")
    if period["SWE"].isna().any():
        raise ValueError("SWE has gaps in this window. Pick a period that is fully covered.")

    error, mf, tt = optimise(period)
    opening = float(period["SWE"].iloc[0])
    stores, _melts = simulate_snow(
        period["P"].tolist(),
        period["T"].tolist(),
        mf,
        tt,
        opening,
    )
    period["SWE_sim"] = stores

    observed_mean = mean_by_hydro_day(period, "SWE")
    simulated_mean = mean_by_hydro_day(period, "SWE_sim")
    # Align on the same hydro days. Both drop 29 February, so they share the index.
    simulated_mean = simulated_mean.reindex(observed_mean.index)

    fig = plot_snow_mean(
        simulated_mean,
        observed_mean,
        title=(
            f"Mean snow store — {river}, {gauge_name}, "
            f"{start.year}/{start.year + 1}–{end.year - 1}/{end.year}"
        ),
        subtitle=(
            f"Degree-day factor {mf:g} mm/°C/d, threshold {tt:g} °C, "
            f"fit on these ten years (RMSE {error:.0f} mm). "
            f"Mean peak {simulated_mean.max():.0f} mm against {observed_mean.max():.0f} mm."
        ),
        note=(
            f"CAMELS-CH {args.gauge}. SWE: SLF · precipitation and temperature: "
            f"MeteoSwiss catchment means."
        ),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"snow_mean_{args.gauge}_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Best: mf={mf:g}, tt={tt:g}, RMSE {error:.1f} mm")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
