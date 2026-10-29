"""Parallel HRUs: pathways model weighted by land-cover area."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from pathways import simulate
from snow_ros import DEFAULT_K_ROS

# From optimise_peaks.py (near-best: keep Nash-Log, lift peaks). Grass ≈ lumped pick.
DEFAULT_MF = 1.0
DEFAULT_TT = 0.5
DEFAULT_DIRECT_OVERFLOW = True
DEFAULT_K_ROS_HRU = DEFAULT_K_ROS


@dataclass(frozen=True)
class HruParams:
    """Store / routing parameters for one land-cover class."""

    imax: float
    k: float
    smax: float
    k_fast: float
    k_gw: float
    f_gw: float


# Overflow → Q same day; k_fast unused but kept for the dataclass.
DEFAULT_HRU_PARAMS: dict[str, HruParams] = {
    "forest": HruParams(imax=4.0, k=0.15, smax=120.0, k_fast=1.0, k_gw=0.015, f_gw=0.4),
    "grass": HruParams(imax=1.5, k=0.3, smax=80.0, k_fast=1.0, k_gw=0.02, f_gw=0.25),
    "quick": HruParams(imax=0.5, k=0.5, smax=20.0, k_fast=1.0, k_gw=0.05, f_gw=0.05),
}

# Lumped twin of the grass pick (for compare plots).
LUMPED_PEAK_PARAMS = dict(mf=1.0, tt=0.5, k=0.3, smax=80.0, k_gw=0.02, f_gw=0.25)


def _accumulate(
    precip: list[float],
    temperature: list[float],
    pet: list[float],
    weight: float,
    params: HruParams,
    *,
    mf: float,
    tt: float,
    direct_overflow: bool,
    k_ros: float,
    catchment_q: list[float],
    catchment_et: list[float],
) -> list[float]:
    result = simulate(
        precip,
        temperature,
        pet,
        imax=params.imax,
        mf=mf,
        tt=tt,
        k=params.k,
        smax=params.smax,
        k_fast=params.k_fast,
        k_gw=params.k_gw,
        f_gw=params.f_gw,
        direct_overflow=direct_overflow,
        k_ros=k_ros,
    )
    for i, q in enumerate(result["Q"]):
        catchment_q[i] += weight * q
        catchment_et[i] += weight * result["ET"][i]
    return result["Q"]


def simulate_hrus(
    precip: list[float],
    temperature: list[float],
    pet: list[float],
    weights: dict[str, float],
    params: dict[str, HruParams],
    *,
    mf: float = DEFAULT_MF,
    tt: float = DEFAULT_TT,
    direct_overflow: bool = DEFAULT_DIRECT_OVERFLOW,
    k_ros: float = DEFAULT_K_ROS_HRU,
) -> dict[str, list[float] | dict[str, list[float]]]:
    """
    Run each cover HRU on the same forcing; return catchment Q = Σ w_i Q_i.

    Also returns per-HRU discharge under key "Q_by_hru".
    """
    if set(weights) != set(params):
        raise ValueError(f"Weight keys {set(weights)} must match params {set(params)}")
    total_w = sum(weights.values())
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"Weights must sum to 1, got {total_w}")

    by_hru: dict[str, list[float]] = {}
    n = len(precip)
    catchment_q = [0.0] * n
    catchment_et = [0.0] * n

    for name, weight in weights.items():
        by_hru[name] = _accumulate(
            precip, temperature, pet, weight, params[name],
            mf=mf, tt=tt, direct_overflow=direct_overflow, k_ros=k_ros,
            catchment_q=catchment_q, catchment_et=catchment_et,
        )

    return {"Q": catchment_q, "ET": catchment_et, "Q_by_hru": by_hru}


def simulate_cover_elevation(
    precip: list[float],
    temperature: list[float],
    pet: list[float],
    cover_weights: dict[str, float],
    params: dict[str, HruParams],
    bands: list,
    z_ref: float,
    *,
    lapse: float = -0.0065,
    mf: float = DEFAULT_MF,
    tt: float = DEFAULT_TT,
    direct_overflow: bool = DEFAULT_DIRECT_OVERFLOW,
    k_ros: float = DEFAULT_K_ROS_HRU,
) -> dict[str, list[float] | dict[str, list[float]]]:
    """
    Cover × elevation under independence: w = w_cover · w_band.

    Same P and PET everywhere; T is lapsed to each band. Cover sets the
    store parameters. Returns Q_by_hru keyed as '{cover}|{band}'.
    """
    from elevation import ElevBand, lapse_temperature

    if set(cover_weights) != set(params):
        raise ValueError("Cover weights must match params")
    if abs(sum(cover_weights.values()) - 1.0) > 1e-6:
        raise ValueError("Cover weights must sum to 1")
    if abs(sum(b.weight for b in bands) - 1.0) > 1e-6:
        raise ValueError("Band weights must sum to 1")

    by_hru: dict[str, list[float]] = {}
    n = len(precip)
    catchment_q = [0.0] * n
    catchment_et = [0.0] * n

    for band in bands:
        assert isinstance(band, ElevBand)
        t_band = [
            lapse_temperature(t, band.z_m, z_ref, lapse) for t in temperature
        ]
        for cover, w_c in cover_weights.items():
            weight = w_c * band.weight
            key = f"{cover}|{band.name}"
            by_hru[key] = _accumulate(
                precip, t_band, pet, weight, params[cover],
                mf=mf, tt=tt, direct_overflow=direct_overflow, k_ros=k_ros,
                catchment_q=catchment_q, catchment_et=catchment_et,
            )

    return {"Q": catchment_q, "ET": catchment_et, "Q_by_hru": by_hru}


def param_summary(params: dict[str, HruParams]) -> str:
    """Short subtitle line for plots."""
    parts = []
    for name in ("forest", "grass", "quick"):
        if name not in params:
            continue
        p = params[name]
        parts.append(f"{name}: Smax={p.smax:g}, k={p.k:g}, f_gw={p.f_gw:g}")
    return " | ".join(parts)


def params_as_dicts(params: dict[str, HruParams]) -> dict[str, dict[str, float]]:
    return {name: asdict(p) for name, p in params.items()}
