"""Mean monthly discharge for 1981–2000 and 2001–2020."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from hydro.load import load_discharge, load_gauge
from hydro.paths import find_data_root, observation_csv, topography_csv
from hydro.plot_regime import plot_regime
from hydro.series import regime_mean, with_calendar, yearly_monthly_means
# Shared figure style, defined in plot_style.py at the repository root.
from hydro.style import apply_style

HERE = Path(__file__).resolve().parent
DATA_ROOT = find_data_root(HERE)
FIGURES = HERE / "figures"
EARLY = (1981, 2000)
LATE = (2001, 2020)
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _regime_subtitle(early, late) -> str:
    early_month = _MONTHS[int(early.idxmax()) - 1]
    late_month = _MONTHS[int(late.idxmax()) - 1]
    if early_month == late_month:
        sentence = f"Both periods peak in {early_month}."
    else:
        sentence = f"Earlier years peak in {early_month}, later years in {late_month}."
    if all(float(late.loc[month]) < float(early.loc[month]) for month in range(4, 8)):
        sentence += " April to July are lower in the later years."
    return sentence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style()
    discharge = with_calendar(load_discharge(observation_csv(args.data_root, args.gauge)))
    early = regime_mean(yearly_monthly_means(discharge, *EARLY))
    late = regime_mean(yearly_monthly_means(discharge, *LATE))
    river, gauge_name = load_gauge(topography_csv(args.data_root), args.gauge)
    fig = plot_regime(
        early,
        late,
        title=f"Regime plot — CAMELS-CH {args.gauge} ({river}, {gauge_name})",
        subtitle=_regime_subtitle(early, late),
        early_label=f"{EARLY[0]}–{EARLY[1]}",
        late_label=f"{LATE[0]}–{LATE[1]}",
        note="Equal 20-year halves of 1981–2020. Each point is a monthly mean.",
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"regime_{args.gauge}_{EARLY[0]}_{LATE[1]}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
