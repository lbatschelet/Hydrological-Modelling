import matplotlib

matplotlib.use("Agg")

import geopandas as gpd
from shapely.geometry import Point, box

from catchment_map.plot import plot_catchment_map


def test_map_uses_a_left_aligned_title():
    landcover = gpd.GeoDataFrame(
        {"OBJVAL": ["Wald"]},
        geometry=[box(0, 0, 2, 2)],
        crs="EPSG:2056",
    )
    outlet = gpd.GeoDataFrame(
        {"gauge_id": [2303], "water_body": ["Thur"], "gauge_name": ["Jonschwil"]},
        geometry=[box(0, 0, 10, 10)],
        crs="EPSG:2056",
    )
    inflowing = outlet.iloc[0:0]
    station = gpd.GeoDataFrame({"gauge_id": [2303]}, geometry=[Point(1, 1)], crs="EPSG:2056")
    fig = plot_catchment_map(
        landcover,
        outlet,
        inflowing,
        title="Thur",
        station=station,
    )
    assert fig.axes[0].get_title(loc="left") == "Thur"
