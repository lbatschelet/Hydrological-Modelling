"""Shared figure style. Color palette to aide my color blindness"""

from __future__ import annotations

import matplotlib.pyplot as plt
from cycler import cycler

_OKABE_ITO = (
    "black",
    "orange",
    "sky_blue",
    "bluish_green",
    "yellow",
    "blue",
    "vermillion",
    "reddish_purple",
)

# Petroff positions with the same contrast: blue, orange, purple.
_LINE_COLOR_INDEX = (0, 6, 4)
_LINE_DASHES = ("solid", "dashed", "dashdot")


def _okabe_ito(name: str):
    return plt.color_sequences["okabe_ito"][_OKABE_ITO.index(name)]


STORAGE_COLOR = _okabe_ito("blue")
OUTFLOW_COLOR = _okabe_ito("vermillion")
ET_COLOR = _okabe_ito("bluish_green")


def line_style(index: int) -> dict:
    """Colour and dash pattern. A set of lines is not identified by colour alone."""
    colors = plt.color_sequences["petroff10"]
    palette = [colors[i] for i in _LINE_COLOR_INDEX]
    return {
        "color": palette[index % len(palette)],
        "linestyle": _LINE_DASHES[index // len(palette)],
    }


def set_title(
    ax,
    text: str,
    *,
    subtitle: str | None = None,
    size: float | None = None,
    pad: float = 12,
) -> None:
    """Left-aligned bold title. The subtitle is the sentence the figure is there to show."""
    ax.set_title(
        text,
        loc="left",
        pad=pad + (16 if subtitle else 0),
        fontweight="bold",
        fontsize=size or plt.rcParams["axes.titlesize"],
    )
    if not subtitle:
        return
    ax.annotate(
        subtitle,
        xy=(0, 1),
        xycoords="axes fraction",
        xytext=(0, 3),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=plt.rcParams["font.size"],
        color="0.25",
        annotation_clip=False,
    )


def new_figure():
    """One axes in the standard figure size."""
    return plt.subplots(figsize=(10, 5.5))


def style_axes(ax) -> None:
    """Horizontal grid, open right side, legend inside at the upper right."""
    ax.grid(True, axis="y", alpha=0.35)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=True, facecolor="white", framealpha=1)


def apply_style() -> None:
    """Helvetica, then Arial. Liberation Sans and DejaVu Sans if neither is installed."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"],
            "axes.prop_cycle": cycler(color=plt.color_sequences["petroff10"]),
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "legend.frameon": True,
            "legend.fancybox": False,
            "legend.edgecolor": "0.85",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "0.35",
            "axes.linewidth": 0.8,
            "grid.color": "0.85",
            "grid.linewidth": 0.7,
            "axes.grid": False,
            "figure.dpi": 120,
            "savefig.dpi": 160,
            "savefig.bbox": "tight",
            "axes.unicode_minus": False,
        }
    )
