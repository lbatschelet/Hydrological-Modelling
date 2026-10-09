"""Exercise 1a — HRU map: land use × two slope classes as polygons."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

from catchment_map.clip import clip_to_polygon
from catchment_map.dem import (
    clip_raster,
    merge_dem,
    reproject_array,
    slope_class_polygons,
    slope_degrees,
)
from catchment_map.hru import aggregate_landcover, hru_polygons
from catchment_map.plot_hru import hru_subtitle, plot_hru_combined, plot_hru_map
from plot_style import apply_style


def find_repo(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "data" / "camels_ch").is_dir():
            return candidate
    raise FileNotFoundError(f"No CAMELS-CH data above {start}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    parser.add_argument("--threshold", type=float, default=15.0, help="Slope threshold in degrees")
    parser.add_argument("--res", type=float, default=30.0, help="DEM resolution in metres")
    args = parser.parse_args()
    apply_style()

    repo = find_repo(Path(__file__).resolve().parent)
    data = repo / "data"
    dem_paths = sorted((data / "dem").glob("Copernicus_DSM_COG_10_*.tif"))
    if not dem_paths:
        raise FileNotFoundError("No Copernicus DEM tiles in data/dem/")

    catchments = gpd.read_file(
        data / "camels_ch" / "catchment_delineations" / "CAMELS_CH_catchments.shp"
    )
    outlet = catchments.loc[catchments["gauge_id"] == args.gauge]
    if outlet.empty:
        raise ValueError(f"Unknown gauge_id {args.gauge}")
    polygon = outlet.geometry.iloc[0]
    bounds = tuple(polygon.bounds)

    dem, dem_profile = merge_dem(dem_paths)
    dem_lv95, profile_lv95 = reproject_array(dem, dem_profile, "EPSG:2056", args.res)
    dem_clip, profile_clip = clip_raster(dem_lv95, profile_lv95, polygon)
    slope = slope_degrees(dem_clip, profile_clip["transform"])
    slope_polys = slope_class_polygons(
        slope,
        profile_clip["transform"],
        profile_clip["crs"],
        threshold_deg=args.threshold,
    )
    slope_polys = clip_to_polygon(slope_polys, polygon)

    landcover = gpd.read_file(data / "Landcover" / "swissTLMRegio_LandCover.shp", bbox=bounds)
    landuse = aggregate_landcover(landcover, polygon)
    hrus = hru_polygons(landuse, slope_polys)

    out_dir = Path(__file__).resolve().parent / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    hrus.to_file(out_dir / f"hru_{args.gauge}.gpkg", layer="hru", driver="GPKG")

    row = outlet.iloc[0]
    title = f"{row.water_body}, {row.gauge_name} — HRUs (land cover × slope)"
    subtitle = hru_subtitle(hrus)
    fig = plot_hru_combined(
        hrus, outlet, title=title, threshold_deg=args.threshold, subtitle=subtitle
    )
    out = out_dir / f"hru_{args.gauge}_landuse_slope.png"
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig2 = plot_hru_map(
        hrus, outlet, title=title, threshold_deg=args.threshold, subtitle=subtitle
    )
    out2 = out_dir / f"hru_{args.gauge}_panels.png"
    fig2.savefig(out2, dpi=160, bbox_inches="tight")
    plt.close(fig2)

    summary = (
        hrus.groupby(["landuse", "slope_class"], as_index=False)["area_km2"]
        .sum()
        .sort_values("area_km2", ascending=False)
    )
    print(summary.to_string(index=False))
    print(f"Saved: {out}")
    print(f"Saved: {out2}")
    print(f"Saved: {out_dir / f'hru_{args.gauge}.gpkg'}")


if __name__ == "__main__":
    main()
