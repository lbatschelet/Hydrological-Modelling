"""Land-cover map of one catchment and the gauged basins that drain into it."""

from __future__ import annotations

import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

LANDCOVER_COLORS = {
    "Wald": "#2F7D4A",
    "Siedl": "#C8B8A4",
    "Stadtzentr": "#6B5E55",
    "Obstanlage": "#A6C94A",
    "Reben": "#7A4E86",
    "Sumpf": "#7D9A72",
    "Fels": "#8A7E74",
    "Geroell": "#D4C6B2",
    "Gletscher": "#E7F2F6",
    "See": "#4C78A8",
    "Stausee": "#2C4F86",
}
LANDCOVER_LABELS = {
    "Wald": "Wald",
    "Siedl": "Siedlung",
    "Stadtzentr": "Stadtzentrum",
    "Obstanlage": "Obstanlage",
    "Reben": "Reben",
    "Sumpf": "Sumpf",
    "Fels": "Fels",
    "Geroell": "Geröll",
    "Gletscher": "Gletscher",
    "See": "See",
    "Stausee": "Stausee",
}
INFLOW_COLORS = ("#1B4F72", "#C46B3A", "#6C3483", "#117A65")


def plot_catchment_map(
    landcover: gpd.GeoDataFrame,
    outlet: gpd.GeoDataFrame,
    inflowing: gpd.GeoDataFrame,
    *,
    title: str,
    station: gpd.GeoDataFrame | None = None,
    rivers: gpd.GeoDataFrame | None = None,
) -> plt.Figure:
    """Draw land cover inside the outlet, with inflowing catchments outlined."""
    fig, ax = plt.subplots(figsize=(11, 9))
    legend_handles: list = []

    outlet.plot(ax=ax, color="#F3F0E8", edgecolor="none")
    legend_handles.append(Patch(facecolor="#F3F0E8", edgecolor="#BBBBBB", label="Übrige Fläche"))

    present = [name for name in LANDCOVER_COLORS if name in set(landcover["OBJVAL"])]
    for name in present:
        landcover.loc[landcover["OBJVAL"] == name].plot(
            ax=ax,
            color=LANDCOVER_COLORS[name],
            edgecolor="none",
        )
        legend_handles.append(Patch(facecolor=LANDCOVER_COLORS[name], label=LANDCOVER_LABELS[name]))

    if rivers is not None and not rivers.empty:
        rivers.plot(ax=ax, color="#1D4E89", linewidth=0.35, alpha=0.85)
        legend_handles.append(Line2D([0], [0], color="#1D4E89", lw=1.2, label="Fliessgewässer"))

    outlet.boundary.plot(ax=ax, color="#1A1A1A", linewidth=1.6)
    legend_handles.append(Line2D([0], [0], color="#1A1A1A", lw=1.6, label="Catchment"))

    for index, row in inflowing.reset_index(drop=True).iterrows():
        color = INFLOW_COLORS[int(index) % len(INFLOW_COLORS)]
        gpd.GeoSeries([row.geometry], crs=inflowing.crs).boundary.plot(
            ax=ax, color=color, linewidth=1.4
        )
        label = f"{row.water_body} ({row.gauge_name})"
        legend_handles.append(Line2D([0], [0], color=color, lw=1.4, label=label))
        point = row.geometry.representative_point()
        ax.annotate(
            str(row.water_body),
            (point.x, point.y),
            ha="center",
            va="center",
            fontsize=9,
            color=color,
        )

    if station is not None and not station.empty:
        station.plot(ax=ax, color="#B01E1E", markersize=36, zorder=5)
        legend_handles.append(
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#B01E1E", markersize=7, label="Station")
        )

    ax.set_title(title, loc="left", fontweight="bold", fontsize=13)
    ax.set_aspect("equal")
    km = FuncFormatter(lambda value, _pos: f"{value / 1000:.0f}")
    ax.xaxis.set_major_formatter(km)
    ax.yaxis.set_major_formatter(km)
    ax.set_xlabel("Ost (LV95) [km]")
    ax.set_ylabel("Nord (LV95) [km]")
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig
