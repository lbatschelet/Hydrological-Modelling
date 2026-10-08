"""DEM helpers: slope raster to two-class polygons."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import mapping, shape

from catchment_map.hru import classify_slope


def merge_dem(paths: list[Path]) -> tuple[np.ndarray, dict]:
    datasets = [rasterio.open(path) for path in paths]
    try:
        data, transform = merge(datasets)
        profile = datasets[0].profile.copy()
        profile.update(
            {
                "height": data.shape[1],
                "width": data.shape[2],
                "transform": transform,
            }
        )
        return data[0], profile
    finally:
        for dataset in datasets:
            dataset.close()


def reproject_array(
    data: np.ndarray,
    src_profile: dict,
    dst_crs: str,
    dst_res: float,
) -> tuple[np.ndarray, dict]:
    transform, width, height = calculate_default_transform(
        src_profile["crs"],
        dst_crs,
        src_profile["width"],
        src_profile["height"],
        *rasterio.transform.array_bounds(
            src_profile["height"], src_profile["width"], src_profile["transform"]
        ),
        resolution=dst_res,
    )
    dst = np.empty((height, width), dtype=np.float32)
    reproject(
        source=data.astype(np.float32),
        destination=dst,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=src_profile.get("nodata"),
        dst_nodata=np.nan,
    )
    profile = src_profile.copy()
    profile.update(
        {
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "dtype": "float32",
            "nodata": np.nan,
            "count": 1,
        }
    )
    return dst, profile


def clip_raster(data: np.ndarray, profile: dict, geom) -> tuple[np.ndarray, dict]:
    with rasterio.MemoryFile() as memfile:
        with memfile.open(**{**profile, "count": 1}) as dataset:
            dataset.write(data, 1)
            clipped, transform = mask(dataset, [mapping(geom)], crop=True, nodata=np.nan)
    out_profile = profile.copy()
    out_profile.update(
        {
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": transform,
        }
    )
    return clipped[0], out_profile


def slope_degrees(elevation: np.ndarray, transform) -> np.ndarray:
    """Horn slope in degrees from a projected DEM (metres)."""
    dx = abs(transform.a)
    dy = abs(transform.e)
    # numpy gradient: axis0 = rows (y), axis1 = cols (x)
    gy, gx = np.gradient(elevation.astype(np.float64), dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    slope[np.isnan(elevation)] = np.nan
    return slope


def slope_class_polygons(
    slope_deg: np.ndarray,
    transform,
    crs,
    threshold_deg: float = 15.0,
) -> gpd.GeoDataFrame:
    """Polygonize the two slope classes. Result is vector, not a pixel map."""
    labels = classify_slope(np.nan_to_num(slope_deg, nan=-1.0), threshold_deg=threshold_deg)
    code = np.where(labels == "steil", 2, np.where(labels == "flach", 1, 0)).astype("int16")
    shapes = (
        (shape(geom), value)
        for geom, value in features.shapes(code, mask=code > 0, transform=transform)
    )
    rows = []
    for geom, value in shapes:
        rows.append(
            {
                "slope_class": "steil" if int(value) == 2 else "flach",
                "geometry": geom,
            }
        )
    return gpd.GeoDataFrame(rows, crs=crs).dissolve(by="slope_class", as_index=False)
