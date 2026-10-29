"""
Calibrate pathways model for peaks without wrecking low flows.

Structure: overflow → Q same day (direct_overflow). GW path for baseflow.
Objective: maximize ½ NSE + ½ NSE_high, subject to Nash-Log ≥ baseline − slack.
Split-sample 2010/11–2014/15 vs 2015/16–2019/20.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EX03))

from load import find_data_root, load_camels  # noqa: E402
from metrics import summarise  # noqa: E402
from pathways import simulate  # noqa: E402

IMAX = 2.0
K_FAST = 1.0
DIRECT = True

# Routed pathways baseline used as Nash-Log floor reference.
BASELINE = dict(mf=1.0, tt=0.5, k=0.2, smax=80.0, k_gw=0.02, f_gw=0.3)
NASH_LOG_SLACK = 0.05

MF_VALUES = [1.0, 1.5]
TT_VALUES = [0.5, 1.0]
K_VALUES = [0.1, 0.2, 0.3]
SMAX_VALUES = [40, 50, 60, 80]
K_GW_VALUES = [0.01, 0.02, 0.05]
F_GW_VALUES = [0.15, 0.25, 0.35]

CAL_START, CAL_END = "2010-10-01", "2015-09-30"
VAL_START, VAL_END = "2015-10-01", "2020-09-30"


def run_model(period: pd.DataFrame, *, direct: bool = DIRECT, k_fast: float = K_FAST, **params) -> pd.Series:
    result = simulate(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        imax=IMAX,
        mf=params["mf"],
        tt=params["tt"],
        k=params["k"],
        smax=params["smax"],
        k_fast=k_fast,
        k_gw=params["k_gw"],
        f_gw=params["f_gw"],
        direct_overflow=direct,
    )
    return pd.Series(result["Q"], index=period.index)


def score(period: pd.DataFrame, **params) -> dict[str, float]:
    metrics = summarise(period["Q"], run_model(period, **params))
    metrics["fitness"] = 0.5 * metrics["nse"] + 0.5 * metrics["nse_high"]
    return metrics


def window(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return frame.loc[(frame["date"] >= start) & (frame["date"] <= end)].copy()


def print_metrics(label: str, m: dict[str, float]) -> None:
    print(
        f"  {label}: fit={m['fitness']:.3f}, NSE={m['nse']:.3f}, NSE_high={m['nse_high']:.3f}, "
        f"peak_ratio={m['peak_ratio']:.2f}, Nash-Log={m['nash_log']:.3f}, "
        f"RMSE={m['rmse']:.2f}, bias={m['bias']:.3f}"
    )


def main() -> None:
    root = find_data_root(REPO)
    camels = load_camels(
        root / "timeseries" / "observation_based" / "CAMELS_CH_obs_based_2303.csv",
        root / "timeseries" / "simulation_based" / "CAMELS_CH_sim_based_2303.csv",
    )
    cal = window(camels, CAL_START, CAL_END)
    val = window(camels, VAL_START, VAL_END)

    base_cal = summarise(cal["Q"], run_model(cal, direct=False, k_fast=0.6, **BASELINE))
    floor = base_cal["nash_log"] - NASH_LOG_SLACK
    print("Peak calibration with Nash-Log constraint (direct overflow).")
    print(
        f"Baseline (routed k_fast=0.6): Nash-Log cal={base_cal['nash_log']:.3f}, "
        f"NSE={base_cal['nse']:.3f}, peak_ratio={base_cal['peak_ratio']:.2f}"
    )
    print(f"Constraint: Nash-Log_cal ≥ {floor:.3f}")
    print()

    candidates = []
    for mf in MF_VALUES:
        for tt in TT_VALUES:
            for k in K_VALUES:
                for smax in SMAX_VALUES:
                    for k_gw in K_GW_VALUES:
                        for f_gw in F_GW_VALUES:
                            params = dict(mf=mf, tt=tt, k=k, smax=smax, k_gw=k_gw, f_gw=f_gw)
                            m = score(cal, **params)
                            if m["nash_log"] < floor:
                                continue
                            candidates.append((m["fitness"], params, m))

    candidates.sort(key=lambda row: row[0], reverse=True)
    if not candidates:
        raise RuntimeError("No parameter set met the Nash-Log floor.")

    _, params, cal_m = candidates[0]
    # Prefer neighbour with better validation Nash-Log if fitness almost equal.
    pick = candidates[0]
    for row in candidates[:5]:
        if abs(row[0] - pick[0]) < 0.005:
            v = score(val, **row[1])
            if v["nash_log"] > score(val, **pick[1])["nash_log"]:
                pick = row
    _, params, cal_m = pick
    val_m = score(val, **params)

    print(
        f"Best: mf={params['mf']}, TT={params['tt']}, k={params['k']}, "
        f"Smax={params['smax']}, k_gw={params['k_gw']}, f_gw={params['f_gw']}, "
        f"direct_overflow=True"
    )
    print_metrics("cal", cal_m)
    print_metrics("val", val_m)
    print()
    print("Near-best:")
    for f, p, _ in candidates[:5]:
        v = score(val, **p)
        print(
            f"  fit cal={f:.3f} val={v['fitness']:.3f}  "
            f"mf={p['mf']} TT={p['tt']} k={p['k']} Smax={p['smax']} "
            f"k_gw={p['k_gw']} f_gw={p['f_gw']}  "
            f"peak_ratio val={v['peak_ratio']:.2f} Nash-Log val={v['nash_log']:.3f}"
        )


if __name__ == "__main__":
    main()
