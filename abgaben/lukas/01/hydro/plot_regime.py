"""Mean monthly discharge for two periods."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from hydro.series import MONTHS
from hydro.style import set_title

MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def plot_regime(
    early: pd.Series,
    late: pd.Series,
    *,
    title: str,
    early_label: str,
    late_label: str,
    note: str,
    subtitle: str | None = None,
) -> plt.Figure:
    """Twelve monthly means per period, connected by straight lines."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for series, color, label in (
        (early, "#D62728", early_label),
        (late, "#1F77B4", late_label),
    ):
        ax.plot(MONTHS, series, color=color, lw=2.2, marker="o", markersize=5, label=label)

    ax.set_xticks(MONTHS)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlim(0.5, 12.5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Months")
    ax.set_ylabel("Mean monthly discharge [m³/s]")
    set_title(ax, title, subtitle=subtitle)
    ax.grid(True, axis="y", alpha=0.35)
    ax.legend(loc="upper right")
    ax.spines["right"].set_visible(False)
    fig.text(0.01, 0.01, note, fontsize=8, color="0.4")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    return fig
