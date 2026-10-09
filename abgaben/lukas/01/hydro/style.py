"""Load the shared figure style. The definitions live in plot_style.py at the repo root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from plot_style import apply_style, set_title

__all__ = ["apply_style", "set_title"]
