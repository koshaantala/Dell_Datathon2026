"""Build data/hill_country_sites.csv from the hackathon image_metadata.csv.

Keeps only Hill Country (July 2025) locations that have a precise footprint, and only
the columns the website uses. Re-run whenever the source dataset changes:

    python scripts/extract_sites.py --source path/to/image_metadata.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

KEEP_COLUMNS = [
    "image_id",
    "image_path",
    "locality",
    "county_name",
    "acquisition_date",
    "latitude",
    "longitude",
    "west",
    "south",
    "east",
    "north",
    "fema_flood_zones",
    "fema_zone_subtypes",
    "fema_sfha_tf",
    "elevation_m",
    "elevation_vertical_datum",
    "terrain_elevation_min_m",
    "terrain_elevation_max_m",
    "terrain_slope_mean_degrees",
    "nearest_high_water_mark_key",
    "nearest_high_water_mark_distance_km",
    "usgs_gage_height_station_id",
    "usgs_gage_height_station_name",
    "usgs_gage_height_station_distance_km",
    "watershed_names",
    "screening_notes",
    "source_url",
    "attribution",
    "reuse",
    "license_url",
]


def is_hill_country_site(row: dict[str, str]) -> bool:
    """Hill Country NOAA frames have ids starting HC and a precise footprint."""
    return (
        row.get("state") == "Texas"
        and row.get("image_id", "").startswith("HC")
        and row.get("location_precision") == "georeferenced_footprint_center"
        and bool(row.get("latitude"))
        and bool(row.get("longitude"))
    )


def extract(source: Path, out: Path) -> int:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in KEEP_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"Source CSV is missing columns: {missing}")
        rows = [{c: row[c] for c in KEEP_COLUMNS} for row in reader if is_hill_country_site(row)]

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=KEEP_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, required=True, help="image_metadata.csv")
    parser.add_argument("--out", type=Path, default=Path("data/hill_country_sites.csv"))
    args = parser.parse_args(argv)
    count = extract(args.source, args.out)
    print(f"Wrote {count} sites to {args.out}")
    return 0 if count else 1


if __name__ == "__main__":
    sys.exit(main())
