"""
Rain-on-snow on top of Ex03's temperature-index snow_step.

Open/closed: Ex03 snow stays as-is; we only add an optional melt term when
rain falls on an existing pack (heat from rain ≈ c_w/L_f · P · T).
"""

from __future__ import annotations

import sys
from pathlib import Path

EX03 = Path(__file__).resolve().parent.parent / "group_ex_03"
if str(EX03) not in sys.path:
    sys.path.append(str(EX03))

from snow import snow_step as snow_step_base  # noqa: E402

# mm melt per (mm rain · °C). ≈ c_water / L_fusion when snow is at 0 °C.
DEFAULT_K_ROS = 0.0125


def snow_step(
    swe: float,
    precip: float,
    temperature: float,
    mf: float,
    tt: float,
    k_ros: float = DEFAULT_K_ROS,
) -> tuple[float, float, float]:
    """
    Degree-day melt (Ex03), then extra melt from rain on snow if T > TT.

    Returns SWE, rain, total melt (degree-day + ROS).
    """
    swe, rain, melt = snow_step_base(swe, precip, temperature, mf, tt)
    if k_ros > 0.0 and rain > 0.0 and swe > 0.0 and temperature > tt:
        ros = min(swe, k_ros * rain * (temperature - tt))
        swe -= ros
        melt += ros
    return swe, rain, melt
