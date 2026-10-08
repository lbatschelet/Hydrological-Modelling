"""OUTPUT 2 — regime plot, two equal halves of 1981–2020."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from hydro.load import load_discharge, load_gauge
from hydro.paths import find_data_root, observation_csv, topography_csv
from hydro.plot_regime import plot_regime
from hydro.series import regime_mean, with_calendar, yearly_monthly_means
# Plotstil aus plot_style.py im Repo-Root, geladen über hydro.style.
from hydro.style import apply_style

HERE = Path(__file__).resolve().parent
DATA_ROOT = find_data_root(HERE)
REPO = DATA_ROOT.parents[1]
FIGURES = HERE / "figures"
EARLY = (1981, 2000)
LATE = (2001, 2020)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    apply_style(REPO / ".mplconfig" / "fonts")
    discharge = with_calendar(load_discharge(observation_csv(args.data_root, args.gauge)))
    early = regime_mean(yearly_monthly_means(discharge, *EARLY))
    late = regime_mean(yearly_monthly_means(discharge, *LATE))
    river, gauge_name = load_gauge(topography_csv(args.data_root), args.gauge)
    fig = plot_regime(
        early,
        late,
        title=f"Regime plot — CAMELS-CH {args.gauge} ({river}, {gauge_name})",
        early_label=f"{EARLY[0]}–{EARLY[1]}",
        late_label=f"{LATE[0]}–{LATE[1]}",
        note="Split: equal 20-yr halves of 1981–2020 · monthly means",
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"regime_{args.gauge}_{EARLY[0]}_{LATE[1]}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
