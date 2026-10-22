"""One daily step through interception, snow and soil."""

from __future__ import annotations

from interception import interception_step
from snow import snow_step
from soil import soil_step


def day_step(
    precip: float,
    temperature: float,
    pet: float,
    interception: float,
    swe: float,
    soil: float,
    *,
    imax: float,
    mf: float,
    tt: float,
    k: float,
    smax: float,
) -> tuple[float, float, float, float, float]:
    """Return I, SWE, soil, discharge and total ET after one day."""
    interception, throughfall, et_i = interception_step(interception, precip, pet, imax)
    pet_left = max(pet - et_i, 0.0)
    swe, rain, melt = snow_step(swe, throughfall, temperature, mf, tt)
    soil, discharge, et_s = soil_step(soil, rain + melt, k, smax, pet_left)
    return interception, swe, soil, discharge, et_i + et_s


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
    interception: float = 0.0,
    swe: float = 0.0,
    soil: float = 0.0,
) -> dict[str, list[float]]:
    """Run the flowerpot over the series. All fluxes in mm/d, stores in mm."""
    stores_i: list[float] = []
    stores_swe: list[float] = []
    stores_soil: list[float] = []
    discharges: list[float] = []
    ets: list[float] = []
    for p, t, e in zip(precip, temperature, pet):
        interception, swe, soil, q, et = day_step(
            p, t, e, interception, swe, soil,
            imax=imax, mf=mf, tt=tt, k=k, smax=smax,
        )
        stores_i.append(interception)
        stores_swe.append(swe)
        stores_soil.append(soil)
        discharges.append(q)
        ets.append(et)
    return {
        "interception": stores_i,
        "swe": stores_swe,
        "soil": stores_soil,
        "Q": discharges,
        "ET": ets,
    }
