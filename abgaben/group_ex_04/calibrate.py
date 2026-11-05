# Exercise 4: calibrate lumped flowerpot (warmup / cal / val).

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
EX03 = HERE.parent / "group_ex_03"
sys.path.insert(0, str(EX03))
sys.path.insert(0, str(HERE))

from load import find_data_root, load_camels  # noqa: E402
from metrics import score  # noqa: E402
from model import simulate  # noqa: E402

GAUGE = 2303
IMAX = 2.0  # fixed (thin canopy)

WARM_START, WARM_END = "1981-01-01", "1982-12-31"
CAL_START, CAL_END = "1983-01-01", "2009-12-31"
VAL_START, VAL_END = "2010-01-01", "2020-12-31"

# Coarse grid — keep it small.
MF_VALUES = [0.6, 1.0, 1.5]
TT_VALUES = [0.5, 1.0, 2.0]
K_VALUES = [0.05, 0.1, 0.2, 0.3]
SMAX_VALUES = [40, 80, 120, 160]


def run_q(frame: pd.DataFrame, *, mf: float, tt: float, k: float, smax: float) -> pd.Series:
    out = simulate(
        frame["P"].tolist(),
        frame["T"].tolist(),
        frame["PET"].tolist(),
        imax=IMAX,
        mf=mf,
        tt=tt,
        k=k,
        smax=smax,
    )
    return pd.Series(out["Q"], index=frame.index)


def window_score(full: pd.DataFrame, q: pd.Series, start: str, end: str) -> dict[str, float]:
    mask = (full["date"] >= start) & (full["date"] <= end)
    return score(full.loc[mask, "Q"], q.loc[mask])


def fmt(m: dict[str, float]) -> str:
    return f"NSE={m['nse']:.3f}  Nash-Log={m['nash_log']:.3f}  bias={m['bias']:+.3f}"


def main() -> None:
    root = find_data_root(HERE)
    camels = load_camels(
        root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{GAUGE}.csv",
        root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{GAUGE}.csv",
    )
    # One continuous run: warmup → end of validation.
    full = camels.loc[(camels["date"] >= WARM_START) & (camels["date"] <= VAL_END)].copy()

    print("Exercise 4 — lumped flowerpot (interception + snow + soil/overflow)")
    print(f"Warmup {WARM_START}–{WARM_END}  |  Cal {CAL_START}–{CAL_END}  |  Val {VAL_START}–{VAL_END}")
    print(f"Imax fixed at {IMAX}. Objective on cal: maximize ½ NSE + ½ Nash-Log.\n")

    best = None
    ranked = []
    for mf in MF_VALUES:
        for tt in TT_VALUES:
            for k in K_VALUES:
                for smax in SMAX_VALUES:
                    q = run_q(full, mf=mf, tt=tt, k=k, smax=smax)
                    cal = window_score(full, q, CAL_START, CAL_END)
                    fitness = 0.5 * cal["nse"] + 0.5 * cal["nash_log"]
                    params = dict(mf=mf, tt=tt, k=k, smax=smax)
                    ranked.append((fitness, params, cal))
                    if best is None or fitness > best[0]:
                        best = (fitness, params, cal, q)

    ranked.sort(key=lambda row: row[0], reverse=True)
    fitness, params, cal, q = best
    val = window_score(full, q, VAL_START, VAL_END)

    print("Best parameter set:")
    print(
        f"  mf={params['mf']}, TT={params['tt']}, k={params['k']}, "
        f"Smax={params['smax']}, Imax={IMAX}"
    )
    print(f"  Cal: {fmt(cal)}")
    print(f"  Val: {fmt(val)}")
    print("\nNear-best on cal (equifinality):")
    for fit, p, c in ranked[:5]:
        print(
            f"  fit={fit:.3f}  mf={p['mf']} TT={p['tt']} k={p['k']} Smax={p['smax']}  "
            f"NSE={c['nse']:.3f} Nash-Log={c['nash_log']:.3f}"
        )

    # One-at-a-time sensitivity around the optimum (largest influence?).
    print("\nSensitivity (vary one parameter, others at optimum):")
    base = params
    grids = {
        "mf": MF_VALUES,
        "tt": TT_VALUES,
        "k": K_VALUES,
        "smax": SMAX_VALUES,
    }
    spreads = {}
    for name, values in grids.items():
        fits = []
        for v in values:
            trial = dict(base)
            trial[name] = v
            q_t = run_q(full, **trial)
            cal_t = window_score(full, q_t, CAL_START, CAL_END)
            fits.append(0.5 * cal_t["nse"] + 0.5 * cal_t["nash_log"])
        spread = max(fits) - min(fits)
        spreads[name] = spread
        print(f"  {name}: fitness range {min(fits):.3f} … {max(fits):.3f}  (Δ={spread:.3f})")

    top = max(spreads, key=spreads.get)
    print(f"\nLargest influence on this grid: {top} (Δ fitness = {spreads[top]:.3f})")

    # Save pick for plotting script.
    pick = HERE / "best_params.txt"
    pick.write_text(
        f"mf={params['mf']}\nTT={params['tt']}\nk={params['k']}\n"
        f"Smax={params['smax']}\nImax={IMAX}\n"
        f"cal_nse={cal['nse']:.4f}\ncal_nash_log={cal['nash_log']:.4f}\ncal_bias={cal['bias']:.4f}\n"
        f"val_nse={val['nse']:.4f}\nval_nash_log={val['nash_log']:.4f}\nval_bias={val['bias']:.4f}\n"
        f"most_sensitive={top}\n"
    )
    print(f"\nWrote {pick}")


if __name__ == "__main__":
    main()
