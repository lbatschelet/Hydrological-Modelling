# Pathways lumped with direct overflow vs Ex03 simple flowerpot.
# Continuous series with spin-up; plot window only.

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
REPO = HERE.parents[1]


def _load_ex03_model():
    spec = importlib.util.spec_from_file_location("ex03_model", EX03 / "model.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(EX03))
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from hru_model import LUMPED_PEAK_PARAMS  # noqa: E402
from metrics import summarise  # noqa: E402
from pathways import simulate as simulate_pathways  # noqa: E402
from plot_style import apply_style  # noqa: E402
from series import running_slice  # noqa: E402

sys.path.insert(0, str(EX03))
from load import find_data_root, load_camels, load_gauge  # noqa: E402
from run import IMAX, K, MF, SMAX, TT, plot_runoff  # noqa: E402

ex03_model = _load_ex03_model()
FIGURES = HERE / "figures"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--start", default="2019-10-01")
    parser.add_argument("--end", default="2020-09-30")
    parser.add_argument(
        "--spin-years",
        type=int,
        default=None,
        help="If set, only warm up this many years before start (not full record)",
    )
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    data_root = find_data_root(HERE)
    obs = data_root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{args.gauge}.csv"
    sim = data_root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{args.gauge}.csv"
    attrs = data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"
    river, gauge_name = load_gauge(attrs, args.gauge)

    camels = load_camels(obs, sim)
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)
    full, period = running_slice(
        camels, start, end,
        from_record_start=args.spin_years is None,
        spin_years=args.spin_years,
    )
    plot_mask = (full["date"] >= start) & (full["date"] <= end)

    q_ex03_full = pd.Series(
        ex03_model.simulate(
            full["P"].tolist(),
            full["T"].tolist(),
            full["PET"].tolist(),
            imax=IMAX,
            mf=MF,
            tt=TT,
            k=K,
            smax=SMAX,
        )["Q"],
        index=full.index,
    )
    p = LUMPED_PEAK_PARAMS
    q_new_full = pd.Series(
        simulate_pathways(
            full["P"].tolist(),
            full["T"].tolist(),
            full["PET"].tolist(),
            imax=IMAX,
            mf=p["mf"],
            tt=p["tt"],
            k=p["k"],
            smax=p["smax"],
            k_fast=1.0,
            k_gw=p["k_gw"],
            f_gw=p["f_gw"],
            direct_overflow=True,
        )["Q"],
        index=full.index,
    )
    q_ex03 = q_ex03_full.loc[plot_mask]
    q_new = q_new_full.loc[plot_mask]
    period["Q_mod"] = q_new.values

    fig = plot_runoff(
        period,
        title=f"Peak-tuned pathways — {river}, {gauge_name}, {start.year}/{end.year}",
        subtitle=(
            f"running series from {full['date'].iloc[0].date()}. direct overflow. "
            f"mf={p['mf']:g}, TT={p['tt']:g}, Smax={p['smax']:g}, "
            f"k={p['k']:g}, k_gw={p['k_gw']:g}, f_gw={p['f_gw']:g}."
        ),
        note=f"CAMELS-CH {args.gauge}. Future ideas — not Ex03.",
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"peaks_lumped_{args.gauge}_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)

    fig2, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(period["date"], period["Q"], color="#D95F02", lw=1.4, label="Observed Q")
    ax.plot(period["date"], q_ex03.values, color="0.45", lw=1.3, label="Ex03 flowerpot")
    ax.plot(period["date"], q_new.values, color="#1B9E77", lw=1.8, label="Future: pathways + direct overflow")
    ax.set_ylabel("Discharge [mm/d]")
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.35)
    ax.legend(loc="upper right")
    ax.set_title(
        f"Ex03 vs peak-tuned — {river}, {gauge_name}, {start.year}/{end.year}",
        loc="left",
        fontweight="bold",
    )
    fig2.autofmt_xdate(rotation=30, ha="right")
    fig2.tight_layout()
    out2 = args.out_dir / f"peaks_vs_ex03_{args.gauge}_{start.year}_{end.year}.png"
    fig2.savefig(out2)
    plt.close(fig2)

    m_old = summarise(period["Q"], q_ex03)
    m_new = summarise(period["Q"], q_new)
    print(f"Running series {full['date'].iloc[0].date()} → {end.date()}; plot {start.date()}–{end.date()}")
    print(f"Saved: {out}")
    print(f"Saved: {out2}")
    print(
        f"Ex03   NSE={m_old['nse']:.3f} NSE_high={m_old['nse_high']:.3f} "
        f"peak_ratio={m_old['peak_ratio']:.2f} Nash-Log={m_old['nash_log']:.3f}"
    )
    print(
        f"Peaks  NSE={m_new['nse']:.3f} NSE_high={m_new['nse_high']:.3f} "
        f"peak_ratio={m_new['peak_ratio']:.2f} Nash-Log={m_new['nash_log']:.3f}"
    )


if __name__ == "__main__":
    main()
