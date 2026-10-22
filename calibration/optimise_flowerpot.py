"""Grid search for the flowerpot against observed discharge. Not part of the hand-in."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "abgaben" / "group_ex_03"))

from load import find_data_root, load_camels  # noqa: E402
from model import simulate  # noqa: E402

IMAX = 2.0
MF_VALUES = [0.6, 1.0, 1.5, 2.0, 3.0]
TT_VALUES = [0.5, 1.0, 1.5, 2.0]
K_VALUES = [0.05, 0.1, 0.2, 0.3, 0.5]
SMAX_VALUES = [40, 60, 80, 100, 150, 200]


def rmse(period: pd.DataFrame, mf: float, tt: float, k: float, smax: float) -> float:
    result = simulate(
        period["P"].tolist(),
        period["T"].tolist(),
        period["PET"].tolist(),
        imax=IMAX,
        mf=mf,
        tt=tt,
        k=k,
        smax=smax,
    )
    error = pd.Series(result["Q"]) - period["Q"].reset_index(drop=True)
    return float((error.pow(2).mean()) ** 0.5)


def search(period: pd.DataFrame) -> list[tuple[float, float, float, float, float]]:
    scores = [
        (rmse(period, mf, tt, k, smax), mf, tt, k, smax)
        for mf in MF_VALUES
        for tt in TT_VALUES
        for k in K_VALUES
        for smax in SMAX_VALUES
    ]
    scores.sort()
    return scores


def main() -> None:
    root = find_data_root(REPO)
    camels = load_camels(
        root / "timeseries" / "observation_based" / "CAMELS_CH_obs_based_2303.csv",
        root / "timeseries" / "simulation_based" / "CAMELS_CH_sim_based_2303.csv",
    )
    decade = camels.loc[
        (camels["date"] >= "2010-10-01") & (camels["date"] <= "2020-09-30")
    ].copy()
    winter = camels.loc[
        (camels["date"] >= "2019-10-01") & (camels["date"] <= "2020-09-30")
    ].copy()

    print("Defaults (mf=1, TT=2, k=0.1, Smax=80)")
    print(f"  2010–2020 RMSE {rmse(decade, 1.0, 2.0, 0.1, 80):.2f} mm/d")
    print(f"  2019/20   RMSE {rmse(winter, 1.0, 2.0, 0.1, 80):.2f} mm/d")

    decade_best = search(decade)[0]
    winter_best = search(winter)[0]
    print(
        f"Best on 2010–2020: mf={decade_best[1]}, TT={decade_best[2]}, "
        f"k={decade_best[3]}, Smax={decade_best[4]} → RMSE {decade_best[0]:.2f} mm/d"
    )
    print(
        f"Best on 2019/20:   mf={winter_best[1]}, TT={winter_best[2]}, "
        f"k={winter_best[3]}, Smax={winter_best[4]} → RMSE {winter_best[0]:.2f} mm/d"
    )


if __name__ == "__main__":
    main()
