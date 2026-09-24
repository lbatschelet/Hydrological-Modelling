"""
OUTPUT 2 — Regime plot for a CAMELS-CH catchment.

Compares mean monthly discharge for early vs late period (1981–2020)
to illustrate possible climate-change related regime shifts.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_style import apply_style, set_title

ROOT = Path(__file__).resolve().parents[1]
ATTR_PATH = ROOT / "data/camels_ch/static_attributes/CAMELS_CH_topographic_attributes.csv"
OUT_DIR = ROOT / "figures"

MONTHS = np.arange(1, 13)
MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

# Equal 20-year halves of 1981–2020
PERIOD_EARLY = (1981, 2000)
PERIOD_LATE = (2001, 2020)


def gauge_info(gauge_id: int) -> tuple[str, str]:
    attrs = pd.read_csv(ATTR_PATH, comment="#", encoding="latin-1")
    row = attrs.loc[attrs["gauge_id"] == gauge_id]
    if row.empty:
        return "unknown", "unknown"
    r = row.iloc[0]
    return str(r["water_body_name"]), str(r["gauge_name"])


def load_discharge(gauge_id: int) -> pd.DataFrame:
    path = (
        ROOT
        / "data/camels_ch/timeseries/observation_based"
        / f"CAMELS_CH_obs_based_{gauge_id}.csv"
    )
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"discharge_vol(m3/s)": "Q"})
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df.dropna(subset=["Q"])


def yearly_monthly_means(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """One value per year×month = mean daily Q in that month."""
    sub = df.loc[(df["year"] >= y0) & (df["year"] <= y1)]
    return (
        sub.groupby(["year", "month"], as_index=False)["Q"]
        .mean()
        .rename(columns={"Q": "Q_month"})
    )


def regime_mean(ym: pd.DataFrame) -> pd.Series:
    """Mean monthly regime across years."""
    return ym.groupby("month")["Q_month"].mean().reindex(MONTHS)


def plot_regime(
    early: pd.Series,
    late: pd.Series,
    gauge_id: int,
    river: str,
    gauge_name: str,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5.5))

    for series, color, label in [
        (early, "#D62728", f"{PERIOD_EARLY[0]}–{PERIOD_EARLY[1]}"),
        (late, "#1F77B4", f"{PERIOD_LATE[0]}–{PERIOD_LATE[1]}"),
    ]:
        ax.plot(
            MONTHS,
            series,
            color=color,
            lw=2.2,
            marker="o",
            markersize=5,
            label=label,
            zorder=2,
        )

    ax.set_xticks(MONTHS)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlim(0.5, 12.5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Months")
    ax.set_ylabel("Mean monthly discharge [m³/s]")
    set_title(ax, f"Regime plot — CAMELS-CH {gauge_id} ({river}, {gauge_name})")
    ax.grid(True, axis="y", alpha=0.35)
    ax.legend(loc="upper right")
    ax.spines["right"].set_visible(False)

    fig.text(
        0.01,
        0.01,
        "Split: equal 20-yr halves of 1981–2020 · monthly means",
        fontsize=8,
        color="0.4",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    return fig


def main() -> None:
    apply_style()
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    args = parser.parse_args()

    river, gauge_name = gauge_info(args.gauge)
    df = load_discharge(args.gauge)

    early = regime_mean(yearly_monthly_means(df, *PERIOD_EARLY))
    late = regime_mean(yearly_monthly_means(df, *PERIOD_LATE))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = plot_regime(early, late, args.gauge, river, gauge_name)
    out = OUT_DIR / f"regime_{args.gauge}_{PERIOD_EARLY[0]}_{PERIOD_LATE[1]}.png"
    fig.savefig(out)
    print(f"Saved: {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
