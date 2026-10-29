# Personal ex 03: CAMELS observed Q vs CAMELS simulated Q (gauge 2303).

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from plot_style import apply_style  # noqa: E402

GAUGE = 2303
FIGURES = HERE / "figures"
LOG_FLOOR = 0.01


def find_camels(start: Path) -> Path:
    for p in (start, *start.parents):
        root = p / "data" / "camels_ch"
        if root.is_dir():
            return root
    raise FileNotFoundError("data/camels_ch not found")


def load_obs_sim(root: Path, gauge: int) -> pd.DataFrame:
    obs = pd.read_csv(
        root / "timeseries" / "observation_based" / f"CAMELS_CH_obs_based_{gauge}.csv",
        parse_dates=["date"],
    )
    sim = pd.read_csv(
        root / "timeseries" / "simulation_based" / f"CAMELS_CH_sim_based_{gauge}.csv",
        parse_dates=["date"],
    )
    df = obs[["date", "discharge_spec(mm/d)"]].merge(
        sim[["date", "discharge_spec_sim(mm/d)"]], on="date"
    )
    return df.rename(
        columns={"discharge_spec(mm/d)": "Q_obs", "discharge_spec_sim(mm/d)": "Q_sim"}
    ).dropna()


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    return 1.0 - float(np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))


def nash_log(obs: np.ndarray, sim: np.ndarray) -> float:
    zo = np.log(np.maximum(obs, LOG_FLOOR))
    zs = np.log(np.maximum(sim, LOG_FLOOR))
    return 1.0 - float(np.sum((zo - zs) ** 2) / np.sum((zo - zo.mean()) ** 2))


def bias(obs: np.ndarray, sim: np.ndarray) -> float:
    """(Σobs − Σsim) / Σobs. >0 = sim too dry."""
    return float((obs - sim).sum() / obs.sum())


def scores(obs: pd.Series, sim: pd.Series) -> dict[str, float]:
    o, s = obs.to_numpy(float), sim.to_numpy(float)
    high = o >= np.quantile(o, 0.9)
    return {
        "nse": nse(o, s),
        "nash_log": nash_log(o, s),
        "nse_high": nse(o[high], s[high]),
        "bias": bias(o, s),
        "peak_ratio": float(s[high].mean() / o[high].mean()),
    }


def season_of(month: int) -> str:
    if month in (12, 1, 2):
        return "DJF"
    if month in (3, 4, 5):
        return "MAM"
    if month in (6, 7, 8):
        return "JJA"
    return "SON"


