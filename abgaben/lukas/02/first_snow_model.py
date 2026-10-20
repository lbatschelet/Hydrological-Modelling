"""Temperature-index snow store. One catchment, one temperature, daily step."""

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
    ET_COLOR,
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
    new_figure,
    set_title,
    style_axes,
)

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

# Fit on the mild winter 2019/20 alone.
WINTER_MF = 1.0
WINTER_TT = 2.0
# Fit on the ten hydrological years 2010/11–2019/20 (see plot_snow_decade.py).
DECADE_MF = 0.6
DECADE_TT = 0.5


def simulate_snow(
    precip: list[float],
    temperature: list[float],
    mf: float,
    tt: float,
    swe: float = 0.0,
) -> tuple[list[float], list[float]]:
    """Snow store at the end of each day, and the melt removed that day."""
    stores: list[float] = []
    melts: list[float] = []
    for rain, temp in zip(precip, temperature):
        # One threshold does both jobs: at or below it, precipitation falls as snow and melt is off.
        snowfall = rain if temp <= tt else 0.0
        # The degree-day term can ask for more melt than the store holds.
        melt = min(swe + snowfall, mf * max(temp - tt, 0.0))
        swe = swe + snowfall - melt
        stores.append(swe)
        melts.append(melt)
    return stores, melts


def load_snow_forcing(path: Path) -> pd.DataFrame:
    """Daily precipitation, mean temperature, and snow water equivalent."""
    raw = pd.read_csv(path, parse_dates=["date"])
    renamed = raw.rename(
        columns={
            "precipitation(mm/d)": "P",
            "temperature_mean(degC)": "T",
            "swe(mm)": "SWE",
        }
    )
    return renamed[["date", "P", "T", "SWE"]]


def load_gauge(attrs_path: Path, gauge_id: int) -> tuple[str, str]:
    """River and gauge name for one id."""
    attrs = pd.read_csv(attrs_path, comment="#", encoding="latin-1")
    row = attrs.loc[attrs["gauge_id"] == gauge_id]
    if row.empty:
        raise ValueError(f"Unknown gauge_id {gauge_id}")
    record = row.iloc[0]
    return str(record["water_body_name"]), str(record["gauge_name"])


def find_data_root(start: Path) -> Path:
    """Nearest data/camels_ch at or above start."""
    for candidate in (start, *start.parents):
        root = candidate / "data" / "camels_ch"
        if root.is_dir():
            return root
    raise FileNotFoundError(f"No CAMELS-CH data above {start}")


def plot_snow(
    dates: pd.Series,
    winter: pd.Series,
    decade: pd.Series,
    observed: pd.Series,
    *,
    title: str,
    subtitle: str,
    note: str,
) -> plt.Figure:
    """Observed SWE and two simulated stores: winter fit and ten-year fit."""
    fig, ax = new_figure()
    known = observed.notna()
    ax.plot(
        dates[known],
        observed[known],
        color=OUTFLOW_COLOR,
        lw=1.8,
        label="Observed SWE",
    )
    ax.plot(
        dates,
        winter,
        color=STORAGE_COLOR,
        lw=2.2,
        label=f"Simulated, this winter (mf={WINTER_MF:g}, TT={WINTER_TT:g} °C)",
    )
    ax.plot(
        dates,
        decade,
        color=ET_COLOR,
        lw=2.0,
        ls="--",
        label=f"Simulated, ten-year fit (mf={DECADE_MF:g}, TT={DECADE_TT:g} °C)",
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Snow water equivalent [mm]")
    set_title(ax, title, subtitle=subtitle)
    style_axes(ax)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=30, ha="right")
    figure_note(fig, note)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    return fig


def snow_message(winter: pd.Series, decade: pd.Series, observed: pd.Series) -> str:
    """Peaks of both stores against the observed snow."""
    paired = observed.notna()
    if not paired.any():
        return "No observed SWE in this window."
    return (
        f"This-winter peak {float(winter[paired].max()):.0f} mm, "
        f"ten-year-fit peak {float(decade[paired].max()):.0f} mm, "
        f"observed peak {float(observed[paired].max()):.0f} mm."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", default="2019-10-01")
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

    # Start from the snow already on the ground. An empty store would miss that water all winter.
    opening = period["SWE"].iloc[0]
    swe0 = 0.0 if pd.isna(opening) else float(opening)
    winter, _ = simulate_snow(
        period["P"].tolist(), period["T"].tolist(), WINTER_MF, WINTER_TT, swe0
    )
    decade, _ = simulate_snow(
        period["P"].tolist(), period["T"].tolist(), DECADE_MF, DECADE_TT, swe0
    )
    period["SWE_winter"] = winter
    period["SWE_decade"] = decade

    fig = plot_snow(
        period["date"],
        period["SWE_winter"],
        period["SWE_decade"],
        period["SWE"],
        title=f"Snow store — {river}, {gauge_name}, {start.year}/{end.year}",
        subtitle=snow_message(period["SWE_winter"], period["SWE_decade"], period["SWE"]),
        note=(
            f"CAMELS-CH {args.gauge}. SWE: SLF · precipitation and temperature: "
            f"MeteoSwiss catchment means."
        ),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"snow_{args.gauge}_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")
    print(snow_message(period["SWE_winter"], period["SWE_decade"], period["SWE"]))


if __name__ == "__main__":
    main()
