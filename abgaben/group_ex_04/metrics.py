"""NSE, Nash-Log, Bias (Exercise 4)."""

from __future__ import annotations

import numpy as np

_LOG_FLOOR = 0.01


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    return 1.0 - float(np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))


def nash_log(obs: np.ndarray, sim: np.ndarray) -> float:
    zo = np.log(np.maximum(obs, _LOG_FLOOR))
    zs = np.log(np.maximum(sim, _LOG_FLOOR))
    return 1.0 - float(np.sum((zo - zs) ** 2) / np.sum((zo - zo.mean()) ** 2))


def bias(obs: np.ndarray, sim: np.ndarray) -> float:
    """(Σobs − Σsim) / Σobs. >0 = model too dry."""
    return float((obs - sim).sum() / obs.sum())


def score(obs, sim) -> dict[str, float]:
    o = np.asarray(obs, dtype=float)
    s = np.asarray(sim, dtype=float)
    return {"nse": nse(o, s), "nash_log": nash_log(o, s), "bias": bias(o, s)}