def main() -> None:
    apply_style()
    root = find_camels(HERE)
    df = load_obs_sim(root, GAUGE)
    FIGURES.mkdir(parents=True, exist_ok=True)

    m = scores(df["Q_obs"], df["Q_sim"])
    print(
        f"Overall NSE={m['nse']:.3f}  Nash-Log={m['nash_log']:.3f}  "
        f"NSE_high={m['nse_high']:.3f}  peak_ratio={m['peak_ratio']:.2f}  "
        f"bias={m['bias']:+.3f}"
    )

    # --- 1:1 scatter (overall + low flows) ---
    o, s = df["Q_obs"].to_numpy(float), df["Q_sim"].to_numpy(float)
    lim = max(o.max(), s.max()) * 1.05
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    axes[0].scatter(o, s, s=5, alpha=0.25, c="0.3", edgecolors="none", rasterized=True)
    axes[0].plot([0, lim], [0, lim], color="#D95F02", lw=1.3)
    axes[0].set(xlim=(0, lim), ylim=(0, lim), xlabel="Observed Q [mm/d]", ylabel="Simulated Q [mm/d]")
    axes[0].set_title("Linear", loc="left")
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].text(
        0.97, 0.03,
        f"NSE={m['nse']:.2f}\nNash-Log={m['nash_log']:.2f}\n"
        f"NSE_high={m['nse_high']:.2f}\nbias={m['bias']:+.2f}",
        transform=axes[0].transAxes, ha="right", va="bottom", fontsize=8, family="monospace",
        bbox=dict(facecolor="white", edgecolor="0.75", boxstyle="round,pad=0.3"),
    )
    axes[1].scatter(
        np.maximum(o, LOG_FLOOR), np.maximum(s, LOG_FLOOR),
        s=5, alpha=0.25, c="0.3", edgecolors="none", rasterized=True,
    )
    axes[1].plot([LOG_FLOOR, lim], [LOG_FLOOR, lim], color="#D95F02", lw=1.3)
    axes[1].set(xscale="log", yscale="log", xlabel="Observed Q [mm/d]", ylabel="Simulated Q [mm/d]")
    axes[1].set_title("Log (low flows)", loc="left")
    fig.suptitle("CAMELS obs vs sim — Thur 2303 (1981–2020)", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "camels_obs_vs_sim_2303_scatter.png", dpi=150)
    plt.close(fig)

    # --- monthly regime ---
    monthly = df.assign(month=df["date"].dt.month).groupby("month")[["Q_obs", "Q_sim"]].mean()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(monthly.index, monthly["Q_obs"], "o-", color="#D95F02", lw=2, label="Observed")
    ax.plot(monthly.index, monthly["Q_sim"], "o-", color="#1B9E77", lw=2, label="CAMELS sim")
    ax.set(xticks=range(1, 13), xticklabels=list("JFMAMJJASOND"),
           ylabel="Mean Q [mm/d]", xlabel="Month", ylim=(0, None))
    ax.set_title("Mean monthly regime — is the seasonality right?", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.35)
    fig.tight_layout()
    fig.savefig(FIGURES / "camels_obs_vs_sim_2303_regime.png", dpi=150)
    plt.close(fig)

    # --- seasonal NSE / bias (which season sticks out?) ---
    df = df.assign(season=df["date"].dt.month.map(season_of))
    order = ["DJF", "MAM", "JJA", "SON"]
    rows = {name: scores(g["Q_obs"], g["Q_sim"]) for name, g in df.groupby("season")}
    for name in order:
        r = rows[name]
        print(f"  {name}: NSE={r['nse']:.3f}  Nash-Log={r['nash_log']:.3f}  bias={r['bias']:+.3f}")

    x = np.arange(len(order))
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    axes[0].bar(x - 0.2, [rows[s]["nse"] for s in order], 0.4, color="#1B9E77", label="NSE")
    axes[0].bar(x + 0.2, [rows[s]["nash_log"] for s in order], 0.4, color="#7570B3", label="Nash-Log")
    axes[0].set(xticks=x, xticklabels=order, ylabel="Efficiency")
    axes[0].legend(frameon=False)
    axes[0].grid(True, axis="y", alpha=0.35)
    biases = [rows[s]["bias"] for s in order]
    axes[1].bar(x, biases, color=["#D95F02" if b > 0 else "#1B9E77" for b in biases])
    axes[1].axhline(0, color="0.5", lw=0.8)
    axes[1].set(xticks=x, xticklabels=order, ylabel="Bias (>0 = sim too dry)")
    axes[1].grid(True, axis="y", alpha=0.35)
    fig.suptitle("Which season sticks out?", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "camels_obs_vs_sim_2303_seasons.png", dpi=150)
    plt.close(fig)

    # --- one water year for the eye ---
    wy = df[(df["date"] >= "2019-10-01") & (df["date"] <= "2020-09-30")]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(wy["date"], wy["Q_obs"], color="#D95F02", lw=1.3, label="Observed")
    ax.plot(wy["date"], wy["Q_sim"], color="#1B9E77", lw=1.3, label="CAMELS sim")
    ax.set(ylabel="Q [mm/d]", ylim=(0, None))
    ax.set_title("2019/20 hydrograph — events by eye", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.35)
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(FIGURES / "camels_obs_vs_sim_2303_hydro_2019_2020.png", dpi=150)
    plt.close(fig)

    print(f"Figures → {FIGURES}")


if __name__ == "__main__":
    main()
