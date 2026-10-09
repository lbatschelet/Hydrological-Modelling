"""Build HRU polygons from land use and two slope classes."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

LANDUSE_MAP = {
    "Wald": "Wald",
    "Siedl": "Siedlung",
    "Stadtzentr": "Siedlung",
    "Obstanlage": "Obstanlage",
    "Reben": "Reben",
    "Sumpf": "Sumpf",
    "Fels": "Fels",
    "Geroell": "Geröll",
    "Gletscher": "Gletscher",
    "See": "See",
    "Stausee": "See",
}


def classify_slope(slope_deg: np.ndarray, threshold_deg: float = 15.0) -> np.ndarray:
    """Two slope classes, stored as flach and steil."""
    return np.where(slope_deg >= threshold_deg, "steil", "flach")


def aggregate_landcover(
    landcover: gpd.GeoDataFrame,
    catchment: BaseGeometry,
) -> gpd.GeoDataFrame:
    """Clip land cover to the catchment. Gaps, mostly open land, are stored as Offenland."""
    clipped = gpd.clip(landcover, catchment)
    if clipped.empty:
        covered = Polygon()
    else:
        clipped = clipped.copy()
        clipped["landuse"] = clipped["OBJVAL"].map(LANDUSE_MAP).fillna(clipped["OBJVAL"])
        covered = unary_union(clipped.geometry)

    gap = catchment.difference(covered)
    parts = []
    if not clipped.empty:
        parts.append(clipped[["landuse", "geometry"]])
    if not gap.is_empty:
        gaps = gpd.GeoDataFrame({"landuse": ["Offenland"]}, geometry=[gap], crs=landcover.crs)
        parts.append(gaps.explode(index_parts=False))
    out = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=landcover.crs)
    return out.dissolve(by="landuse", as_index=False).explode(index_parts=False).reset_index(drop=True)


def hru_polygons(landuse: gpd.GeoDataFrame, slope: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Intersect land-use and slope polygons, dissolve by both attributes."""
    crossed = gpd.overlay(landuse, slope, how="intersection")
    if crossed.empty:
        return crossed
    dissolved = crossed.dissolve(by=["landuse", "slope_class"], as_index=False)
    dissolved["area_km2"] = dissolved.geometry.area / 1e6
    return dissolved.sort_values(["landuse", "slope_class"]).reset_index(drop=True)
