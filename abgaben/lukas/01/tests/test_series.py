import pandas as pd
import pytest

from hydro.series import regime_mean, select_period, yearly_monthly_means


def test_regime_mean_uses_one_value_per_month():
    df = pd.DataFrame({"year": [1981, 1981], "month": [1, 1], "Q": [2.0, 4.0]})
    mean = regime_mean(yearly_monthly_means(df, 1981, 1981))
    assert mean.loc[1] == 3.0


def test_yearly_monthly_means_drop_years_outside_period():
    df = pd.DataFrame(
        {
            "year": [1980, 1981],
            "month": [1, 1],
            "Q": [10.0, 2.0],
        }
    )
    means = yearly_monthly_means(df, 1981, 1981)
    assert list(means["Q_month"]) == [2.0]


def test_select_period_keeps_inclusive_bounds():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-09-30", "2019-10-01", "2020-09-30", "2020-10-01"]),
            "Q": [1.0, 2.0, 3.0, 4.0],
        }
    )
    period = select_period(df, pd.Timestamp("2019-10-01"), pd.Timestamp("2020-09-30"))
    assert list(period["Q"]) == [2.0, 3.0]


def test_select_period_rejects_empty_window():
    df = pd.DataFrame({"date": pd.to_datetime(["2019-10-01"]), "Q": [1.0]})
    with pytest.raises(ValueError):
        select_period(df, pd.Timestamp("2020-10-01"), pd.Timestamp("2019-09-30"))
