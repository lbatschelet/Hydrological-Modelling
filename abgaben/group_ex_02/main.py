# Exercise 2a – Single linear storage
# Linear storage: the discharge is proportional to the storage content.
# Flowerpot: constant precipitation of 10 mm per time step for the first 10 steps.

import sys
from pathlib import Path

import matplotlib.pyplot as plt

from storage import simulate

# Gemeinsamer Plotstil. Definitionen stehen in plot_style.py im Repo-Root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plot_style import (  # noqa: E402
    LINE_COLORS,
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    new_figure,
    set_title,
    style_axes,
)

apply_style()

FIGURES = Path(__file__).resolve().parent / "figures"
FIGURES.mkdir(exist_ok=True)

total_time_steps = 70  # storage is near 0 after 70 steps with k = 0.1
precipitation_per_time_step = 10
precipitation_duration = 10
k = 0.1  # fraction of storage released per step, between 0 and 1

inflow = [
    precipitation_per_time_step if step < precipitation_duration else 0
    for step in range(total_time_steps)
]

storage, outflow = simulate(inflow, k)

fig, ax = new_figure()
ax.plot(storage, color=STORAGE_COLOR, lw=2.2, label="Storage")
ax.plot(outflow, color=OUTFLOW_COLOR, lw=2.2, label="Outflow")
ax.set_xlabel("Time steps")
ax.set_ylabel("Storage and outflow [mm]")
set_title(ax, "Linear storage")
style_axes(ax)
fig.savefig(FIGURES / "linear_storage.png")
print(f"Saved: {FIGURES / 'linear_storage.png'}")
plt.show()


# Exercise 2b – Storage cascade
# Two linear storages in series. Outflow of the first is inflow of the second.
# Maximum discharge for all 9 combinations of k1 and k2 in {0.1, 0.4, 0.7}.

k_values = [0.1, 0.4, 0.7]

fig, ax = new_figure()
color_index = 0
for k1 in k_values:
    for k2 in k_values:
        _, outflow_1 = simulate(inflow, k1)
        _, outflow_2 = simulate(outflow_1, k2)
        print(f"k1={k1}, k2={k2}, max Q2={max(outflow_2):.3f} mm")
        ax.plot(outflow_2, color=LINE_COLORS[color_index], lw=1.8, label=f"k1={k1}, k2={k2}")
        color_index += 1

ax.set_xlabel("Time steps")
ax.set_ylabel("Outflow of second storage [mm]")
set_title(ax, "Storage cascade")
style_axes(ax, legend_outside=True)
fig.savefig(FIGURES / "storage_cascade.png")
print(f"Saved: {FIGURES / 'storage_cascade.png'}")
plt.show()


# Exercise 2c – Storage max capacity & ET
# ET as a function of soil moisture θ and two parameters:
#   θwp: (permanent) wilting point
#   θc: retention capacity, often called field capacity
#
# For a single linear reservoir, add a maximum storage capacity.
# Then add ET = ET0 * (S(t) / Smax) ** 0.5 with ET0 = 2 mm/d
