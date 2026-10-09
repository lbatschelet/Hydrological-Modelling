"""Plot HRU polygons (land use × two slope classes)."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from plot_style import set_title

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
LANDUSE_LABELS = {
    "Wald": "Forest",
    "Siedlung": "Settlement",
    "Offenland": "Open land",
    "Obstanlage": "Orchard",
    "Reben": "Vineyard",
    "Sumpf": "Wetland",
    "Fels": "Rock",
    "Geröll": "Scree",
    "See": "Lake",
    "Gletscher": "Glacier",
}
SLOPE_LABELS = {"flach": "Gentle", "steil": "Steep"}


def hru_subtitle(hrus: gpd.GeoDataFrame) -> str:
    """One sentence from the area shares. Only states a slope pattern when it is clear."""
    totals = hrus.groupby("landuse")["area_km2"].sum()
    top = totals.idxmax()
    top_label = LANDUSE_LABELS.get(top, top)
    if float(totals.max()) > float(totals.sum()) / 2:
        sentence = f"Most of the basin is {top_label.lower()}."
    else:
        sentence = f"{top_label} covers more of the basin than any other class."

    def _mostly(landuse: str, slope: str) -> bool:
        part = hrus.loc[hrus["landuse"] == landuse]
        area = float(part["area_km2"].sum())
        if area == 0:
            return False
        on_slope = float(part.loc[part["slope_class"] == slope, "area_km2"].sum())
        return on_slope > 0.6 * area

    forest_steep = _mostly("Wald", "steil")
    settlement_gentle = _mostly("Siedlung", "flach")
    if forest_steep and settlement_gentle:
        sentence += " Forest sits mostly on steep ground, settlement on gentle ground."
    elif forest_steep:
        sentence += " Forest sits mostly on steep ground."
    elif settlement_gentle:
        sentence += " Settlement sits mostly on gentle ground."
    return sentence


def plot_hru_map(
    hrus: gpd.GeoDataFrame,
    outlet: gpd.GeoDataFrame,
    *,
    title: str,
    threshold_deg: float,
    subtitle: str | None = None,
) -> plt.Figure:
    """Two-panel polygon map: land use and slope class of the same HRUs."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharex=True, sharey=True)
    km = FuncFormatter(lambda value, _pos: f"{value / 1000:.0f}")

    ax = axes[0]
    for name, color in LANDUSE_COLORS.items():
        part = hrus.loc[hrus["landuse"] == name]
        if part.empty:
            continue
        part.plot(ax=ax, color=color, edgecolor="#555555", linewidth=0.15)
    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.2)
    handles = [
        Patch(facecolor=LANDUSE_COLORS[name], edgecolor="#555555", label=LANDUSE_LABELS[name])
        for name in LANDUSE_COLORS
        if name in set(hrus["landuse"])
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8)
    ax.set_title("Land cover", loc="left", fontweight="bold")

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
            Patch(facecolor=slope_colors["flach"], label=f"{SLOPE_LABELS['flach']} (< {threshold_deg:.0f}°)"),
            Patch(facecolor=slope_colors["steil"], label=f"{SLOPE_LABELS['steil']} (≥ {threshold_deg:.0f}°)"),
        ],
        loc="upper left",
        fontsize=8,
    )
    ax.set_title("Slope", loc="left", fontweight="bold")

    for ax in axes:
        ax.set_aspect("equal")
        ax.xaxis.set_major_formatter(km)
        ax.yaxis.set_major_formatter(km)
        ax.set_xlabel("Easting (LV95) [km]")
        ax.set_ylabel("Northing (LV95) [km]")
        ax.grid(True, alpha=0.25)

    fig.suptitle(title, fontweight="bold", x=0.01, ha="left", fontsize=13)
    if subtitle:
        fig.text(0.01, 0.935, subtitle, fontsize=11, color="0.25", ha="left", va="top")
        fig.tight_layout(rect=[0, 0.06, 1, 0.90])
    else:
        fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    note = (
        f"HRUs are land cover intersected with slope, as polygons. "
        f"Threshold {threshold_deg:.0f}°. DEM: Copernicus GLO-30."
    )
    fig.text(0.01, 0.01, note, fontsize=8, color="0.4")
    return fig


def plot_hru_combined(
    hrus: gpd.GeoDataFrame,
    outlet: gpd.GeoDataFrame,
    *,
    title: str,
    threshold_deg: float,
    subtitle: str | None = None,
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
        legend_handles.append(Patch(facecolor=color, edgecolor="#444444", label=LANDUSE_LABELS[name]))

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
        Patch(
            facecolor="white",
            edgecolor="#5D1A1A",
            hatch="////",
            label=f"{SLOPE_LABELS['steil']} (≥ {threshold_deg:.0f}°)",
        )
    )
    legend_handles.append(
        Patch(facecolor="white", edgecolor="#AAAAAA", label=f"{SLOPE_LABELS['flach']} (< {threshold_deg:.0f}°)")
    )

    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.5)
    set_title(ax, title, subtitle=subtitle)
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(km)
    ax.yaxis.set_major_formatter(km)
    ax.set_xlabel("Easting (LV95) [km]")
    ax.set_ylabel("Northing (LV95) [km]")
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)
    ax.grid(True, alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "HRU polygons: land cover × slope. DEM: Copernicus GLO-30.",
        fontsize=8,
        color="0.4",
    )
    fig.tight_layout()
    return fig
