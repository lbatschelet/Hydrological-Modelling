"""
OUTPUT EXERCISE 1 — Hydrological year plot of Q, P, T and PET.

Q, P, T from observation-based CAMELS-CH; PET from simulation-based (pet_sim).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from plot_style import apply_style, set_title

ROOT = Path(__file__).resolve().parents[1]
ATTR_PATH = ROOT / "data/camels_ch/static_attributes/CAMELS_CH_topographic_attributes.csv"
OUT_DIR = ROOT / "figures"

# Hydrological year start (Swiss convention: 1 Oct).
HY_START = pd.Timestamp("2019-10-01")
HY_END = pd.Timestamp("2020-09-30")


def gauge_info(gauge_id: int) -> tuple[str, str]:
    attrs = pd.read_csv(ATTR_PATH, comment="#", encoding="latin-1")
    row = attrs.loc[attrs["gauge_id"] == gauge_id]
    if row.empty:
        return "unknown", "unknown"
    r = row.iloc[0]
    return str(r["water_body_name"]), str(r["gauge_name"])


def load_data(gauge_id: int) -> pd.DataFrame:
    obs_path = (
        ROOT
        / "data/camels_ch/timeseries/observation_based"
        / f"CAMELS_CH_obs_based_{gauge_id}.csv"
    )
    sim_path = (
        ROOT
        / "data/camels_ch/timeseries/simulation_based"
        / f"CAMELS_CH_sim_based_{gauge_id}.csv"
    )
    obs = pd.read_csv(obs_path, parse_dates=["date"])
    sim = pd.read_csv(sim_path, parse_dates=["date"])
    df = obs.merge(sim[["date", "pet_sim(mm/d)"]], on="date", how="inner")
    return df.rename(
        columns={
            "discharge_spec(mm/d)": "Q",
            "precipitation(mm/d)": "P",
            "temperature_mean(degC)": "T",
            "pet_sim(mm/d)": "PET",
        }
    )


def plot_hydro_year(
    df: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    gauge_id: int,
    river: str,
    gauge_name: str,
) -> plt.Figure:
    period = df.loc[(df["date"] >= start) & (df["date"] <= end)].copy()
    if period.empty:
        raise ValueError(f"No data between {start.date()} and {end.date()}")

    fig, (ax_q, ax_t) = plt.subplots(
        2,
        1,
        figsize=(12, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [2.6, 1.0], "hspace": 0.08},
    )

    ax_p = ax_q.twinx()

    # Daily steps (no linear interpolation between days)
    ax_q.fill_between(
        period["date"],
        period["Q"],
        step="mid",
        color="#6BAED6",
        alpha=0.55,
        label="Q (discharge)",
        zorder=2,
    )
    ax_q.step(
        period["date"],
        period["Q"],
        where="mid",
        color="#2171B5",
        lw=0.8,
        zorder=3,
    )
    ax_q.fill_between(
        period["date"],
        period["PET"],
        step="mid",
        color="#74C476",
        alpha=0.45,
        label="PET",
        zorder=4,
    )
    ax_q.step(
        period["date"],
        period["PET"],
        where="mid",
        color="#238B45",
        lw=0.8,
        zorder=5,
    )
    ax_p.bar(
        period["date"],
        period["P"],
        width=1.0,
        color="#08519C",
        alpha=0.75,
        label="P (precipitation)",
        zorder=1,
        align="center",
    )

    ax_q.set_ylabel("Q and PET [mm/d]")
    ax_p.set_ylabel("Precipitation [mm/d]")
    ax_p.invert_yaxis()

    q_pet_max = max(period["Q"].max(), period["PET"].max())
    ax_q.set_ylim(0, max(q_pet_max * 1.15, 1))
    p_max = max(period["P"].max(), 1)
    ax_p.set_ylim(p_max * 2.2, 0)

    set_title(
        ax_q,
        f"Hydrological year {start.year}/{end.year} — "
        f"CAMELS-CH {gauge_id} ({river}, {gauge_name})",
    )

    h1, l1 = ax_q.get_legend_handles_labels()
    h2, l2 = ax_p.get_legend_handles_labels()
    ax_q.legend(h1 + h2, l1 + l2, loc="upper left")

    ax_q.grid(True, axis="y", alpha=0.3)
    ax_q.set_zorder(ax_p.get_zorder() + 1)
    ax_q.patch.set_visible(False)

    ax_t.plot(period["date"], period["T"], color="#E6550D", lw=1.0, label="T mean")
    ax_t.axhline(0, color="0.5", lw=0.8, ls="--")
    ax_t.fill_between(
        period["date"],
        period["T"],
        0,
        where=period["T"] >= 0,
        color="#FDAE6B",
        alpha=0.35,
        interpolate=False,
    )
    ax_t.fill_between(
        period["date"],
        period["T"],
        0,
        where=period["T"] < 0,
        color="#9ECAE1",
        alpha=0.45,
        interpolate=False,
    )
    ax_t.set_ylabel("T [°C]")
    ax_t.set_xlabel("Date")
    ax_t.legend(loc="upper left")
    ax_t.grid(True, axis="y", alpha=0.3)

    ax_t.xaxis.set_major_locator(mdates.MonthLocator())
    ax_t.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=30, ha="right")

    fig.text(
        0.01,
        0.01,
        "Q, P, T: observation-based · PET: simulation-based (pet_sim, Penman–Monteith)",
        fontsize=8,
        color="0.4",
    )

    return fig


def main() -> None:
    apply_style()
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", type=str, default=str(HY_START.date()))
    parser.add_argument("--end", type=str, default=str(HY_END.date()))
    args = parser.parse_args()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    river, gauge_name = gauge_info(args.gauge)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data(args.gauge)
    fig = plot_hydro_year(df, start, end, args.gauge, river, gauge_name)
    out = OUT_DIR / f"hydro_year_{args.gauge}_{start.year}_{end.year}.png"
    fig.savefig(out)
    print(f"Saved: {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
