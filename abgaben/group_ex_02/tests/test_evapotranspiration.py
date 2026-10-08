import pytest

from evapotranspiration import et_from_soil_moisture, evapotranspiration
from storage import simulate_limited


def test_et_follows_sqrt_of_relative_storage():
    assert evapotranspiration(25, smax=100, et0=2) == 1.0


def test_et_is_zero_for_empty_storage():
    assert evapotranspiration(0, smax=100, et0=2) == 0.0


def test_soil_moisture_et_is_limited_by_wilting_point_and_field_capacity():
    assert et_from_soil_moisture(0.1, theta_wp=0.2, theta_c=0.4, et0=2) == 0.0
    assert et_from_soil_moisture(0.3, theta_wp=0.2, theta_c=0.4, et0=2) == pytest.approx(1.0)
    assert et_from_soil_moisture(0.5, theta_wp=0.2, theta_c=0.4, et0=2) == 2.0


def test_storage_stays_at_capacity_and_excess_becomes_discharge():
    storage, discharge, et = simulate_limited([100], k=0, smax=40, et0=0)
    assert storage == [40]
    assert discharge == [60]
    assert et == [0]


def test_et_is_taken_out_of_storage():
    storage, discharge, et = simulate_limited([0], k=0, smax=100, et0=2, storage=25)
    assert et == [1.0]
    assert discharge == [0]
    assert storage == [24.0]
