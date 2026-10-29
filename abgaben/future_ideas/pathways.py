"""
Pathways model: interception → snow (+ optional ROS) → soil → fast / GW.

Reuses Ex03 interception; snow via snow_ros (wraps Ex03 snow_step).
"""

from __future__ import annotations

import sys
from pathlib import Path

from routing import linear_route
from snow_ros import DEFAULT_K_ROS, snow_step
from soil_pathways import soil_step

EX03 = Path(__file__).resolve().parent.parent / "group_ex_03"
if str(EX03) not in sys.path:
    sys.path.append(str(EX03))

from interception import interception_step  # noqa: E402


def day_step(
    precip: float,
    temperature: float,
    pet: float,
    interception: float,
    swe: float,
    soil: float,
    fast: float,
    groundwater: float,
    *,
    imax: float,
    mf: float,
    tt: float,
    k: float,
    smax: float,
    k_fast: float,
    k_gw: float,
    f_gw: float,
    direct_overflow: bool = False,
    k_ros: float = DEFAULT_K_ROS,
) -> tuple[float, float, float, float, float, float, float]:
    """Return I, SWE, soil, fast, GW, discharge and total ET."""
    interception, throughfall, et_i = interception_step(interception, precip, pet, imax)
    pet_left = max(pet - et_i, 0.0)
    swe, rain, melt = snow_step(swe, throughfall, temperature, mf, tt, k_ros=k_ros)
    soil, et_s, overflow, drainage = soil_step(soil, rain + melt, k, smax, pet_left)

    f_gw = min(max(f_gw, 0.0), 1.0)
    percolation = f_gw * drainage
    interflow = drainage - percolation

    if direct_overflow:
        q_fast = overflow
        fast = 0.0
    else:
        fast, q_fast = linear_route(fast, overflow, k_fast)
    groundwater, q_gw = linear_route(groundwater, percolation, k_gw)
    discharge = interflow + q_fast + q_gw
    return interception, swe, soil, fast, groundwater, discharge, et_i + et_s


def simulate(
    precip: list[float],
    temperature: list[float],
    pet: list[float],
    *,
    imax: float,
    mf: float,
    tt: float,
    k: float,
    smax: float,
    k_fast: float,
    k_gw: float,
    f_gw: float,
    direct_overflow: bool = False,
    k_ros: float = DEFAULT_K_ROS,
    interception: float = 0.0,
    swe: float = 0.0,
    soil: float = 0.0,
    fast: float = 0.0,
    groundwater: float = 0.0,
) -> dict[str, list[float]]:
    """Run the pathways model. Fluxes in mm/d, stores in mm."""
    stores_i: list[float] = []
    stores_swe: list[float] = []
    stores_soil: list[float] = []
    stores_fast: list[float] = []
    stores_gw: list[float] = []
    discharges: list[float] = []
    ets: list[float] = []
    for p, t, e in zip(precip, temperature, pet):
        interception, swe, soil, fast, groundwater, q, et = day_step(
            p, t, e, interception, swe, soil, fast, groundwater,
            imax=imax, mf=mf, tt=tt, k=k, smax=smax,
            k_fast=k_fast, k_gw=k_gw, f_gw=f_gw,
            direct_overflow=direct_overflow,
            k_ros=k_ros,
        )
        stores_i.append(interception)
        stores_swe.append(swe)
        stores_soil.append(soil)
        stores_fast.append(fast)
        stores_gw.append(groundwater)
        discharges.append(q)
        ets.append(et)
    return {
        "interception": stores_i,
        "swe": stores_swe,
        "soil": stores_soil,
        "fast": stores_fast,
        "groundwater": stores_gw,
        "Q": discharges,
        "ET": ets,
    }
