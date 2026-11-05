# Exercise 4: one better and one bad modelled-vs-observed window.

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
REPO = HERE.parents[1]
sys.path.insert(0, str(EX03))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from load import find_data_root, load_camels, load_gauge  # noqa: E402
from model import simulate  # noqa: E402
from plot_style import (  # noqa: E402
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
    set_title,
)

FIGURES = HERE / "figures"
GAUGE = 2303
WARM_START = "1981-01-01"

PARAMS = dict(imax=2.0, mf=1.5, tt=0.5, k=0.1, smax=120.0)

BETTER = ("2010-07-09", "2010-08-02", "better")
BAD = ("2020-01-28", "2020-02-12", "bad")


def read_params() -> dict:
    path = HERE / "best_params.txt"
    if not path.exists():
        return dict(PARAMS)
    raw = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        raw[key.strip()] = val.strip()
    return dict(
        imax=float(raw.get("Imax", PARAMS["imax"])),
        mf=float(raw.get("mf", PARAMS["mf"])),
        tt=float(raw.get("TT", PARAMS["tt"])),
        k=float(raw.get("k", PARAMS["k"])),
        smax=float(raw.get("Smax", PARAMS["smax"])),
    )


def plot_window(
    period: pd.DataFrame,
    *,
    title: str,
    subtitle: str,
    note: str,
    out: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(period["date"], period["Q"], color=OUTFLOW_COLOR, lw=1.5, label="Observed Q")
    ax.plot(period["date"], period["Q_mod"], color=STORAGE_COLOR, lw=1.8, label="Modelled Q")
    ax.set_ylabel("Discharge [mm/d]")
    ax.set_ylim(bottom=0)
    set_title(ax, title, subtitle=subtitle)
    ax.grid(True, axis="y", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.legend(loc="upper right")
    fig.autofmt_xdate(rotation=30, ha="right")
    figure_note(fig, note)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.18, top=0.82)
    fig.savefig(out, bbox_inches=None, pad_inches=0.3)
    plt.close(fig)
    print(f"Saved: {out}")


def main() -> None:
    apply_style()
    params = read_params()
    root = find_data_root(HERE)
    river, gauge_name = load_gauge(
        root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv",
        GAUGE,
    )
    camels = load_camels(
        root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{GAUGE}.csv",
        root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{GAUGE}.csv",
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    param_line = (
        f"mf={params['mf']:g}, TT={params['tt']:g} °C, "
        f"k={params['k']:g}, Smax={params['smax']:g} mm, Imax={params['imax']:g}"
    )
    note = (
        f"CAMELS-CH {GAUGE}, {river}, {gauge_name}. "
        "Q/P/T observed catchment mean; PET = CAMELS pet_sim. "
        f"Lumped flowerpot. {param_line}."
    )
    titles = {
        "better": "Better window — timing ok, peaks still low",
        "bad": "Bad window — peak strongly underestimated",
    }

    for start, end, tag in (BETTER, BAD):
        full = camels.loc[(camels["date"] >= WARM_START) & (camels["date"] <= end)].copy()
        result = simulate(
            full["P"].tolist(),
            full["T"].tolist(),
            full["PET"].tolist(),
            **params,
        )
        full["Q_mod"] = result["Q"]
        period = full.loc[(full["date"] >= start) & (full["date"] <= end)].copy()
        plot_window(
            period,
            title=titles[tag],
            subtitle=f"{start} to {end}. Thur at Jonschwil-Mühlau.",
            note=note,
            out=FIGURES / f"event_{tag}_{start}_{end}.png",
        )


if __name__ == "__main__":
    main()
