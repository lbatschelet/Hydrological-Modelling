from pathlib import Path

from hydro.paths import find_data_root
# Plotstil aus plot_style.py im Repo-Root, geladen über hydro.style.
from hydro.style import apply_style

apply_style(find_data_root(Path(__file__)).parents[1] / ".mplconfig" / "fonts")
