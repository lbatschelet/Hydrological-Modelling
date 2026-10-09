# Exercise 2a. One linear store: outflow is a fixed fraction of storage.
# Precipitation is 10 mm on each of the first 10 steps, then zero.

import sys
from pathlib import Path

import matplotlib.pyplot as plt

from storage import simulate, simulate_limited

# Shared figure style. The definitions live in plot_style.py at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plot_style import (  # noqa: E402
    ET_COLOR,
    OUTFLOW_COLOR,
    STORAGE_COLOR,
    apply_style,
    line_style,
    new_figure,
    set_title,
    style_axes,
)

apply_style()

FIGURES = Path(__file__).resolve().parent / "figures"
FIGURES.mkdir(exist_ok=True)

total_time_steps = 70  # long enough for k = 0.1 to drain the store
precipitation_per_time_step = 10
precipitation_duration = 10
k = 0.1

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
set_title(
    ax,
    "Linear storage",
    subtitle=(
        f"Only {k:.0%} of the store leaves each step."
    ),
)
style_axes(ax)
fig.savefig(FIGURES / "linear_storage.png")
print(f"Saved: {FIGURES / 'linear_storage.png'}")
plt.show()


# Exercise 2b. Two stores in series. The first store's outflow is the second store's inflow.
# Peak outflow of the second store, for every pair of k in {0.1, 0.4, 0.7}.

k_values = [0.1, 0.4, 0.7]

fig, ax = new_figure()
color_index = 0
for k1 in k_values:
    for k2 in k_values:
        _, outflow_1 = simulate(inflow, k1)
        _, outflow_2 = simulate(outflow_1, k2)
        print(f"k1={k1}, k2={k2}, max Q2={max(outflow_2):.3f} mm")
        ax.plot(outflow_2, lw=1.8, label=f"k1={k1}, k2={k2}", **line_style(color_index))
        color_index += 1

ax.set_xlabel("Time steps")
ax.set_ylabel("Outflow of second storage [mm]")
set_title(
    ax,
    "Storage cascade",
    subtitle="Swapping the two k values gives the same line. A slow store holds the peak down.",
)
style_axes(ax, legend_outside=True)
fig.savefig(FIGURES / "storage_cascade.png")
print(f"Saved: {FIGURES / 'storage_cascade.png'}")
plt.show()


# Exercise 2c. Same store, plus a capacity and ET = ET0 * sqrt(S / Smax).
# Smax is below the uncapped peak, so the cap is visible.
# The wilting-point form is et_from_soil_moisture; this figure does not use it.

smax = 40
et0 = 2

limited_storage, limited_outflow, et = simulate_limited(inflow, k, smax, et0)

fig, ax = new_figure()
ax.plot(storage, color=STORAGE_COLOR, lw=1.5, ls="--", label="Storage, no cap or ET")
ax.plot(limited_storage, color=STORAGE_COLOR, lw=2.2, label="Storage")
ax.plot(limited_outflow, color=OUTFLOW_COLOR, lw=2.2, label="Outflow")
ax.plot(et, color=ET_COLOR, lw=2.2, label="ET")
ax.set_xlabel("Time steps")
ax.set_ylabel("Storage, outflow and ET [mm]")
set_title(
    ax,
    "Linear storage with capacity and ET",
    subtitle=(
        f"The store stops at {smax:g} mm. Further rain leaves as outflow, "
        f"and ET is {et0:g} mm when the store is full."
    ),
)
style_axes(ax)
fig.savefig(FIGURES / "storage_capacity_et.png")
print(f"Saved: {FIGURES / 'storage_capacity_et.png'}")
plt.show()
