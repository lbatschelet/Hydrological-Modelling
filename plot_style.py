"""Shared figure style: Helvetica Neue, bold left-aligned titles."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parent
_HN_TTC = Path("/System/Library/Fonts/HelveticaNeue.ttc")
_HN_BOLD_INDEX = 1

STORAGE_COLOR = "#1F77B4"
OUTFLOW_COLOR = "#D62728"
LINE_COLORS = [
    "#1F77B4",
    "#D62728",
    "#2CA02C",
    "#FF7F0E",
    "#9467BD",
    "#8C564B",
    "#E377C2",
    "#7F7F7F",
    "#17BECF",
]

_font_cache: Path | None = None
_title_font: FontProperties | None = None


def _ensure_helvetica_neue_bold(cache: Path) -> Path:
    out = cache / "HelveticaNeue-Bold.ttf"
    if out.exists():
        return out

    from fontTools.ttLib import TTCollection

    cache.mkdir(parents=True, exist_ok=True)
    collection = TTCollection(str(_HN_TTC))
    collection.fonts[_HN_BOLD_INDEX].save(str(out))
    return out


def title_font(size: float | None = None) -> FontProperties:
    """Helvetica Neue Bold for plot titles."""
    global _title_font
    if _title_font is None:
        if _font_cache is None:
            raise RuntimeError("Call apply_style() before drawing titles")
        path = _ensure_helvetica_neue_bold(_font_cache)
        font_manager.fontManager.addfont(str(path))
        _title_font = FontProperties(fname=str(path))
    fp = _title_font.copy()
    fp.set_size(size if size is not None else plt.rcParams.get("axes.titlesize", 13))
    return fp


def set_title(ax, text: str, *, size: float | None = None, pad: float = 12) -> None:
    """Left-aligned title in Helvetica Neue Bold."""
    ax.set_title(text, loc="left", pad=pad, fontproperties=title_font(size))


def new_figure():
    """One axes in the standard figure size."""
    return plt.subplots(figsize=(10, 5.5))


def style_axes(ax, *, legend_outside: bool = False) -> None:
    """Horizontal grid, open right side, legend."""
    ax.grid(True, axis="y", alpha=0.35)
    ax.spines["right"].set_visible(False)
    if legend_outside:
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    else:
        ax.legend(loc="upper right")


def apply_style(font_cache: Path | None = None) -> None:
    """Clean Helvetica Neue body text. Titles via set_title()."""
    global _font_cache, _title_font
    _font_cache = font_cache or (ROOT / ".mplconfig" / "fonts")
    _title_font = None
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Helvetica Neue",
                "Helvetica",
                "Arial",
                "DejaVu Sans",
            ],
            "font.size": 11,
            "axes.titlesize": 13,
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
    title_font()
