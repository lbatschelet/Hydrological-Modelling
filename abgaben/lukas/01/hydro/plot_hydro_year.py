"""Hydrological-year figure: Q, PET, precipitation and temperature."""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from hydro.style import set_title


def plot_hydro_year(
    period: pd.DataFrame,
    *,
    title: str,
    subtitle: str | None = None,
) -> plt.Figure:
    """Draw one already selected period. Expects date, Q, P, T, PET."""
    fig, (ax_q, ax_t) = plt.subplots(
        2,
        1,
        figsize=(12, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [2.6, 1.0], "hspace": 0.08},
    )
    ax_p = ax_q.twinx()

    ax_q.fill_between(
        period["date"],
        period["Q"],
        step="mid",
        color="#6BAED6",
        alpha=0.55,
        label="Q (discharge)",
        zorder=2,
    )
    ax_q.step(period["date"], period["Q"], where="mid", color="#2171B5", lw=0.8, zorder=3)
    ax_q.fill_between(
        period["date"],
        period["PET"],
        step="mid",
        color="#74C476",
        alpha=0.45,
        label="PET",
        zorder=4,
    )
    ax_q.step(period["date"], period["PET"], where="mid", color="#238B45", lw=0.8, zorder=5)
    ax_p.bar(
        period["date"],
        period["P"],
        width=1.0,
        color="#08519C",
        alpha=0.75,
        label="P (precipitation)",
        zorder=1,
        align="center",
    )

    ax_q.set_ylabel("Q and PET [mm/d]")
    ax_p.set_ylabel("Precipitation [mm/d]")
    ax_p.invert_yaxis()

    q_pet_max = max(period["Q"].max(), period["PET"].max())
    ax_q.set_ylim(0, max(q_pet_max * 1.15, 1))
    p_max = max(float(period["P"].max()), 1.0)
    ax_p.set_ylim(p_max * 2.2, 0)

    set_title(ax_q, title, subtitle=subtitle)

    flux_handles, flux_labels = ax_q.get_legend_handles_labels()
    precip_handles, precip_labels = ax_p.get_legend_handles_labels()
    ax_q.legend(flux_handles + precip_handles, flux_labels + precip_labels, loc="upper left")
    ax_q.grid(True, axis="y", alpha=0.3)
    ax_q.set_zorder(ax_p.get_zorder() + 1)
    ax_q.patch.set_visible(False)

    ax_t.plot(period["date"], period["T"], color="#E6550D", lw=1.0, label="T mean")
    ax_t.axhline(0, color="0.5", lw=0.8, ls="--")
    ax_t.fill_between(
        period["date"],
        period["T"],
        0,
        where=period["T"] >= 0,
        color="#FDAE6B",
        alpha=0.35,
        interpolate=False,
    )
    ax_t.fill_between(
        period["date"],
        period["T"],
        0,
        where=period["T"] < 0,
        color="#9ECAE1",
        alpha=0.45,
        interpolate=False,
    )
    ax_t.set_ylabel("T [°C]")
    ax_t.set_xlabel("Date")
    ax_t.legend(loc="upper left")
    ax_t.grid(True, axis="y", alpha=0.3)
    ax_t.xaxis.set_major_locator(mdates.MonthLocator())
    ax_t.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.text(
        0.01,
        0.01,
        "Q, P, T: observation-based · PET: simulation-based (pet_sim, Penman–Monteith)",
        fontsize=8,
        color="0.4",
    )
    return fig
