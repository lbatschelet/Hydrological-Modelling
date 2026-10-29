# Cover HRUs (± elevation bands). Continuous series with spin-up; plot window only.

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
sys.path.insert(0, str(EX03))

from elevation import DEFAULT_LAPSE, load_bands  # noqa: E402
from hru_model import (  # noqa: E402
    DEFAULT_HRU_PARAMS,
    DEFAULT_MF,
    DEFAULT_TT,
    LUMPED_PEAK_PARAMS,
    param_summary,
    simulate_cover_elevation,
    simulate_hrus,
)
from landcover import COVER_TO_GROUP, cover_fractions, load_hru_weights, load_landcover_row  # noqa: E402
from load import find_data_root, load_camels, load_gauge  # noqa: E402
from pathways import simulate as simulate_pathways  # noqa: E402
from plot_style import apply_style  # noqa: E402
from run import IMAX, K, MF, SMAX, TT, plot_runoff  # noqa: E402
from series import running_slice  # noqa: E402

ex03_model = _load_ex03_model()
FIGURES = HERE / "figures"


def weight_line(weights: dict[str, float]) -> str:
    return ", ".join(f"{name}={100 * w:.0f}%" for name, w in weights.items())


def main() -> None:
    parser = argparse.ArgumentParser(description="Parallel HRU run (land cover ± elevation)")
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
    parser.add_argument("--bands", action="store_true")
    parser.add_argument("--compare-lumped", action="store_true")
    args = parser.parse_args()

    apply_style()
    data_root = find_data_root(HERE)
    obs = data_root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{args.gauge}.csv"
    sim = data_root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{args.gauge}.csv"
    attrs = data_root / "static_attributes" / "CAMELS_CH_topographic_attributes.csv"
    landcover_path = data_root / "static_attributes" / "CAMELS_CH_landcover_attributes.csv"
    river, gauge_name = load_gauge(attrs, args.gauge)

    camels = load_camels(obs, sim)
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    full, period = running_slice(
        camels, start, end,
        from_record_start=args.spin_years is None,
        spin_years=args.spin_years,
    )
    plot_mask = (full["date"] >= start) & (full["date"] <= end)

    cover_row = load_landcover_row(landcover_path, args.gauge)
    weights = load_hru_weights(landcover_path, args.gauge)
    raw = cover_fractions(cover_row)
    print("CORINE % (all 12 → 3 param groups):")
    for col, pct in raw.items():
        print(f"  {col:18s} {pct:6.2f}%  →  {COVER_TO_GROUP[col]}")
    print(f"Groups: {weight_line(weights)}")
    print(f"Running series {full['date'].iloc[0].date()} → {end.date()}; plot {start.date()}–{end.date()}")

    if args.bands:
        bands, z_ref = load_bands(attrs, args.gauge)
        result = simulate_cover_elevation(
            full["P"].tolist(),
            full["T"].tolist(),
            full["PET"].tolist(),
            weights,
            DEFAULT_HRU_PARAMS,
            bands,
            z_ref,
            lapse=DEFAULT_LAPSE,
            mf=DEFAULT_MF,
            tt=DEFAULT_TT,
        )
        band_line = ", ".join(f"{b.name}@{b.z_m:.0f}m" for b in bands)
        mode = "cover × elevation"
        subtitle = (
            f"running from {full['date'].iloc[0].date()}. {weight_line(weights)}. "
            f"Bands: {band_line}. lapse={DEFAULT_LAPSE} °C/m."
        )
        tag = "hru_bands"
        print(f"Bands (ref elev_mean={z_ref:.0f} m): {band_line}")
    else:
        result = simulate_hrus(
            full["P"].tolist(),
            full["T"].tolist(),
            full["PET"].tolist(),
            weights,
            DEFAULT_HRU_PARAMS,
            mf=DEFAULT_MF,
            tt=DEFAULT_TT,
        )
        mode = "cover only"
        subtitle = (
            f"running from {full['date'].iloc[0].date()}. {weight_line(weights)}. "
            f"{param_summary(DEFAULT_HRU_PARAMS)}."
        )
        tag = "hru"

    q_mod = pd.Series(result["Q"], index=full.index).loc[plot_mask]
    period["Q_mod"] = q_mod.values
    args.out_dir.mkdir(parents=True, exist_ok=True)
    fig = plot_runoff(
        period,
        title=f"HRU ({mode}) — {river}, {gauge_name}, {start.year}/{end.year}",
        subtitle=subtitle,
        note=f"CAMELS-CH {args.gauge}. Direct overflow. Future ideas — not Ex03.",
    )
    out = args.out_dir / f"{tag}_{args.gauge}_camels_{start.year}_{end.year}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")
    print(
        f"Mean Qobs={period['Q'].mean():.2f} mm/d, "
        f"Qmod={period['Q_mod'].mean():.2f} mm/d"
    )

    if args.compare_lumped:
        q_ex03 = pd.Series(
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
        ).loc[plot_mask]
        lp = LUMPED_PEAK_PARAMS
        q_path = pd.Series(
            simulate_pathways(
                full["P"].tolist(),
                full["T"].tolist(),
                full["PET"].tolist(),
                imax=IMAX,
                mf=lp["mf"],
                tt=lp["tt"],
                k=lp["k"],
                smax=lp["smax"],
                k_fast=1.0,
                k_gw=lp["k_gw"],
                f_gw=lp["f_gw"],
                direct_overflow=True,
            )["Q"],
            index=full.index,
        ).loc[plot_mask]
        fig2, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(period["date"], period["Q"], color="#D95F02", lw=1.4, label="Observed Q")
        ax.plot(period["date"], q_ex03.values, color="0.45", lw=1.2, label="Ex03 flowerpot")
        ax.plot(period["date"], q_path.values, color="#7570B3", lw=1.3, label="Pathways lumped")
        ax.plot(period["date"], period["Q_mod"], color="#1B9E77", lw=1.8, label=f"HRU ({mode})")
        ax.set_ylabel("Discharge [mm/d]")
        ax.set_ylim(bottom=0)
        ax.grid(True, axis="y", alpha=0.35)
        ax.legend(loc="upper right")
        ax.set_title(
            f"Ex03 vs future HRU — {river}, {gauge_name}, {start.year}/{end.year}",
            loc="left",
            fontweight="bold",
        )
        fig2.autofmt_xdate(rotation=30, ha="right")
        fig2.tight_layout()
        out2 = args.out_dir / f"{tag}_vs_lumped_{args.gauge}_{start.year}_{end.year}.png"
        fig2.savefig(out2)
        plt.close(fig2)
        print(f"Saved: {out2}")


if __name__ == "__main__":
    main()
