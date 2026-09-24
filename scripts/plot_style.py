"""Shared matplotlib styling for CAMELS-CH exercise plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties

_ROOT = Path(__file__).resolve().parents[1]
_FONT_CACHE = _ROOT / ".mplconfig" / "fonts"
_HN_TTC = Path("/System/Library/Fonts/HelveticaNeue.ttc")
# Face index 1 = Helvetica Neue Bold (see TTCollection listing)
_HN_BOLD_INDEX = 1

_title_font: FontProperties | None = None


def _ensure_helvetica_neue_bold() -> Path:
    """Extract Bold from the system TTC into a local cache file."""
    out = _FONT_CACHE / "HelveticaNeue-Bold.ttf"
    if out.exists():
        return out

    from fontTools.ttLib import TTCollection

    _FONT_CACHE.mkdir(parents=True, exist_ok=True)
    ttc = TTCollection(str(_HN_TTC))
    font = ttc.fonts[_HN_BOLD_INDEX]
    font.save(str(out))
    return out


def title_font(size: float | None = None) -> FontProperties:
    """Helvetica Neue Bold for plot titles."""
    global _title_font
    if _title_font is None:
        path = _ensure_helvetica_neue_bold()
        font_manager.fontManager.addfont(str(path))
        _title_font = FontProperties(fname=str(path))
    fp = _title_font.copy()
    if size is not None:
        fp.set_size(size)
    else:
        fp.set_size(plt.rcParams.get("axes.titlesize", 13))
    return fp


def set_title(ax, text: str, *, size: float | None = None, pad: float = 12) -> None:
    """Left-aligned title in Helvetica Neue Bold."""
    ax.set_title(text, loc="left", pad=pad, fontproperties=title_font(size))


def apply_style() -> None:
    """Clean Helvetica Neue body text; titles via set_title()."""
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
    # Warm up title font registration
    title_font()
