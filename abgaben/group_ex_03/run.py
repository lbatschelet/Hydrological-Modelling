# Lumped flowerpot for the Thur. CAMELS catchment mean or a MeteoSwiss station.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from load import (
    find_data_root,
    load_camels,
    load_gauge,
    load_station,
    with_station_forcing,
)
from model import simulate

# Shared figure style. The definitions live in plot_style.py at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plot_style import (  # noqa: E402
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
    set_title,
)

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

# Imax kept small. The rest is a grid search on CAMELS Q for 2010/11–2019/20
# (see calibration/optimise_flowerpot.py).
IMAX = 2.0
MF = 1.0
TT = 0.5
K = 0.2
SMAX = 80.0

STATIONS = {
    "sae": ("smn/ogd-smn_sae_d_historical.csv", "Säntis"),
    "ebk": ("smn/ogd-smn_ebk_d_historical.csv", "Ebnat-Kappel"),
}


def plot_runoff(
    period: pd.DataFrame,
    *,
    title: str,
    subtitle: str,
    note: str,
) -> plt.Figure:
    """Modelled and observed discharge, precipitation hanging from the top."""
    fig, ax_q = plt.subplots(figsize=(10, 5.5))
    ax_p = ax_q.twinx()

    ax_q.plot(period["date"], period["Q"], color=OUTFLOW_COLOR, lw=1.4, label="Observed Q")
    ax_q.plot(period["date"], period["Q_mod"], color=STORAGE_COLOR, lw=1.8, label="Modelled Q")
    ax_p.bar(period["date"], period["P"], width=1.0, color="0.55", alpha=0.55, label="P")

    ax_q.set_ylabel("Discharge [mm/d]")
    ax_p.set_ylabel("Precipitation [mm/d]")
    ax_p.invert_yaxis()
    ax_q.set_ylim(bottom=0)
    ax_p.set_ylim(max(float(period["P"].max()) * 2.2, 1.0), 0)

    set_title(ax_q, title, subtitle=subtitle)
    ax_q.grid(True, axis="y", alpha=0.35)
    ax_q.spines["top"].set_visible(False)
    handles_q, labels_q = ax_q.get_legend_handles_labels()
    handles_p, labels_p = ax_p.get_legend_handles_labels()
    ax_q.legend(handles_q + handles_p, labels_q + labels_p, loc="upper right")
    ax_q.set_zorder(ax_p.get_zorder() + 1)
    ax_q.patch.set_visible(False)
    ax_q.xaxis.set_major_locator(mdates.MonthLocator())
    ax_q.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=30, ha="right")
    figure_note(fig, note)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    return fig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", default="2019-10-01")
    parser.add_argument("--end", default="2020-09-30")
    parser.add_argument(
        "--forcing",
        choices=["camels", "sae", "ebk"],
        default="camels",
        help="Catchment-average CAMELS or a MeteoSwiss station for P and T",
    )
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    data_root = find_data_root(HERE)
    repo = data_root.parents[1]
    obs = data_root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{args.gauge}.csv"
    sim = data_root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{args.gauge}.csv"
    attrs = data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"
    river, gauge_name = load_gauge(attrs, args.gauge)

    camels = load_camels(obs, sim)
    if args.forcing == "camels":
        forcing = camels
        forcing_label = "CAMELS catchment mean"
    else:
        rel_path, station_name = STATIONS[args.forcing]
        station_path = repo / "data" / "meteoswiss" / rel_path
        forcing = with_station_forcing(camels, load_station(station_path))
        forcing_label = station_name

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    period = forcing.loc[(forcing["date"] >= start) & (forcing["date"] <= end)].copy()
    if period.empty:
        raise ValueError(f"No data between {start.date()} and {end.date()}")

    result = simulate(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        imax=IMAX,
        mf=MF,
        tt=TT,
        k=K,
        smax=SMAX,
    )
    period["Q_mod"] = result["Q"]

    fig = plot_runoff(
        period,
        title=f"Flowerpot — {river}, {gauge_name}, {start.year}/{end.year}",
        subtitle=(
            f"{forcing_label}. "
            f"mf={MF:g}, TT={TT:g} °C, Smax={SMAX:g} mm, k={K:g}."
        ),
        note=f"CAMELS-CH {args.gauge}. PET from CAMELS pet_sim. Forcing: {forcing_label}.",
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"flowerpot_{args.gauge}_{args.forcing}_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")
    print(
        f"Mean Qobs={period['Q'].mean():.2f} mm/d, "
        f"Qmod={period['Q_mod'].mean():.2f} mm/d"
    )


if __name__ == "__main__":
    main()
