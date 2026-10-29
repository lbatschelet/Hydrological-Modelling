"""Objective functions (Schaefli Class 4) plus peak-focused scores."""

from __future__ import annotations

import numpy as np
import pandas as pd

_LOG_FLOOR = 0.01


def _arrays(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> tuple[np.ndarray, np.ndarray]:
    obs = np.asarray(observed, dtype=float)
    mod = np.asarray(modelled, dtype=float)
    if obs.shape != mod.shape:
        raise ValueError("observed and modelled must have the same length")
    return obs, mod


def rmse(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> float:
    obs, mod = _arrays(observed, modelled)
    return float(np.sqrt(np.mean((obs - mod) ** 2)))


def bias(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> float:
    """Relative bias: sum(obs − mod) / sum(obs). Positive = model too dry."""
    obs, mod = _arrays(observed, modelled)
    total = float(obs.sum())
    if total == 0:
        return float("nan")
    return float((obs - mod).sum() / total)


def nash_sutcliffe(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> float:
    obs, mod = _arrays(observed, modelled)
    denom = float(np.sum((obs - obs.mean()) ** 2))
    if denom == 0:
        return float("nan")
    return 1.0 - float(np.sum((obs - mod) ** 2) / denom)


def nash_log(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> float:
    obs, mod = _arrays(observed, modelled)
    z_obs = np.log(np.maximum(obs, _LOG_FLOOR))
    z_mod = np.log(np.maximum(mod, _LOG_FLOOR))
    denom = float(np.sum((z_obs - z_obs.mean()) ** 2))
    if denom == 0:
        return float("nan")
    return 1.0 - float(np.sum((z_obs - z_mod) ** 2) / denom)


def nse_high(
    observed: pd.Series | list[float],
    modelled: pd.Series | list[float],
    quantile: float = 0.9,
) -> float:
    obs, mod = _arrays(observed, modelled)
    threshold = float(np.quantile(obs, quantile))
    mask = obs >= threshold
    if mask.sum() < 2:
        return float("nan")
    return nash_sutcliffe(obs[mask], mod[mask])


def peak_ratio(
    observed: pd.Series | list[float],
    modelled: pd.Series | list[float],
    quantile: float = 0.9,
) -> float:
    obs, mod = _arrays(observed, modelled)
    threshold = float(np.quantile(obs, quantile))
    mask = obs >= threshold
    if not mask.any() or float(obs[mask].mean()) == 0:
        return float("nan")
    return float(mod[mask].mean() / obs[mask].mean())


def summarise(observed: pd.Series | list[float], modelled: pd.Series | list[float]) -> dict[str, float]:
    return {
        "nash_log": nash_log(observed, modelled),
        "nse": nash_sutcliffe(observed, modelled),
        "nse_high": nse_high(observed, modelled),
        "peak_ratio": peak_ratio(observed, modelled),
        "rmse": rmse(observed, modelled),
        "bias": bias(observed, modelled),
    }
