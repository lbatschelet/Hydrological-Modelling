from pathlib import Path

from hydro.paths import find_data_root
from hydro.style import apply_style

apply_style(find_data_root(Path(__file__)).parents[1] / ".mplconfig" / "fonts")
