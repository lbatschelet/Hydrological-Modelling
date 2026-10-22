"""Station precipitation against the CAMELS catchment mean. One figure per station."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from load import find_data_root, load_camels, load_gauge, load_station

# Shared figure style. The definitions live in plot_style.py at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plot_style import (  # noqa: E402
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
)

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

STATIONS = {
    "sae": ("smn/ogd-smn_sae_d_historical.csv", "Säntis", "SAE"),
    "ebk": ("smn/ogd-smn_ebk_d_historical.csv", "Ebnat-Kappel", "EBK"),
}


def paired_precip(camels: pd.DataFrame, station: pd.DataFrame) -> pd.DataFrame:
    """Days with precipitation from both sources."""
    merged = camels[["date", "P"]].merge(
        station[["date", "P"]],
        on="date",
        how="inner",
        suffixes=("_camels", "_station"),
    )
    return merged.dropna().reset_index(drop=True)


def plot_compare(
    paired: pd.DataFrame,
    *,
    station_label: str,
    title: str,
    subtitle: str,
    note: str,
) -> plt.Figure:
    """Cumulative 1:1 panel and daily scatter, as on the course slide."""
    fig, (ax_c, ax_s) = plt.subplots(1, 2, figsize=(10, 4.2))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.15, top=0.84, wspace=0.28)

    cum_station = paired["P_station"].cumsum()
    cum_camels = paired["P_camels"].cumsum()
    limit = max(float(cum_station.iloc[-1]), float(cum_camels.iloc[-1]))
    ax_c.plot(cum_station, cum_camels, color=STORAGE_COLOR, lw=1.8, label="station vs CAMELS")
    ax_c.plot([0, limit], [0, limit], color=OUTFLOW_COLOR, lw=1.4, label="1:1 line")
    ax_c.set_xlabel(f"Cumulated precip {station_label} [mm]")
    ax_c.set_ylabel("Cumulated precip CAMELS [mm]")
    ax_c.set_xlim(0, limit * 1.02)
    ax_c.set_ylim(0, limit * 1.02)
    ax_c.grid(True, alpha=0.35)
    ax_c.spines["right"].set_visible(False)
    ax_c.legend(loc="upper left")

    ax_s.scatter(
        paired["P_station"],
        paired["P_camels"],
        s=12,
        alpha=0.45,
        color=STORAGE_COLOR,
        edgecolors="none",
        label="daily pairs",
    )
    day_limit = max(float(paired["P_station"].max()), float(paired["P_camels"].max()), 1.0)
    ax_s.plot([0, day_limit], [0, day_limit], color=OUTFLOW_COLOR, lw=1.4, label="1:1 line")
    ax_s.set_xlabel(f"Precip {station_label} [mm/d]")
    ax_s.set_ylabel("Precip CAMELS [mm/d]")
    ax_s.set_xlim(0, day_limit * 1.05)
    ax_s.set_ylim(0, day_limit * 1.05)
    ax_s.grid(True, alpha=0.35)
    ax_s.spines["right"].set_visible(False)
    ax_s.legend(loc="upper left")

    fig.suptitle(title, fontweight="bold", x=0.09, ha="left", fontsize=13, y=0.98)
    fig.text(0.09, 0.90, subtitle, fontsize=11, color="0.25", ha="left", va="top")
    figure_note(fig, note)
    return fig


def precip_message(paired: pd.DataFrame, station_label: str) -> str:
    """One sentence on which series holds more water over the overlap."""
    total_station = float(paired["P_station"].sum())
    total_camels = float(paired["P_camels"].sum())
    ratio = total_camels / total_station if total_station > 0 else float("nan")
    return (
        f"Over the overlap, CAMELS totals {total_camels:.0f} mm and {station_label} "
        f"{total_station:.0f} mm (CAMELS / station = {ratio:.2f})."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--station", choices=["sae", "ebk", "both"], default="both")
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    data_root = find_data_root(HERE)
    repo = data_root.parents[1]
    camels = load_camels(
        data_root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{args.gauge}.csv",
        data_root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{args.gauge}.csv",
    )
    attrs = data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"
    river, gauge_name = load_gauge(attrs, args.gauge)

    names = ["sae", "ebk"] if args.station == "both" else [args.station]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for key in names:
        rel_path, name, code = STATIONS[key]
        station = load_station(repo / "data" / "meteoswiss" / rel_path)
        paired = paired_precip(camels, station)
        if paired.empty:
            raise ValueError(f"No overlapping precip days for {name}")

        start = paired["date"].iloc[0].date()
        end = paired["date"].iloc[-1].date()
        subtitle = precip_message(paired, name)
        fig = plot_compare(
            paired,
            station_label=name,
            title=f"Station versus CAMELS precip — {name}",
            subtitle=subtitle,
            note=(
                f"CAMELS-CH {args.gauge} ({river}, {gauge_name}). "
                f"Overlap {start} to {end}, {len(paired)} days. "
                f"Station: MeteoSwiss {name} ({code})."
            ),
        )
        out = args.out_dir / f"precip_compare_{args.gauge}_{key}.png"
        # Keep the manual margins; global savefig.bbox=tight would re-open the gap.
        fig.savefig(out, bbox_inches=None)
        plt.close(fig)
        print(f"Saved: {out}")
        print(subtitle)


if __name__ == "__main__":
    main()
