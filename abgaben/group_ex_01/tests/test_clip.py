import geopandas as gpd
from shapely.geometry import box

from catchment_map.clip import clip_to_polygon


def test_clip_keeps_only_the_part_inside_the_catchment():
    features = gpd.GeoDataFrame(
        {"OBJVAL": ["Wald", "See"]},
        geometry=[box(0, 0, 4, 2), box(10, 10, 12, 12)],
        crs="EPSG:2056",
    )
    clipped = clip_to_polygon(features, box(0, 0, 2, 2))
    assert list(clipped["OBJVAL"]) == ["Wald"]
    assert clipped.geometry.iloc[0].area == 4
