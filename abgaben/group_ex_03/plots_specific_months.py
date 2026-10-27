#Insight into discharge regimes of certain months based on run.py (with CAMELS)

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from load import find_data_root, load_camels
from model import simulate
from run import IMAX, MF, TT, K, SMAX, plot_runoff


#folder for diagrammes
HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


#load the CAMELS data
data_root = find_data_root(HERE)

data = load_camels(
    data_root / "timeseries" / "observation_based" / "CAMELS_CH_obs_based_2303.csv",
    data_root / "timeseries" / "simulation_based" / "CAMELS_CH_sim_based_2303.csv"
)


#From our hydrological year
data = data[
    (data["date"] >= "2019-10-01") &
    (data["date"] <= "2020-09-30")
].copy()


#model for entire year, so that the storages are not reset (later we select individual months)
result = simulate(
    data["P"].tolist(),
    data["T"].tolist(),
    data["PET"].tolist(),
    imax=IMAX,
    mf=MF,
    tt=TT,
    k=K,
    smax=SMAX
)

data["Q_mod"] = result["Q"]


#Chosen months for event diagrams
events = [
    ("December 2019", "2019-12-01", "2019-12-31"),
    ("February 2020", "2020-02-01", "2020-02-29"),  #2020 is a leap year!
    ("May 2020", "2020-05-01", "2020-05-31"),
    ("June 2020", "2020-06-01", "2020-06-30"),
    ("July 2020", "2020-07-01", "2020-07-31"),
    ("September 2020", "2020-08-25", "2020-09-15"),
]


#Diagram for every chosen period (the chosen months for comparison)
for name, start, end in events:

    #pick only our timeframes
    period = data[
        (data["date"] >= start) &
        (data["date"] <= end)
    ].copy()

    #use original plot funciton
    fig = plot_runoff(
        period,
        title="Flowerpot — Thur, Jonschwil-Mühlau",
        subtitle=(
            f"CAMELS catchment mean. {name}. "
            f"mf={MF:g}, TT={TT:g} °C, Smax={SMAX:g} mm, k={K:g}."
        ),
        note="CAMELS-CH 2303. PET from CAMELS pet_sim. Forcing: CAMELS catchment mean."
    )


    ax = fig.axes[0]
    ax.lines[0].set_color("#D95F02")

    #update legend
    ax.legend(
        handles=[ax.lines[0], ax.lines[1], fig.axes[1].patches[0]],
        labels=["Observed Q", "Modelled Q", "P"],
        loc="upper right"
    )

    # set x-axis to certain days within a month (not whole year)
    first_day = pd.Timestamp(start)
    last_day = pd.Timestamp(end)

    days = pd.date_range(first_day, last_day)
    ticks = [days[i] for i in range(0, len(days), 4)]

    if ticks[-1] != last_day:
        if (last_day - ticks[-1]).days < 3:
            ticks.pop()
        ticks.append(last_day)

    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    ax.set_xlim(
        first_day - pd.Timedelta(hours=12),
        last_day + pd.Timedelta(hours=12)
    )

    #set same alignment as other plots
    fig.autofmt_xdate(rotation=30, ha="right")

    #save
    filename = "discharge_regime_" + name.lower().replace(" ", "_") + ".png"
    out = FIGURES / filename

    fig.savefig(out)
    plt.close(fig)

    print("Saved:", out)

print("All event plots created!")