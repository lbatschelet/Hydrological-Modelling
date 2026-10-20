"""Grid search for the degree-day factor and the melt threshold. Not part of the submission."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "abgaben" / "lukas" / "02"))
sys.path.insert(0, str(REPO))

from first_snow_model import find_data_root, load_snow_forcing, plot_snow, simulate_snow  # noqa: E402
from plot_style import apply_style  # noqa: E402

# Wider than the lecture ranges (mf 1–7, threshold 0–2 °C), so the search can leave that box.
MF_VALUES = [round(0.2 + 0.2 * i, 1) for i in range(40)]  # 0.2 … 8.0
TT_VALUES = [round(-1.0 + 0.25 * i, 2) for i in range(21)]  # −1 … 4 °C
LECTURE_MF = (1.0, 7.0)
LECTURE_TT = (0.0, 2.0)


def snow_record(gauge: int) -> pd.DataFrame:
    """Days from the first SWE value onward. Earlier years have an empty SWE column."""
    root = find_data_root(REPO)
    path = root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{gauge}.csv"
    forcing = load_snow_forcing(path)
    first = forcing.loc[forcing["SWE"].notna(), "date"].iloc[0]
    return forcing.loc[forcing["date"] >= first].reset_index(drop=True)


def rmse(record: pd.DataFrame, mf: float, tt: float) -> float:
    """Root mean square error against SWE. The opening day is the initial store, not a scored day."""
    opening = float(record["SWE"].iloc[0])
    stores, _melts = simulate_snow(
        record["P"].tolist(),
        record["T"].tolist(),
        mf,
        tt,
        opening,
    )
    simulated = pd.Series(stores)
    observed = record["SWE"]
    paired = observed.notna()
    paired.iloc[0] = False
    error = simulated[paired] - observed[paired]
    return float((error.pow(2).mean()) ** 0.5)


def best_on(scores: list[tuple[float, float, float]], mf_bounds, tt_bounds):
    inside = [
        row
        for row in scores
        if mf_bounds[0] <= row[1] <= mf_bounds[1] and tt_bounds[0] <= row[2] <= tt_bounds[1]
    ]
    return min(inside, key=lambda row: row[0])


def main() -> None:
    gauge = 2303
    record = snow_record(gauge)
    scores = [(rmse(record, mf, tt), mf, tt) for tt in TT_VALUES for mf in MF_VALUES]
    scores.sort()
    full = scores[0]
    lecture = best_on(scores, LECTURE_MF, LECTURE_TT)
    current = rmse(record, 1.0, 2.0)

    print(f"SWE days scored: {int(record['SWE'].notna().sum()) - 1}")
    print(f"Record: {record['date'].iloc[0].date()} to {record['date'].iloc[-1].date()}")
    print(f"Current submission (mf=1, tt=2): RMSE {current:.1f} mm")
    print(f"Best inside the lecture ranges: mf={lecture[1]:.1f}, tt={lecture[2]:.1f}, RMSE {lecture[0]:.1f} mm")
    print(f"Best on the wider grid: mf={full[1]:.1f}, tt={full[2]:.1f}, RMSE {full[0]:.1f} mm")
    print("Next best:")
    for error, mf, tt in scores[1:6]:
        print(f"  mf={mf:.1f}, tt={tt:.1f}, RMSE {error:.1f} mm")

    apply_style()
    start = pd.Timestamp("2019-10-01")
    end = pd.Timestamp("2020-09-30")
    period = record.loc[(record["date"] >= start) & (record["date"] <= end)].copy()
    opening = period["SWE"].iloc[0]
    swe0 = 0.0 if pd.isna(opening) else float(opening)
    stores, _melts = simulate_snow(period["P"].tolist(), period["T"].tolist(), full[1], full[2], swe0)
    period["SWE_sim"] = stores
    fig = plot_snow(
        period["date"],
        period["SWE_sim"],
        period["SWE"],
        title=f"Snow store — CAMELS-CH {gauge}, 2019/2020",
        subtitle=(
            f"Degree-day factor {full[1]:.1f} mm/°C/d, threshold {full[2]:.1f} °C, "
            f"fit on the whole SWE record. "
            f"The simulated peak is {period['SWE_sim'].max():.0f} mm, "
            f"the observed peak is {period['SWE'].max():.0f} mm."
        ),
    )
    out_dir = Path(__file__).resolve().parent / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "snow_2303_2019_2020_optimised.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
