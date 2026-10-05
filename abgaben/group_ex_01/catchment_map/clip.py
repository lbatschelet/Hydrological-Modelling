"""Clip vector layers to one catchment polygon."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def clip_to_polygon(features: gpd.GeoDataFrame, polygon: BaseGeometry) -> gpd.GeoDataFrame:
    """Keep the part of each feature that lies inside the polygon."""
    return gpd.clip(features, polygon).reset_index(drop=True)
