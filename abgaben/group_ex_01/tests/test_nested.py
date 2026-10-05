import geopandas as gpd
from shapely.geometry import box

from catchment_map.nested import inflowing_catchments


def _frame(rows):
    return gpd.GeoDataFrame(rows, crs="EPSG:2056")


def test_inflowing_catchments_are_fully_inside_and_smaller():
    outlet = box(0, 0, 10, 10)
    nested = box(1, 1, 4, 4)
    outside = box(20, 20, 22, 22)
    larger = box(-5, -5, 15, 15)
    catchments = _frame(
        {
            "gauge_id": [2303, 2374, 9999, 2181],
            "geometry": [outlet, nested, outside, larger],
        }
    )
    inside = inflowing_catchments(catchments, 2303)
    assert list(inside["gauge_id"]) == [2374]


def test_inflowing_catchments_exclude_the_outlet():
    catchments = _frame({"gauge_id": [2303], "geometry": [box(0, 0, 1, 1)]})
    inside = inflowing_catchments(catchments, 2303)
    assert inside.empty
