from pathlib import Path

import pandas as pd
import pytest

from hydro.load import load_discharge, load_fluxes, load_gauge
from hydro.series import with_calendar


def test_load_fluxes_renames_agreed_columns(tmp_path: Path):
    obs = tmp_path / "obs.csv"
    sim = tmp_path / "sim.csv"
    obs.write_text(
        "date,discharge_spec(mm/d),precipitation(mm/d),temperature_mean(degC)\n"
        "2020-01-01,1.5,2.0,-1.0\n"
    )
    sim.write_text("date,pet_sim(mm/d)\n2020-01-01,0.2\n")
    df = load_fluxes(obs, sim)
    assert list(df.columns) == ["date", "Q", "P", "T", "PET"]
    assert df.loc[0, "Q"] == 1.5
    assert df.loc[0, "PET"] == 0.2


def test_load_discharge_uses_volume(tmp_path: Path):
    obs = tmp_path / "obs.csv"
    obs.write_text("date,discharge_vol(m3/s),discharge_spec(mm/d)\n2020-01-01,8.0,1.5\n")
    df = load_discharge(obs)
    assert list(df.columns) == ["date", "Q"]
    assert df.loc[0, "Q"] == 8.0


def test_with_calendar_adds_year_and_month():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-15"]), "Q": [8.0]})
    out = with_calendar(df)
    assert out.loc[0, "year"] == 2020
    assert out.loc[0, "month"] == 1


def test_load_gauge_reads_river_and_name(tmp_path: Path):
    attrs = tmp_path / "attrs.csv"
    attrs.write_text("# comment\ngauge_id,water_body_name,gauge_name\n2303,Thur,Jonschwil\n")
    assert load_gauge(attrs, 2303) == ("Thur", "Jonschwil")


def test_load_gauge_rejects_unknown_id(tmp_path: Path):
    attrs = tmp_path / "attrs.csv"
    attrs.write_text("gauge_id,water_body_name,gauge_name\n2303,Thur,Jonschwil\n")
    with pytest.raises(ValueError):
        load_gauge(attrs, 9999)
