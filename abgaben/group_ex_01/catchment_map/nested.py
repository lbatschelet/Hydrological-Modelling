"""Which gauged catchments lie inside an outlet catchment."""

from __future__ import annotations

import geopandas as gpd


def inflowing_catchments(catchments: gpd.GeoDataFrame, outlet_id: int) -> gpd.GeoDataFrame:
    """Catchments fully inside the outlet and smaller than it."""
    outlet = catchments.loc[catchments["gauge_id"] == outlet_id]
    if outlet.empty:
        raise ValueError(f"Unknown gauge_id {outlet_id}")
    polygon = outlet.geometry.iloc[0]
    others = catchments.loc[catchments["gauge_id"] != outlet_id]
    inside = others.geometry.within(polygon) & (others.geometry.area < polygon.area)
    return others.loc[inside].reset_index(drop=True)
