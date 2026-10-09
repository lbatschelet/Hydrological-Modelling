"""Evapotranspiration from storage, and from soil moisture between wilting point and field capacity."""

from __future__ import annotations


def evapotranspiration(storage: float, smax: float, et0: float) -> float:
    """ET0 times the square root of relative storage. Empty storage evaporates nothing."""
    if storage <= 0 or smax <= 0:
        return 0.0
    return et0 * (storage / smax) ** 0.5


def et_from_soil_moisture(theta: float, theta_wp: float, theta_c: float, et0: float) -> float:
    """ET rises from 0 at wilting point to ET0 at field capacity."""
    if theta <= theta_wp:
        return 0.0
    if theta >= theta_c:
        return et0
    return et0 * (theta - theta_wp) / (theta_c - theta_wp)
