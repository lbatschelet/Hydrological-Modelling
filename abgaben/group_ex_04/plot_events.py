# Exercise 4: better/bad windows — lumped alone, plus same windows with HRU×bands overlay.

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
FUTURE = HERE.parent / "future_ideas"
REPO = HERE.parents[1]
sys.path.insert(0, str(EX03))
sys.path.insert(0, str(FUTURE))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from elevation import DEFAULT_LAPSE, load_bands  # noqa: E402
from hru_model import (  # noqa: E402
    DEFAULT_HRU_PARAMS,
    DEFAULT_MF,
    DEFAULT_TT,
    simulate_cover_elevation,
)
from landcover import load_hru_weights  # noqa: E402
from load import find_data_root, load_camels, load_gauge  # noqa: E402
from model import simulate  # noqa: E402
from plot_style import (  # noqa: E402
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    figure_note,
    line_style,
    set_title,
    style_axes,
)
from snow_ros import DEFAULT_K_ROS  # noqa: E402

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


def run_lumped(period: pd.DataFrame, params: dict) -> list[float]:
    result = simulate(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        **params,
    )
    return result["Q"]


def run_hru_bands(period: pd.DataFrame, data_root: Path, gauge: int) -> list[float]:
    weights = load_hru_weights(
        data_root / "static_attributes" / "CAMELS_CH_landcover_attributes.csv",
        gauge,
    )
    bands, z_ref = load_bands(
        data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv",
        gauge,
    )
    result = simulate_cover_elevation(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        weights,
        DEFAULT_HRU_PARAMS,
        bands,
        z_ref,
        lapse=DEFAULT_LAPSE,
        mf=DEFAULT_MF,
        tt=DEFAULT_TT,
        k_ros=DEFAULT_K_ROS,
    )
    return result["Q"]


def plot_window(
    period: pd.DataFrame,
    lines: list[tuple[str, str, dict]],
    *,
    title: str,
    subtitle: str,
    note: str,
    out: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for column, label, style in lines:
        ax.plot(period["date"], period[column], label=label, **style)
    ax.set_ylabel("Discharge [mm/d]")
    ax.set_ylim(bottom=0)
    set_title(ax, title, subtitle=subtitle)
    style_axes(ax)
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
    note_lumped = (
        f"CAMELS-CH {GAUGE}, {river}, {gauge_name}. "
        "Q/P/T observed catchment mean; PET = CAMELS pet_sim. "
        f"Lumped flowerpot. {param_line}."
    )
    note_compare = (
        f"CAMELS-CH {GAUGE}, {river}, {gauge_name}. "
        "Obs + Ex04 lumped + future_ideas HRU cover × elev bands (+ROS). "
        f"Lumped: {param_line}."
    )
    titles = {
        "better": "Better window — timing ok, peaks still low",
        "bad": "Bad window — rain-on-snow, peak strongly underestimated",
    }
    subtitles = {
        "better": "2010-07-09 to 2010-08-02. Thur at Jonschwil-Mühlau.",
        "bad": (
            "2020-01-28 to 2020-02-12. Thur at Jonschwil-Mühlau. "
            "Rain-on-snow (MeteoSwiss)."
        ),
    }
    hru_style = {**line_style(2), "lw": 1.8}

    for start, end, tag in (BETTER, BAD):
        full = camels.loc[(camels["date"] >= WARM_START) & (camels["date"] <= end)].copy()
        full["Q_lumped"] = run_lumped(full, params)
        full["Q_hru"] = run_hru_bands(full, root, GAUGE)
        period = full.loc[(full["date"] >= start) & (full["date"] <= end)].copy()
        subtitle = subtitles[tag]

        plot_window(
            period,
            [
                ("Q", "Observed Q", {"color": OUTFLOW_COLOR, "lw": 1.5}),
                ("Q_lumped", "Modelled Q", {"color": STORAGE_COLOR, "lw": 1.8}),
            ],
            title=titles[tag],
            subtitle=subtitle,
            note=note_lumped,
            out=FIGURES / f"event_{tag}_{start}_{end}.png",
        )
        plot_window(
            period,
            [
                ("Q", "Observed Q", {"color": OUTFLOW_COLOR, "lw": 1.5}),
                ("Q_lumped", "Lumped (Ex04)", {"color": STORAGE_COLOR, "lw": 1.8}),
                ("Q_hru", "HRU × bands", hru_style),
            ],
            title=titles[tag],
            subtitle=subtitle,
            note=note_compare,
            out=FIGURES / f"event_{tag}_hru_bands_{start}_{end}.png",
        )


if __name__ == "__main__":
    main()
