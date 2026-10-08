import geopandas as gpd
import numpy as np
from shapely.geometry import box

from catchment_map.hru import (
    aggregate_landcover,
    classify_slope,
    hru_polygons,
)


def test_classify_slope_uses_two_named_classes():
    classes = classify_slope(np.array([[5.0, 20.0], [15.0, 14.9]]), threshold_deg=15.0)
    assert classes.tolist() == [["flach", "steil"], ["steil", "flach"]]


def test_aggregate_landcover_merges_settlement_and_fills_gaps():
    landcover = gpd.GeoDataFrame(
        {"OBJVAL": ["Wald", "Siedl", "Stadtzentr"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        crs="EPSG:2056",
    )
    catchment = box(0, 0, 4, 1)
    agg = aggregate_landcover(landcover, catchment)
    assert set(agg["landuse"]) == {"Wald", "Siedlung", "Offenland"}
    assert abs(agg.geometry.union_all().area - 4.0) < 1e-6


def test_hru_polygons_intersect_landuse_and_slope():
    landuse = gpd.GeoDataFrame(
        {"landuse": ["Wald", "Offenland"]},
        geometry=[box(0, 0, 2, 2), box(2, 0, 4, 2)],
        crs="EPSG:2056",
    )
    slope = gpd.GeoDataFrame(
        {"slope_class": ["flach", "steil"]},
        geometry=[box(0, 0, 4, 1), box(0, 1, 4, 2)],
        crs="EPSG:2056",
    )
    hrus = hru_polygons(landuse, slope)
    assert set(zip(hrus["landuse"], hrus["slope_class"])) == {
        ("Wald", "flach"),
        ("Wald", "steil"),
        ("Offenland", "flach"),
        ("Offenland", "steil"),
    }
    assert abs(hrus.geometry.area.sum() - 8.0) < 1e-6
