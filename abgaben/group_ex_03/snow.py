"""Temperature-index snowpack. One threshold for rain/snow and for melt."""

from __future__ import annotations


def snow_step(
    swe: float, precip: float, temperature: float, mf: float, tt: float
) -> tuple[float, float, float]:
    """Return updated SWE, rain, and melt. Rain is precip that never entered the pack."""
    snowfall = precip if temperature <= tt else 0.0
    rain = 0.0 if temperature <= tt else precip
    melt = min(swe + snowfall, mf * max(temperature - tt, 0.0))
    swe = swe + snowfall - melt
    return swe, rain, melt
