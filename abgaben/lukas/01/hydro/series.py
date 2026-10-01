"""Period filters and monthly regime statistics."""

from __future__ import annotations

import pandas as pd

MONTHS = list(range(1, 13))


def with_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add year and month from a date column."""
    out = df.copy()
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month
    return out


def select_period(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Inclusive date window. Raises if the window contains no rows."""
    period = df.loc[(df["date"] >= start) & (df["date"] <= end)].copy()
    if period.empty:
        raise ValueError(f"No data between {start.date()} and {end.date()}")
    return period


def yearly_monthly_means(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """One value per year and month: the mean of daily Q."""
    window = df.loc[(df["year"] >= y0) & (df["year"] <= y1)]
    return (
        window.groupby(["year", "month"], as_index=False)["Q"]
        .mean()
        .rename(columns={"Q": "Q_month"})
    )


def regime_mean(ym: pd.DataFrame) -> pd.Series:
    """Mean monthly regime across years. Index is calendar month 1–12."""
    return ym.groupby("month")["Q_month"].mean().reindex(MONTHS)
