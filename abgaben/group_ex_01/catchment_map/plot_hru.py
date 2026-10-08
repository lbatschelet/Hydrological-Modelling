"""Plot HRU polygons (land use × two slope classes)."""

from __future__ import annotations

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

LANDUSE_COLORS = {
    "Wald": "#2F7D4A",
    "Siedlung": "#C8B8A4",
    "Offenland": "#E8D9A8",
    "Obstanlage": "#A6C94A",
    "Reben": "#7A4E86",
    "Sumpf": "#7D9A72",
    "Fels": "#8A7E74",
    "Geröll": "#D4C6B2",
    "See": "#4C78A8",
    "Gletscher": "#E7F2F6",
}


def plot_hru_map(
    hrus: gpd.GeoDataFrame,
    outlet: gpd.GeoDataFrame,
    *,
    title: str,
    threshold_deg: float,
) -> plt.Figure:
    """Two-panel polygon map: land use and slope class of the same HRUs."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharex=True, sharey=True)
    km = FuncFormatter(lambda value, _pos: f"{value / 1000:.0f}")

    # Left: land use fill
    ax = axes[0]
    for name, color in LANDUSE_COLORS.items():
        part = hrus.loc[hrus["landuse"] == name]
        if part.empty:
            continue
        part.plot(ax=ax, color=color, edgecolor="#555555", linewidth=0.15)
    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.2)
    handles = [
        Patch(facecolor=LANDUSE_COLORS[name], edgecolor="#555555", label=name)
        for name in LANDUSE_COLORS
        if name in set(hrus["landuse"])
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8)
    ax.set_title("Bodennutzung", loc="left", fontweight="bold")

    # Right: slope class fill
    ax = axes[1]
    slope_colors = {"flach": "#F2C14E", "steil": "#C0392B"}
    for name, color in slope_colors.items():
        part = hrus.loc[hrus["slope_class"] == name]
        if part.empty:
            continue
        part.plot(ax=ax, color=color, edgecolor="#555555", linewidth=0.15)
    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.2)
    ax.legend(
        handles=[
            Patch(facecolor=slope_colors["flach"], label=f"flach (< {threshold_deg:.0f}°)"),
            Patch(facecolor=slope_colors["steil"], label=f"steil (≥ {threshold_deg:.0f}°)"),
        ],
        loc="upper left",
        fontsize=8,
    )
    ax.set_title("Steilheit", loc="left", fontweight="bold")

    for ax in axes:
        ax.set_aspect("equal")
        ax.xaxis.set_major_formatter(km)
        ax.yaxis.set_major_formatter(km)
        ax.set_xlabel("Ost (LV95) [km]")
        ax.set_ylabel("Nord (LV95) [km]")
        ax.grid(True, alpha=0.25)

    fig.suptitle(title, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    note = (
        f"HRUs = Bodennutzung ∩ Steilheit (Polygone) · "
        f"Schwelle {threshold_deg:.0f}° · DEM: Copernicus GLO-30"
    )
    fig.text(0.01, 0.01, note, fontsize=8, color="0.4")
    return fig


def plot_hru_combined(
    hrus: gpd.GeoDataFrame,
    outlet: gpd.GeoDataFrame,
    *,
    title: str,
    threshold_deg: float,
) -> plt.Figure:
    """Single map: land-use colour, slope class by hatching."""
    fig, ax = plt.subplots(figsize=(11, 9))
    km = FuncFormatter(lambda value, _pos: f"{value / 1000:.0f}")

    legend_handles = []
    for name, color in LANDUSE_COLORS.items():
        part = hrus.loc[hrus["landuse"] == name]
        if part.empty:
            continue
        part.plot(ax=ax, color=color, edgecolor="#444444", linewidth=0.2)
        legend_handles.append(Patch(facecolor=color, edgecolor="#444444", label=name))

    steil = hrus.loc[hrus["slope_class"] == "steil"]
    if not steil.empty:
        steil.plot(
            ax=ax,
            facecolor="none",
            edgecolor="#5D1A1A",
            linewidth=0.0,
            hatch="////",
        )
    legend_handles.append(
        Patch(facecolor="white", edgecolor="#5D1A1A", hatch="////", label=f"steil (≥ {threshold_deg:.0f}°)")
    )
    legend_handles.append(
        Patch(facecolor="white", edgecolor="#AAAAAA", label=f"flach (< {threshold_deg:.0f}°)")
    )

    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.5)
    ax.set_title(title, loc="left", fontweight="bold", fontsize=13)
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(km)
    ax.yaxis.set_major_formatter(km)
    ax.set_xlabel("Ost (LV95) [km]")
    ax.set_ylabel("Nord (LV95) [km]")
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)
    ax.grid(True, alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "HRU-Polygone: Bodennutzung × Steilheit · DEM Copernicus GLO-30",
        fontsize=8,
        color="0.4",
    )
    fig.tight_layout()
    return fig
