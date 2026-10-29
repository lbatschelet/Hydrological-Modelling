"""One continuous simulate() over the record, then cut out the plot/metric window."""

from __future__ import annotations

import pandas as pd


def running_slice(
    frame: pd.DataFrame,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    *,
    from_record_start: bool = True,
    spin_years: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return (full, window).

    Default (running series): `full` is everything from the first available day
    up to `end`. Stores are never reset at `start` — the plot window is only a
    cut of that continuous run.

    If `from_record_start` is False, use `spin_years` before `start` instead
    (faster smoke tests).
    """
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    if from_record_start:
        run_from = frame["date"].min()
    else:
        years = 1 if spin_years is None else spin_years
        run_from = start_ts - pd.DateOffset(years=years)

    full = frame.loc[(frame["date"] >= run_from) & (frame["date"] <= end_ts)].copy()
    window = full.loc[(full["date"] >= start_ts) & (full["date"] <= end_ts)].copy()
    if window.empty:
        raise ValueError(f"No data between {start_ts.date()} and {end_ts.date()}")
    if full.empty:
        raise ValueError(f"No data to simulate up to {end_ts.date()}")
    return full, window
