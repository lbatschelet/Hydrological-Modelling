"""Map for group exercise 1: land cover of catchment 2303 and its inflowing basins."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

from catchment_map.clip import clip_to_polygon
from catchment_map.nested import inflowing_catchments
from catchment_map.plot import plot_catchment_map


def find_repo(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "data" / "camels_ch").is_dir():
            return candidate
    raise FileNotFoundError(f"No CAMELS-CH data above {start}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gauge", type=int, default=2303)
    args = parser.parse_args()

    repo = find_repo(Path(__file__).resolve().parent)
    data = repo / "data"
    catchments = gpd.read_file(
        data / "camels_ch" / "catchment_delineations" / "CAMELS_CH_catchments.shp"
    )
    gauges = gpd.read_file(
        data / "camels_ch" / "catchment_delineations" / "CAMELS_CH_gauging_stations.shp"
    )
    outlet = catchments.loc[catchments["gauge_id"] == args.gauge]
    if outlet.empty:
        raise ValueError(f"Unknown gauge_id {args.gauge}")
    polygon = outlet.geometry.iloc[0]
    bounds = tuple(polygon.bounds)

    landcover = clip_to_polygon(
        gpd.read_file(data / "Landcover" / "swissTLMRegio_LandCover.shp", bbox=bounds),
        polygon,
    )
    rivers = clip_to_polygon(
        gpd.read_file(data / "Hydrography" / "swissTLMRegio_FlowingWater.shp", bbox=bounds),
        polygon,
    )
    inflowing = inflowing_catchments(catchments, args.gauge)
    station = gauges.loc[gauges["gauge_id"] == args.gauge]
    row = outlet.iloc[0]
    fig = plot_catchment_map(
        landcover,
        outlet,
        inflowing,
        title=f"{row.water_body}, {row.gauge_name} — Landbedeckung und Teileinzugsgebiete",
        station=station,
        rivers=rivers,
    )
    out_dir = Path(__file__).resolve().parent / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"catchment_{args.gauge}_landcover.png"
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
