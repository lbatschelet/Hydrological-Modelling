import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from hydro.plot_hydro_year import plot_hydro_year
from hydro.plot_regime import plot_regime


def test_plot_hydro_year_returns_temperature_and_flux_axes():
    period = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-10-01", "2019-10-02"]),
            "Q": [1.0, 2.0],
            "P": [0.0, 5.0],
            "T": [-1.0, 3.0],
            "PET": [0.2, 0.3],
        }
    )
    fig = plot_hydro_year(period, title="Hydro year")
    titled = [ax.get_title(loc="left") for ax in fig.axes]
    assert "Hydro year" in titled
    assert len(fig.axes) >= 2
    plt.close(fig)


def test_plot_regime_labels_both_periods():
    early = pd.Series(range(1, 13), index=range(1, 13), dtype=float)
    late = early + 1
    fig = plot_regime(
        early,
        late,
        title="Regime",
        early_label="1981–2000",
        late_label="2001–2020",
        note="monthly means",
    )
    ax = fig.axes[0]
    assert ax.get_title(loc="left") == "Regime"
    assert [line.get_label() for line in ax.get_lines()] == ["1981–2000", "2001–2020"]
    plt.close(fig)
