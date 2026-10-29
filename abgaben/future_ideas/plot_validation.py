"""Validation quality figures: scatter, residuals, flow-duration. No I/O."""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from metrics import summarise

_LOG_FLOOR = 0.01


def metrics_box_text(m: dict[str, float]) -> str:
    """Compact annotation; bias is (obs−mod)/obs → positive = model too dry."""
    return (
        f"NSE = {m['nse']:.3f}\n"
        f"Nash-Log = {m['nash_log']:.3f}\n"
        f"NSE$_\\mathrm{{high}}$ = {m['nse_high']:.3f}\n"
        f"peak ratio = {m['peak_ratio']:.2f}\n"
        f"RMSE = {m['rmse']:.2f} mm/d\n"
        f"bias = {m['bias']:+.3f}\n"
        f"(bias > 0 → model too dry)"
    )


def plot_obs_vs_mod(
    observed: pd.Series,
    modelled: pd.Series,
    *,
    title: str,
    subtitle: str,
) -> plt.Figure:
    """1:1 scatter of daily Q (linear + log)."""
    obs = np.asarray(observed, dtype=float)
    mod = np.asarray(modelled, dtype=float)
    m = summarise(obs, mod)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    lim = max(float(np.nanmax(obs)), float(np.nanmax(mod)), 1.0) * 1.05

    ax = axes[0]
    ax.scatter(obs, mod, s=8, alpha=0.35, c="0.25", edgecolors="none", rasterized=True)
    ax.plot([0, lim], [0, lim], color="#D95F02", lw=1.4, label="1:1")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Observed Q [mm/d]")
    ax.set_ylabel("Modelled Q [mm/d]")
    ax.set_title("Linear", loc="left", fontsize=11)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="upper left", frameon=False)
    ax.text(
        0.98, 0.02, metrics_box_text(m),
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="0.75", alpha=0.92),
    )

    ax = axes[1]
    o = np.maximum(obs, _LOG_FLOOR)
    s = np.maximum(mod, _LOG_FLOOR)
    ax.scatter(o, s, s=8, alpha=0.35, c="0.25", edgecolors="none", rasterized=True)
    lo = min(o.min(), s.min())
    hi = max(o.max(), s.max())
    grid = np.logspace(np.log10(lo), np.log10(hi), 50)
    ax.plot(grid, grid, color="#D95F02", lw=1.4, label="1:1")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Observed Q [mm/d]")
    ax.set_ylabel("Modelled Q [mm/d]")
    ax.set_title("Log–log", loc="left", fontsize=11)
    ax.grid(True, which="both", alpha=0.35)
    ax.legend(loc="upper left", frameon=False)

    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.01, 0.98, subtitle, ha="left", va="top", fontsize=9, color="0.25")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return fig


def plot_residuals(
    dates: pd.Series,
    observed: pd.Series,
    modelled: pd.Series,
    *,
    title: str,
    subtitle: str,
) -> plt.Figure:
    """Residual time series and residual vs observed."""
    obs = np.asarray(observed, dtype=float)
    mod = np.asarray(modelled, dtype=float)
    res = mod - obs
    m = summarise(obs, mod)
    mean_res = float(np.mean(res))

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), gridspec_kw={"height_ratios": [1.2, 1]})

    ax = axes[0]
    ax.axhline(0.0, color="0.5", lw=1)
    ax.axhline(mean_res, color="#1B9E77", lw=1.2, ls="--", label=f"mean residual = {mean_res:+.3f} mm/d")
    ax.plot(dates, res, color="0.35", lw=0.7)
    ax.set_ylabel("Q$_\\mathrm{mod}$ − Q$_\\mathrm{obs}$ [mm/d]")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.text(0.01, -0.18, subtitle, transform=ax.transAxes, fontsize=9, color="0.3")
    ax.grid(True, axis="y", alpha=0.35)
    ax.legend(loc="upper right", frameon=False)

    ax = axes[1]
    ax.axhline(0.0, color="0.5", lw=1)
    ax.scatter(obs, res, s=8, alpha=0.35, c="0.25", edgecolors="none", rasterized=True)
    ax.set_xlabel("Observed Q [mm/d]")
    ax.set_ylabel("Residual [mm/d]")
    ax.grid(True, alpha=0.35)
    ax.text(
        0.98, 0.98,
        f"bias (obs−mod)/obs = {m['bias']:+.3f}\nmean(mod−obs) = {mean_res:+.3f} mm/d",
        transform=ax.transAxes, ha="right", va="top", fontsize=8, family="monospace",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="0.75", alpha=0.92),
    )

    fig.tight_layout()
    return fig


def plot_flow_duration(
    observed: pd.Series,
    modelled: pd.Series,
    *,
    title: str,
    subtitle: str,
) -> plt.Figure:
    """Flow-duration curves (exceedance)."""
    obs = np.sort(np.asarray(observed, dtype=float))[::-1]
    mod = np.sort(np.asarray(modelled, dtype=float))[::-1]
    n = len(obs)
    p_obs = np.arange(1, n + 1) / (n + 1)
    p_mod = np.arange(1, len(mod) + 1) / (len(mod) + 1)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(p_obs * 100, obs, color="#D95F02", lw=1.6, label="Observed")
    ax.plot(p_mod * 100, mod, color="#1B9E77", lw=1.6, label="Modelled")
    ax.set_xlabel("Exceedance probability [%]")
    ax.set_ylabel("Discharge [mm/d]")
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.text(0.0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="0.3")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    return fig
