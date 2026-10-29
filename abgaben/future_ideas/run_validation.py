# Validation-period quality plots (future_ideas pathways ± HRU bands).

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EX03))
sys.path.insert(0, str(REPO))

from elevation import DEFAULT_LAPSE, load_bands  # noqa: E402
from hru_model import (  # noqa: E402
    DEFAULT_HRU_PARAMS,
    DEFAULT_MF,
    DEFAULT_TT,
    LUMPED_PEAK_PARAMS,
    simulate_cover_elevation,
)
from landcover import load_hru_weights  # noqa: E402
from load import find_data_root, load_camels  # noqa: E402
from metrics import summarise  # noqa: E402
from pathways import simulate  # noqa: E402
from plot_style import apply_style  # noqa: E402
from plot_validation import plot_flow_duration, plot_obs_vs_mod, plot_residuals  # noqa: E402
from series import running_slice  # noqa: E402
from snow_ros import DEFAULT_K_ROS  # noqa: E402

FIGURES = HERE / "figures"
VAL_START, VAL_END = "2015-10-01", "2020-09-30"
IMAX = 2.0


def run_pathways(period: pd.DataFrame, *, k_ros: float) -> pd.Series:
    p = LUMPED_PEAK_PARAMS
    result = simulate(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        imax=IMAX,
        mf=p["mf"],
        tt=p["tt"],
        k=p["k"],
        smax=p["smax"],
        k_fast=1.0,
        k_gw=p["k_gw"],
        f_gw=p["f_gw"],
        direct_overflow=True,
        k_ros=k_ros,
    )
    return pd.Series(result["Q"], index=period.index)


def run_hru_bands(period: pd.DataFrame, data_root: Path, gauge: int, *, k_ros: float) -> pd.Series:
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
        k_ros=k_ros,
    )
    return pd.Series(result["Q"], index=period.index)


def print_metrics(label: str, observed: pd.Series, modelled: pd.Series) -> dict[str, float]:
    m = summarise(observed, modelled)
    mean_res = float((modelled - observed).mean())
    print(
        f"{label}: NSE={m['nse']:.3f}, Nash-Log={m['nash_log']:.3f}, "
        f"NSE_high={m['nse_high']:.3f}, peak_ratio={m['peak_ratio']:.2f}, "
        f"RMSE={m['rmse']:.2f}, bias(obs−mod)/obs={m['bias']:+.3f}, "
        f"mean(mod−obs)={mean_res:+.3f} mm/d"
    )
    return m


def save_suite(
    period: pd.DataFrame,
    modelled: pd.Series,
    *,
    tag: str,
    title_model: str,
    out_dir: Path,
) -> None:
    start = period["date"].iloc[0].date()
    end = period["date"].iloc[-1].date()
    subtitle = f"Validation {start} – {end}. CAMELS-CH 2303."
    stem = f"val_{tag}"

    fig = plot_obs_vs_mod(
        period["Q"], modelled,
        title=f"Obs vs mod — {title_model}",
        subtitle=subtitle,
    )
    path = out_dir / f"{stem}_scatter.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")

    fig = plot_residuals(
        period["date"], period["Q"], modelled,
        title=f"Residuals — {title_model}",
        subtitle=subtitle,
    )
    path = out_dir / f"{stem}_residuals.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")

    fig = plot_flow_duration(
        period["Q"], modelled,
        title=f"Flow duration — {title_model}",
        subtitle=subtitle,
    )
    path = out_dir / f"{stem}_fdc.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation quality plots")
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", default=VAL_START)
    parser.add_argument("--end", default=VAL_END)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    parser.add_argument("--k-ros", type=float, default=DEFAULT_K_ROS)
    parser.add_argument(
        "--models",
        default="pathways,hru_bands",
        help="Comma list: pathways, hru_bands",
    )
    args = parser.parse_args()

    apply_style()
    data_root = find_data_root(HERE)
    camels = load_camels(
        data_root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{args.gauge}.csv",
        data_root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{args.gauge}.csv",
    )
    full, period = running_slice(camels, args.start, args.end, from_record_start=True)
    val_mask = (full["date"] >= args.start) & (full["date"] <= args.end)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"Validation {args.start} → {args.end} "
        f"(running series from {full['date'].iloc[0].date()})"
    )
    print(f"k_ros={args.k_ros:g}")
    print()

    for name in [n.strip() for n in args.models.split(",") if n.strip()]:
        if name == "pathways":
            q_full = run_pathways(full, k_ros=args.k_ros)
            title = "pathways + direct overflow + ROS"
            p = LUMPED_PEAK_PARAMS
            detail = (
                f"mf={p['mf']:g}, TT={p['tt']:g}, k={p['k']:g}, Smax={p['smax']:g}, "
                f"f_gw={p['f_gw']:g}, k_ros={args.k_ros:g}"
            )
        elif name == "hru_bands":
            q_full = run_hru_bands(full, data_root, args.gauge, k_ros=args.k_ros)
            title = "HRU cover × elevation + ROS"
            detail = f"3 cover × 4 bands, k_ros={args.k_ros:g}"
        else:
            raise ValueError(f"Unknown model {name!r}")

        modelled = q_full.loc[val_mask]
        print_metrics(name, period["Q"], modelled)
        print(f"  ({detail})")
        save_suite(period, modelled, tag=name, title_model=title, out_dir=args.out_dir)
        print()


if __name__ == "__main__":
    main()
